from typing import List, Dict, Any, Optional
from curl_cffi import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import time
import warnings

warnings.filterwarnings("ignore")

from datetime import datetime, timedelta

def parse_posted_time(datetime_str: str, text_str: str) -> tuple[str, float]:
    """Converts LinkedIn datetime attribute or relative text into ISO date and epoch timestamp."""
    now = datetime.now()
    
    # 1. Try ISO date attribute first (e.g. '2026-09-30')
    if datetime_str and re.match(r"^\d{4}-\d{2}-\d{2}", datetime_str):
        try:
            dt = datetime.fromisoformat(datetime_str[:10])
            return dt.strftime("%Y-%m-%d"), dt.timestamp()
        except Exception:
            pass

    # 2. Parse relative time text (e.g. '3 hours ago', '2 days ago', '1 week ago')
    clean_text = text_str.lower().strip()
    if not clean_text or "just now" in clean_text:
        return now.strftime("%Y-%m-%d"), now.timestamp()

    num_match = re.search(r"(\d+)", clean_text)
    num = int(num_match.group(1)) if num_match else 1

    if "minute" in clean_text:
        target_dt = now - timedelta(minutes=num)
    elif "hour" in clean_text:
        target_dt = now - timedelta(hours=num)
    elif "day" in clean_text:
        target_dt = now - timedelta(days=num)
    elif "week" in clean_text:
        target_dt = now - timedelta(weeks=num)
    elif "month" in clean_text:
        target_dt = now - timedelta(days=num * 30)
    elif "year" in clean_text:
        target_dt = now - timedelta(days=num * 365)
    else:
        target_dt = now - timedelta(days=1)

    return target_dt.strftime("%Y-%m-%d"), target_dt.timestamp()

class LinkedInJob:
    def __init__(
        self,
        job_id: str,
        title: str,
        company: str,
        location: str,
        url: str,
        posted_time: str = "",
        posted_date_iso: str = "",
        posted_timestamp: float = 0.0,
        seniority: str = "",
        description_snippet: str = "",
        full_description: str = ""
    ):
        self.job_id = job_id
        self.title = title
        self.company = company
        self.location = location
        self.url = url
        self.posted_time = posted_time
        self.posted_date_iso = posted_date_iso
        self.posted_timestamp = posted_timestamp
        self.seniority = seniority
        self.description_snippet = description_snippet
        self.full_description = full_description
        self.role_level_category = "Higher Role"
        self.hiring_manager: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "url": self.url,
            "posted_time": self.posted_time,
            "posted_date_iso": self.posted_date_iso,
            "posted_timestamp": self.posted_timestamp,
            "seniority": self.seniority,
            "description_snippet": self.description_snippet,
            "full_description": self.full_description,
            "role_level_category": self.role_level_category,
            "hiring_manager": self.hiring_manager
        }


class LinkedInClient:
    """Live LinkedIn Client with pagination, full JD extraction, and browser impersonation."""

    def __init__(self):
        self.base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self._jd_cache: Dict[str, Dict[str, Any]] = {}

    def search_jobs(
        self,
        keywords: str,
        location: str = "Bengaluru, Karnataka, India",
        limit: int = 10,
        start_offset: int = 0,
        fetch_full_jd: bool = True
    ) -> List[LinkedInJob]:
        """Fetch live jobs from LinkedIn Guest Search API with pagination support."""
        params = {
            "keywords": keywords,
            "location": location,
            "sortBy": "DD", # Sort by Date Posted (newest first)
            "start": start_offset
        }
        jobs = []
        try:
            resp = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                impersonate="chrome124",
                verify=False,
                timeout=15
            )
            if resp.status_code != 200:
                print(f"[!] LinkedIn API responded with status {resp.status_code} for '{keywords}'")
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.find_all("li")

            for item in items:
                if len(jobs) >= limit:
                    break

                title_el = item.find("h3", class_=re.compile("base-search-card__title"))
                comp_el = item.find("h4", class_=re.compile("base-search-card__subtitle"))
                link_el = item.find("a", class_=re.compile("base-card__full-link"))
                loc_el = item.find("span", class_=re.compile("job-search-card__location"))
                time_el = item.find("time")

                if not title_el or not link_el:
                    continue

                raw_link = link_el.get("href", "")
                clean_url = raw_link.split("?")[0]
                job_id_match = re.search(r"-(\d{8,12})(?:\?|$)", clean_url)
                job_id = job_id_match.group(1) if job_id_match else str(abs(hash(clean_url)))

                title = title_el.get_text(strip=True)
                company = comp_el.get_text(strip=True) if comp_el else "Unknown Company"
                loc = loc_el.get_text(strip=True) if loc_el else location
                
                posted_text = time_el.get_text(strip=True) if time_el else ""
                datetime_attr = time_el.get("datetime", "") if time_el else ""
                posted_iso, posted_ts = parse_posted_time(datetime_attr, posted_text)

                job = LinkedInJob(
                    job_id=job_id,
                    title=title,
                    company=company,
                    location=loc,
                    url=clean_url,
                    posted_time=posted_text,
                    posted_date_iso=posted_iso,
                    posted_timestamp=posted_ts
                )

                # Fetch full JD if requested (for deep resume vs JD matching)
                if fetch_full_jd:
                    details = self.fetch_job_details(clean_url)
                    job.full_description = details.get("description", "")
                    job.seniority = details.get("seniority", "")
                    job.description_snippet = job.full_description[:280] if job.full_description else ""

                jobs.append(job)

        except Exception as e:
            print(f"[!] Error fetching LinkedIn jobs for '{keywords}': {e}")

        return jobs

    def fetch_job_details(self, job_url: str) -> Dict[str, Any]:
        """Fetch detailed description and metadata for a specific LinkedIn job posting."""
        if job_url in self._jd_cache:
            return self._jd_cache[job_url]

        details = {
            "seniority": "",
            "employment_type": "",
            "description": "",
            "on_page_poster": None
        }
        try:
            resp = requests.get(
                job_url,
                headers=self.headers,
                impersonate="chrome124",
                verify=False,
                timeout=10
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Check criteria
                criteria_items = soup.find_all("li", class_=re.compile("description__job-criteria-item"))
                for item in criteria_items:
                    header = item.find("h3")
                    val = item.find("span")
                    if header and val:
                        h_text = header.get_text(strip=True).lower()
                        v_text = val.get_text(strip=True)
                        if "seniority" in h_text:
                            details["seniority"] = v_text
                        elif "employment" in h_text:
                            details["employment_type"] = v_text

                # Check description
                desc_el = soup.find("div", class_=re.compile("show-more-less-html__markup"))
                if desc_el:
                    details["description"] = desc_el.get_text(separator=" ", strip=True)

                # Check on-page recruiter/hirer
                poster_card = soup.find("div", class_=re.compile("message-the-recruiter|hiring-team|hirer"))
                if poster_card:
                    name_el = poster_card.find(re.compile("h\d|span"), class_=re.compile("name|title"))
                    link_el = poster_card.find("a", href=re.compile("linkedin.com/in/"))
                    if name_el and link_el:
                        details["on_page_poster"] = {
                            "name": name_el.get_text(strip=True),
                            "linkedin_url": link_el.get("href", "").split("?")[0]
                        }
        except Exception:
            pass

        self._jd_cache[job_url] = details
        return details
