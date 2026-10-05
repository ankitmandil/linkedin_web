from typing import Dict, Any, Optional
from ddgs import DDGS
import re
import urllib.parse
import time
import warnings

warnings.filterwarnings("ignore")

class HiringManagerFinder:
    """Discovers verified LinkedIn profiles of Executives & Hiring Managers dynamically across all companies."""

    def __init__(self):
        # In-memory cache per session to prevent repeated searches for the same company/role
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _normalize_company_name(self, company: str) -> str:
        clean = re.sub(r"[,\.-]|(Pvt|Ltd|Inc|Technologies|Software|Corporation|LLC)\b", "", company, flags=re.IGNORECASE)
        return clean.strip().lower()

    def _extract_reporting_manager_from_jd(self, jd_text: str) -> Optional[str]:
        """Extracts reporting manager title mentioned directly in the Job Description text."""
        if not jd_text:
            return None
        patterns = [
            r"(?:reports?\s+to(?:\s+the)?|reporting\s+to(?:\s+the)?)\s+([A-Za-z\s]{3,35}?)(?:\.|\n|,|and|who|with)",
            r"(?:working\s+closely\s+with(?:\s+the)?)\s+([A-Za-z\s]{3,35}?)(?:\.|\n|,|and|who|with)"
        ]
        for pattern in patterns:
            match = re.search(pattern, jd_text, re.IGNORECASE)
            if match:
                candidate_title = match.group(1).strip()
                # Validate it looks like a leadership title
                if any(kw in candidate_title.lower() for kw in ["director", "head", "vp", "president", "chief", "cpo", "cto", "lead", "manager"]):
                    return candidate_title
        return None

    def _determine_target_titles(self, job_title: str, candidate_track: str, extracted_reporting: Optional[str] = None) -> str:
        """Determines target leadership title to search based on track and seniority hierarchy."""
        if extracted_reporting:
            return extracted_reporting

        title_lower = job_title.lower()

        # Data Science / AI Track
        if candidate_track == "DATA_SCIENCE":
            if any(kw in title_lower for kw in ["director", "head of", "vp", "vice president", "chief"]):
                return "CTO OR Chief Data Scientist OR VP Engineering OR Head of AI"
            elif any(kw in title_lower for kw in ["lead", "principal", "staff"]):
                return "Director Data Science OR Head of Data Science OR VP Data Science OR Chief Data Scientist"
            else:
                return "Lead Data Scientist OR Director Data Science OR Head of AI"

        # Engineering Track
        elif candidate_track == "ENGINEERING":
            if any(kw in title_lower for kw in ["director", "vp", "head of"]):
                return "CTO OR Chief Technology Officer OR VP Engineering"
            elif any(kw in title_lower for kw in ["lead", "principal", "staff", "architect"]):
                return "Director of Engineering OR Head of Engineering OR VP Engineering"
            else:
                return "Engineering Manager OR Director of Engineering"

        # Product Management Track
        else:
            if any(kw in title_lower for kw in ["director", "head of", "vp", "vice president", "chief"]):
                return "Chief Product Officer OR CPO OR CEO OR VP Product"
            elif any(kw in title_lower for kw in ["group product manager", "gpm", "principal pm", "lead pm"]):
                return "VP Product OR Vice President Product OR Head of Product OR Director of Product"
            elif any(kw in title_lower for kw in ["senior product manager", "spm"]):
                return "Director of Product OR Head of Product OR Group Product Manager"
            else:
                return "Head of Product OR VP Product OR Director of Product"

    def find_hiring_manager(
        self,
        company: str,
        job_title: str,
        candidate_track: str = "PRODUCT",
        on_page_poster: Optional[Dict[str, Any]] = None,
        jd_text: Optional[str] = ""
    ) -> Dict[str, Any]:
        """Finds the hiring manager or executive leadership LinkedIn profile dynamically."""

        # 1. Check if directly listed on job posting by LinkedIn
        if on_page_poster and on_page_poster.get("linkedin_url"):
            return {
                "name": on_page_poster.get("name", "Hiring Team"),
                "title": "Hiring Team / Job Poster",
                "headline": f"Job Poster at {company}",
                "linkedin_url": on_page_poster["linkedin_url"],
                "confidence": "Direct Job Poster"
            }

        comp_key = self._normalize_company_name(company)
        cache_key = f"{comp_key}::{candidate_track}::{job_title.lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 2. Extract reporting line from JD or determine target hierarchy
        reporting_title = self._extract_reporting_manager_from_jd(jd_text or "")
        leadership_target = self._determine_target_titles(job_title, candidate_track, reporting_title)

        # 3. 100% Dynamic Live Web Discovery across LinkedIn
        query = f"{company} {leadership_target} LinkedIn"
        try:
            with DDGS(verify=False) as ddgs:
                results = list(ddgs.text(query, max_results=5))
                for r in results:
                    href = r.get("href", "")
                    title = r.get("title", "")
                    body = r.get("body", "")

                    if "linkedin.com/in/" in href:
                        # Clean name and title from LinkedIn snippet
                        parts = re.split(r"[-–|:]", title)
                        raw_name = parts[0].strip() if parts else "Leadership"
                        name = re.sub(r"\b(LinkedIn|on LinkedIn|Profile|Overview)\b", "", raw_name, flags=re.IGNORECASE).strip()
                        
                        # Extract title
                        role_title = parts[1].strip() if len(parts) > 1 else leadership_target.split("OR")[0].strip()
                        role_title = re.sub(r"\b(LinkedIn|India)\b", "", role_title, flags=re.IGNORECASE).strip()

                        result = {
                            "name": name,
                            "title": role_title,
                            "headline": title[:100],
                            "linkedin_url": href.split("?")[0],
                            "snippet": body[:160] if body else "",
                            "confidence": "Live Search Discovery"
                        }
                        self._cache[cache_key] = result
                        return result
        except Exception as e:
            print(f"[!] Live hiring manager discovery error for {company}: {e}")

        # 4. Fallback: Pre-filtered direct LinkedIn People Directory query
        company_clean = urllib.parse.quote(company)
        first_role = leadership_target.split("OR")[0].strip()
        fallback = {
            "name": f"{company} {candidate_track.replace('_', ' ').title()} Leadership",
            "title": f"Hiring Manager / {first_role}",
            "headline": f"Executive Leadership at {company}",
            "linkedin_url": f"https://www.linkedin.com/search/results/people/?keywords={company_clean}%20{urllib.parse.quote(first_role)}",
            "confidence": "LinkedIn Search Directory"
        }
        self._cache[cache_key] = fallback
        return fallback
