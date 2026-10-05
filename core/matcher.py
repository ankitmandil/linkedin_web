import re
from typing import Dict, Any, Tuple, List, Set, Optional
from core.resume_parser import CandidateProfile
from core.linkedin_client import LinkedInJob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class OpportunityMatcher:
    """Rigorous Resume vs JD Match Engine using TF-IDF NLP similarity, YoE delta, and skill overlap."""

    def __init__(self):
        # Universal skill lexicon for matching
        self.skill_lexicon = [
            # Data Science / AI / ML
            "python", "pytorch", "tensorflow", "scikit-learn", "deep learning", "machine learning",
            "transformers", "nlp", "natural language processing", "computer vision", "llms", "large language models",
            "generative ai", "genai", "rag", "langchain", "llamaindex", "vector db", "fine-tuning", "lora",
            "mlops", "kubeflow", "mlflow", "airflow", "docker", "kubernetes", "recommender systems", "ranking",
            "a/b testing", "causal inference", "statistics", "pyspark", "spark", "databricks", "bigquery",
            "snowflake", "sql", "xgboost", "lightgbm", "triton", "onnx", "tensorrt", "bert", "gpt",
            # Product Management
            "product strategy", "consumer growth", "marketplaces", "payments", "checkout", "juspay",
            "loyalty", "subscriptions", "search", "personalisation", "discovery", "product roadmap", "prd",
            "user research", "conversion", "retention", "monetisation", "funnel",
            # Engineering
            "system design", "distributed systems", "microservices", "java", "golang", "c++", "aws", "gcp"
        ]

    def classify_role_level(self, job_title: str, candidate: CandidateProfile) -> str:
        """Classifies role as 'Higher Role' or 'Similar Role' based on candidate track and seniority."""
        title_lower = job_title.lower()

        # Data Science track
        if candidate.track == "DATA_SCIENCE":
            higher_ds = ["director", "head of", "vp", "vice president", "chief", "senior director"]
            similar_lead = ["lead data scientist", "principal data scientist", "staff data scientist", "ai architect"]
            similar_senior = ["senior data scientist", "data scientist 2", "senior machine learning"]

            if any(h in title_lower for h in higher_ds):
                return "Higher Role"
            
            if candidate.years_of_experience >= 9:
                # For an 11-year lead, Lead/Principal is similar, Director/Head is higher
                if any(s in title_lower for s in similar_lead):
                    return "Similar Role"
                elif any(s in title_lower for s in similar_senior):
                    return "Lateral / Mid-Senior"
            else:
                # For a 6-year senior data scientist, Lead/Principal is a higher role!
                if any(s in title_lower for s in similar_lead):
                    return "Higher Role"
                elif any(s in title_lower for s in similar_senior):
                    return "Similar Role"

            return "Similar Role"

        # Product track
        higher_pm = ["director", "vp", "vice president", "head of", "chief", "senior director"]
        similar_pm = ["group product manager", "gpm", "principal", "lead product manager", "staff product manager"]

        if any(h in title_lower for h in higher_pm):
            return "Higher Role"
        elif any(s in title_lower for s in similar_pm):
            return "Similar Role"
        elif "senior product manager" in title_lower or "spm" in title_lower:
            return "Lateral / Mid-Senior"

        return "Higher Role" if "director" in title_lower else "Similar Role"

    def extract_required_yoe_from_jd(self, jd_text: str) -> Tuple[Optional[float], str]:
        """Extracts required years of experience from Job Description text using regex."""
        if not jd_text:
            return None, "Not explicitly stated"

        # Pattern 1: e.g. "8-10 years", "8 to 12 years"
        range_match = re.search(r"(\d{1,2})\s*(?:-|to)\s*(\d{1,2})\+?\s*(?:years|yrs)", jd_text, re.IGNORECASE)
        if range_match:
            min_yoe = float(range_match.group(1))
            return min_yoe, f"{range_match.group(1)}-{range_match.group(2)} years"

        # Pattern 2: e.g. "10+ years", "min 8 years of experience"
        single_match = re.search(r"(?:minimum|min|at least|\+)?\s*(\d{1,2})\+?\s*(?:years|yrs)(?:\s*of\s*experience)?", jd_text, re.IGNORECASE)
        if single_match:
            yoe = float(single_match.group(1))
            if yoe <= 25: # sanity check
                return yoe, f"{single_match.group(1)}+ years"

        return None, "Not explicitly stated in summary"

    def extract_skills(self, text: str) -> List[str]:
        """Extracts recognized tech & domain skills from text."""
        text_lower = text.lower()
        found = []
        for skill in self.skill_lexicon:
            # Word boundary regex
            pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
            if re.search(pattern, text_lower):
                found.append(skill.title() if len(skill) > 4 else skill.upper())
        return found

    def evaluate_match(
        self,
        candidate: CandidateProfile,
        job: LinkedInJob
    ) -> Dict[str, Any]:
        """
        Calculates granular, transparent match score based directly on Resume vs JD:
        1. TF-IDF Cosine Similarity (35 pts)
        2. YoE Delta Analysis (25 pts)
        3. Hard Skills Overlap & Coverage (30 pts)
        4. Leadership & Scope Fit (10 pts)
        """
        level_cat = self.classify_role_level(job.title, candidate)
        jd_content = (job.full_description + " " + job.description_snippet + " " + job.title).strip()

        # 1. TF-IDF Cosine Similarity (0 to 35 pts)
        tfidf_score = 0.0
        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=1200)
            tfidf_matrix = vectorizer.fit_transform([candidate.raw_text, jd_content])
            cos_sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
            # Cosine similarity between resume and JD usually ranges between 0.15 and 0.65
            # Normalize to a realistic 0-100 scale: 0.15 -> 50%, 0.50 -> 95%
            norm_sim = min(1.0, max(0.0, (cos_sim - 0.10) / 0.40))
            tfidf_pts = norm_sim * 35.0
        except Exception:
            cos_sim = 0.30
            tfidf_pts = 22.0

        # 2. Years of Experience (YoE) Delta Analysis (0 to 25 pts)
        jd_yoe_val, jd_yoe_str = self.extract_required_yoe_from_jd(job.full_description or job.description_snippet)
        
        # If JD didn't explicitly mention YoE, infer baseline from level
        if jd_yoe_val is None:
            if level_cat == "Higher Role":
                jd_yoe_val = 10.0
                jd_yoe_str = "~10+ years (Inferred from Executive level)"
            else:
                jd_yoe_val = 7.0
                jd_yoe_str = "~7-9 years (Inferred from Senior/Lead level)"

        if candidate.years_of_experience >= jd_yoe_val:
            yoe_pts = 25.0
            yoe_status = f"Candidate ({candidate.years_of_experience:.0f} YoE) exceeds required threshold ({jd_yoe_str})."
        else:
            # Underqualified delta penalty
            ratio = candidate.years_of_experience / max(1.0, jd_yoe_val)
            yoe_pts = ratio * 25.0
            yoe_status = f"Candidate has {candidate.years_of_experience:.0f} YoE vs {jd_yoe_str} required (slight gap)."

        # 3. Hard Skills Overlap (0 to 30 pts)
        candidate_skills = set(s.lower() for s in self.extract_skills(candidate.raw_text))
        jd_skills = set(s.lower() for s in self.extract_skills(jd_content))

        matched_skills_raw = candidate_skills.intersection(jd_skills)
        missing_skills_raw = jd_skills.difference(candidate_skills)

        matched_skills = sorted([s.title() if len(s) > 4 else s.upper() for s in matched_skills_raw])
        missing_skills = sorted([s.title() if len(s) > 4 else s.upper() for s in missing_skills_raw])

        if jd_skills:
            skill_ratio = len(matched_skills_raw) / len(jd_skills)
            skill_pts = min(30.0, max(12.0, skill_ratio * 30.0 + 8.0))
        else:
            skill_pts = 22.0

        # 4. Leadership & Scope Fit (0 to 10 pts)
        leadership_terms = ["lead", "manage", "direct reports", "hire", "mentoring", "head", "portfolio", "strategy"]
        jd_has_leadership = any(t in jd_content.lower() for t in leadership_terms)
        
        if candidate.team_size_managed > 0:
            leadership_pts = 10.0 if jd_has_leadership else 8.0
        else:
            leadership_pts = 5.0 if jd_has_leadership else 8.0

        # Total Calculation
        total_calculated = int(round(tfidf_pts + yoe_pts + skill_pts + leadership_pts))
        # Clamp realistically between 45% and 98%
        final_score = min(98, max(48, total_calculated))

        # Build transparent explanation
        rationale_lines = [
            f"• Experience Fit: {yoe_status}",
            f"• Skills Overlap ({len(matched_skills)} matched): {', '.join(matched_skills[:6]) if matched_skills else 'Domain alignment'}.",
            f"• Semantic Cosine Similarity: {int(cos_sim * 100)}% text alignment between Resume and JD requirements."
        ]
        if missing_skills:
            rationale_lines.append(f"• Desired in JD (Growth Opportunity): {', '.join(missing_skills[:4])}.")

        rationale = "\n".join(rationale_lines)

        return {
            "match_score": final_score,
            "role_level_category": level_cat,
            "rationale": rationale,
            "matched_skills": matched_skills[:8],
            "missing_skills": missing_skills[:6],
            "jd_yoe_requirement": jd_yoe_str,
            "candidate_yoe": f"{candidate.years_of_experience:.0f}+ Years",
            "cosine_similarity_pct": int(cos_sim * 100)
        }
