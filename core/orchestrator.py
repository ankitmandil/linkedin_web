from typing import List, Dict, Any, Optional
from core.resume_parser import ResumeParser, CandidateProfile
from core.linkedin_client import LinkedInClient, LinkedInJob
from core.hiring_manager_finder import HiringManagerFinder
from core.matcher import OpportunityMatcher
from core.outreach_generator import OutreachGenerator
import time

class ProductHiringManagerSystem:
    """End-to-End AI System for Finding Similar & Higher Roles and Executive Hiring Managers."""

    def __init__(self):
        self.parser = ResumeParser()
        self.linkedin_client = LinkedInClient()
        self.hm_finder = HiringManagerFinder()
        self.matcher = OpportunityMatcher()
        self.outreach_gen = OutreachGenerator()

    def run(
        self,
        resume_text: str,
        level_filter: str = "all", # 'all', 'higher', 'similar'
        location: str = "Bengaluru, Karnataka, India",
        page: int = 1,
        page_size: int = 6,
        sort_by: str = "date", # 'date' (latest first, default) or 'match'
        progress_callback = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end analysis:
        1. Analyzes resume, dynamically detects domain track (Data Science vs Product vs Engineering),
           calculates YoE, extracts skills and target titles.
        2. Queries live LinkedIn jobs with pagination support.
        3. Identifies and verifies the Hiring Manager's LinkedIn profile for each company.
        4. Calculates deep TF-IDF semantic match, YoE delta, and skills coverage between Resume and JD.
        """
        def log(msg: str):
            if progress_callback:
                progress_callback(msg)
            else:
                print(f"[*] {msg}", flush=True)

        log("Analyzing resume, calculating years of experience, and detecting career track...")
        candidate = self.parser.parse(resume_text)
        log(f"Candidate Identified: {candidate.name} ({candidate.years_of_experience:.0f}+ YoE, Track: {candidate.track})")
        log(f"Target Higher Roles: {', '.join(candidate.target_higher_roles[:3])}")
        log(f"Target Similar Roles: {', '.join(candidate.target_similar_roles[:2])}")

        # Formulate search queries based on track and level filter
        search_queries = []
        if candidate.track == "DATA_SCIENCE":
            if level_filter == "higher":
                search_queries = ["Director of Data Science", "Head of Data Science", "Head of AI", "VP Data Science"]
            elif level_filter == "similar":
                search_queries = ["Lead Data Scientist", "Principal Data Scientist", "Staff Data Scientist"]
            else:
                search_queries = ["Director of Data Science", "Lead Data Scientist", "Head of AI", "Principal Data Scientist"]
        elif candidate.track == "PRODUCT":
            if level_filter == "higher":
                search_queries = ["Director of Product", "Head of Product", "VP of Product"]
            elif level_filter == "similar":
                search_queries = ["Group Product Manager", "Principal Product Manager", "Lead Product Manager"]
            else:
                search_queries = ["Director of Product", "Group Product Manager", "Head of Product", "Director Product Management"]
        else: # ENGINEERING
            if level_filter == "higher":
                search_queries = ["Director of Engineering", "VP of Engineering", "Head of Engineering"]
            elif level_filter == "similar":
                search_queries = ["Engineering Manager", "Staff Software Engineer", "Principal Engineer"]
            else:
                search_queries = ["Director of Engineering", "Engineering Manager", "Principal Engineer"]

        log(f"Searching LinkedIn jobs (Page {page}, {page_size} results/page) across queries in {location}...")
        
        # Calculate pagination offset for LinkedIn guest API
        start_offset = (page - 1) * page_size
        raw_jobs: List[LinkedInJob] = []
        seen_job_urls = set()

        for q in search_queries:
            if len(raw_jobs) >= page_size * 2:
                break
            log(f"Querying LinkedIn for '{q}' in {location}...")
            # Query with pagination offset
            found = self.linkedin_client.search_jobs(
                keywords=q,
                location=location,
                limit=(page_size // len(search_queries)) + 2,
                start_offset=start_offset,
                fetch_full_jd=True
            )
            for j in found:
                if j.url not in seen_job_urls:
                    seen_job_urls.add(j.url)
                    raw_jobs.append(j)
            time.sleep(0.3)

        # Sort raw jobs by date posted descending (latest first)
        raw_jobs.sort(key=lambda x: x.posted_timestamp, reverse=True)

        log(f"Found {len(raw_jobs)} unique live LinkedIn postings. Evaluating JD vs Resume and finding leaders...")

        results = []
        for i, job in enumerate(raw_jobs, 1):
            if len(results) >= page_size:
                break

            # Deep JD vs Resume evaluation
            match_data = self.matcher.evaluate_match(candidate, job)
            level_cat = match_data["role_level_category"]
            job.role_level_category = level_cat

            # Level filter
            if level_filter == "higher" and level_cat != "Higher Role":
                continue
            if level_filter == "similar" and level_cat != "Similar Role":
                continue

            log(f"[{i}/{len(raw_jobs)}] Finding Hiring Manager for {job.company} ({job.title} - {level_cat})...")
            hm_info = self.hm_finder.find_hiring_manager(
                company=job.company,
                job_title=job.title,
                candidate_track=candidate.track,
                on_page_poster=job.hiring_manager,
                jd_text=job.full_description
            )
            job.hiring_manager = hm_info

            # Generate outreach pitches
            connection_note = self.outreach_gen.generate_connection_note(candidate, job, hm_info)
            inmail_pitch = self.outreach_gen.generate_inmail_pitch(candidate, job, hm_info)

            results.append({
                "job_title": job.title,
                "company": job.company,
                "location": job.location,
                "job_url": job.url,
                "posted_time": job.posted_time,
                "posted_date_iso": job.posted_date_iso,
                "posted_timestamp": job.posted_timestamp,
                "role_level_category": level_cat,
                "match_score": match_data["match_score"],
                "cosine_similarity_pct": match_data["cosine_similarity_pct"],
                "matched_skills": match_data["matched_skills"],
                "missing_skills": match_data["missing_skills"],
                "jd_yoe_requirement": match_data["jd_yoe_requirement"],
                "candidate_yoe": match_data["candidate_yoe"],
                "match_rationale": match_data["rationale"],
                "job_description_snippet": job.description_snippet or "Detailed requirements available on LinkedIn.",
                "hiring_manager": {
                    "name": hm_info.get("name", "Leadership"),
                    "title": hm_info.get("title", "Executive"),
                    "headline": hm_info.get("headline", ""),
                    "linkedin_url": hm_info.get("linkedin_url", ""),
                    "confidence": hm_info.get("confidence", "Verified")
                },
                "outreach": {
                    "connection_note": connection_note,
                    "inmail_pitch": inmail_pitch
                }
            })

        # Sort results: Default is date descending (latest first)
        if sort_by == "date":
            results.sort(key=lambda x: (x.get("posted_timestamp", 0), x.get("match_score", 0)), reverse=True)
        else:
            results.sort(key=lambda x: (x.get("match_score", 0), x.get("posted_timestamp", 0)), reverse=True)

        log(f"Discovery complete! Found {len(results)} matching opportunities on page {page} (Sorted by: {sort_by}).")

        return {
            "candidate": candidate.to_dict(),
            "search_metadata": {
                "level_filter": level_filter,
                "location": location,
                "page": page,
                "page_size": page_size,
                "sort_by": sort_by,
                "has_more": len(results) >= page_size,
                "total_opportunities_found": len(results)
            },
            "opportunities": results
        }
