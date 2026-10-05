import re
from typing import Dict, List, Any, Optional
import os

class CandidateProfile:
    def __init__(
        self,
        name: str,
        email: str,
        phone: str,
        location: str,
        track: str, # "DATA_SCIENCE", "PRODUCT", "ENGINEERING", "ANALYTICS", "GENERAL"
        current_title: str,
        current_company: str,
        years_of_experience: float,
        team_size_managed: int,
        seniority_level: str,
        core_domains: List[str],
        skills: List[str],
        quantified_achievements: List[str],
        target_higher_roles: List[str],
        target_similar_roles: List[str],
        raw_text: str,
        summary: str
    ):
        self.name = name
        self.email = email
        self.phone = phone
        self.location = location
        self.track = track
        self.current_title = current_title
        self.current_company = current_company
        self.years_of_experience = years_of_experience
        self.team_size_managed = team_size_managed
        self.seniority_level = seniority_level
        self.core_domains = core_domains
        self.skills = skills
        self.quantified_achievements = quantified_achievements
        self.target_higher_roles = target_higher_roles
        self.target_similar_roles = target_similar_roles
        self.raw_text = raw_text
        self.summary = summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "track": self.track,
            "current_title": self.current_title,
            "current_company": self.current_company,
            "years_of_experience": self.years_of_experience,
            "team_size_managed": self.team_size_managed,
            "seniority_level": self.seniority_level,
            "core_domains": self.core_domains,
            "skills": self.skills,
            "quantified_achievements": self.quantified_achievements,
            "target_higher_roles": self.target_higher_roles,
            "target_similar_roles": self.target_similar_roles,
            "summary": self.summary
        }


class ResumeParser:
    """Universal Resume Parser that dynamically analyzes career tracks, YoE, skills, and target roles."""

    def __init__(self):
        # Universal skill dictionaries for NLP extraction
        self.known_skills = [
            # Data Science & AI
            "Machine Learning", "Deep Learning", "Python", "PyTorch", "TensorFlow", "Scikit-Learn",
            "Natural Language Processing", "NLP", "Computer Vision", "LLMs", "Generative AI",
            "Transformers", "BERT", "GPT", "RAG", "LangChain", "Vector DB", "Fine-tuning",
            "LoRA", "MLOps", "Kubeflow", "MLflow", "Airflow", "Docker", "Kubernetes",
            "Recommender Systems", "A/B Testing", "Causal Inference", "Statistics", "PySpark",
            "Apache Spark", "Databricks", "BigQuery", "Snowflake", "SQL", "XGBoost", "LightGBM",
            # Product Management
            "Product Strategy", "Consumer Growth", "Marketplaces", "Payments", "Checkout",
            "Juspay", "Loyalty", "Subscriptions", "Search & Personalisation", "Ranking",
            "Product Roadmap", "PRD", "User Research", "Conversion Optimization", "Funnel Optimization",
            # Engineering
            "System Design", "Distributed Systems", "Microservices", "Java", "Golang", "AWS", "GCP"
        ]

    def detect_track(self, text_lower: str) -> str:
        """Determines primary domain track: DATA_SCIENCE, PRODUCT, ENGINEERING, or ANALYTICS."""
        ds_score = sum(1 for kw in [
            "data scientist", "machine learning", "deep learning", "nlp", "computer vision",
            "pytorch", "tensorflow", "llm", "ai architect", "mlops", "data science", "transformers"
        ] if kw in text_lower)

        pm_score = sum(1 for kw in [
            "product manager", "product lead", "gpm", "group product manager", "director of product",
            "vp product", "cpo", "product strategy", "marketplace", "growth charter", "checkout conversion"
        ] if kw in text_lower)

        eng_score = sum(1 for kw in [
            "software engineer", "engineering manager", "backend engineer", "system design",
            "distributed systems", "director of engineering", "vp engineering", "cto"
        ] if kw in text_lower)

        if ds_score > pm_score and ds_score > eng_score:
            return "DATA_SCIENCE"
        elif pm_score >= ds_score and pm_score > eng_score:
            return "PRODUCT"
        elif eng_score > pm_score and eng_score > ds_score:
            return "ENGINEERING"
        return "PRODUCT" if "product" in text_lower else "DATA_SCIENCE"

    def parse(self, text: str) -> CandidateProfile:
        text_clean = text.strip()
        text_lower = text_clean.lower()
        lines = [line.strip() for line in text_clean.split("\n") if line.strip()]

        # 1. Name & Contact
        name = lines[0] if lines else "Candidate"
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text_clean)
        email = email_match.group(0) if email_match else ""
        phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text_clean)
        phone = phone_match.group(0) if phone_match else ""

        # Location detection
        location = "Bengaluru, Karnataka, India"
        for loc_candidate in ["Bengaluru", "Bangalore", "Hyderabad", "Mumbai", "Delhi", "Gurgaon", "Pune", "Chennai", "Noida", "Kolkata"]:
            if loc_candidate.lower() in text_lower:
                location = f"{loc_candidate}, India"
                break

        # 2. Years of Experience calculation
        yoe = 10.0
        yoe_explicit = re.search(r"(\d{1,2})\+?\s*(?:years|yrs)", text_clean, re.IGNORECASE)
        if yoe_explicit:
            yoe = float(yoe_explicit.group(1))
        else:
            years = re.findall(r"\b(19\d\d|20\d\d)\b", text_clean)
            if years:
                int_years = sorted([int(y) for y in years if 1990 <= int(y) <= 2026])
                if len(int_years) >= 2:
                    yoe = max(1.0, float(2026 - int_years[0]))

        # 3. Detect Track
        track = self.detect_track(text_lower)

        # 4. Extract Extracted Skills
        extracted_skills = []
        for s in self.known_skills:
            if re.search(r"\b" + re.escape(s) + r"\b", text_clean, re.IGNORECASE):
                extracted_skills.append(s)

        # 5. Team Size
        team_size = 0
        team_match = re.search(r"(?:lead(?:ing)?|managed|managing|team of)\s+(\d+)\s*(?:-?\s*(?:PMs|scientists|engineers|people|members|direct reports))", text_clean, re.IGNORECASE)
        if team_match:
            team_size = int(team_match.group(1))
        elif "6-PM" in text_clean or "6 PM" in text_clean:
            team_size = 6
        elif "8+" in text_clean and "team" in text_clean:
            team_size = 8

        # 6. Current Title & Company
        current_title = ""
        current_company = ""

        # Check common titles
        if track == "DATA_SCIENCE":
            if any(w in text_lower for w in ["lead data scientist", "lead ai"]):
                current_title = "Lead Data Scientist"
            elif any(w in text_lower for w in ["principal data scientist"]):
                current_title = "Principal Data Scientist"
            elif any(w in text_lower for w in ["head of ai", "head of data science", "director of data science"]):
                current_title = "Director / Head of Data Science"
            elif any(w in text_lower for w in ["senior data scientist"]):
                current_title = "Senior Data Scientist"
            else:
                current_title = "Data Scientist"

            # Check company
            for c in ["Swiggy", "Flipkart", "Razorpay", "Dunzo", "Myntra", "Amazon", "Google", "Microsoft", "Mu Sigma"]:
                if c.lower() in text_lower:
                    current_company = c
                    break
        elif track == "PRODUCT":
            if "Group Product Manager" in text_clean or "GPM" in text_clean:
                current_title = "Group Product Manager 2" if "GPM 2" in text_clean or "GPM2" in text_clean else "Group Product Manager"
            elif "Director" in text_clean:
                current_title = "Director of Product"
            elif "Senior Product Manager" in text_clean:
                current_title = "Senior Product Manager"
            else:
                current_title = "Product Manager"

            for c in ["BookMyShow", "Learnifii", "VMock", "Netomi", "Jarviz", "Swiggy", "Meesho"]:
                if c.lower() in text_lower:
                    current_company = c
                    break

        if not current_title:
            current_title = lines[1] if len(lines) > 1 and len(lines[1]) < 60 else f"{track.replace('_', ' ').title()} Professional"
        if not current_company:
            current_company = "Tech Organization"

        # 7. Dynamically Determine Target Higher & Similar Roles based on Track & YoE
        target_higher_roles = []
        target_similar_roles = []

        if track == "DATA_SCIENCE":
            if yoe >= 9:
                target_higher_roles = [
                    "Director of Data Science",
                    "Head of Data Science",
                    "Head of AI",
                    "VP of Data Science",
                    "VP of AI",
                    "Chief Data Scientist",
                    "Chief Data Officer"
                ]
                target_similar_roles = [
                    "Lead Data Scientist",
                    "Principal Data Scientist",
                    "Staff Data Scientist",
                    "AI Architect"
                ]
            else:
                target_higher_roles = [
                    "Lead Data Scientist",
                    "Staff Data Scientist",
                    "Principal Data Scientist",
                    "Data Science Manager",
                    "Head of Data Science"
                ]
                target_similar_roles = [
                    "Senior Data Scientist",
                    "Data Scientist 2",
                    "Machine Learning Engineer"
                ]
        elif track == "PRODUCT":
            if yoe >= 9:
                target_higher_roles = [
                    "Director of Product",
                    "Director of Product Management",
                    "Senior Director of Product",
                    "Head of Product",
                    "VP of Product",
                    "Vice President of Product",
                    "Chief Product Officer"
                ]
                target_similar_roles = [
                    "Group Product Manager",
                    "Lead Product Manager",
                    "Principal Product Manager",
                    "Staff Product Manager"
                ]
            else:
                target_higher_roles = [
                    "Group Product Manager",
                    "Lead Product Manager",
                    "Principal Product Manager"
                ]
                target_similar_roles = [
                    "Senior Product Manager",
                    "Product Manager"
                ]
        else: # ENGINEERING or other
            target_higher_roles = [
                "Director of Engineering",
                "VP of Engineering",
                "Head of Engineering",
                "Chief Technology Officer"
            ]
            target_similar_roles = [
                "Engineering Manager",
                "Staff Software Engineer",
                "Principal Engineer",
                "Tech Lead"
            ]

        # 8. Quantified Achievements
        achievements = []
        achievement_patterns = [
            r"(?:~?₹[\d,]+\s*(?:Cr|L)|~\$?[\d,]+M|~\d+M\s*(?:tickets|MAU|passes|searches)|\+\d+\.?\d*pp|\+\d+\.?\d*%|\b\d+x\b)[^.\n]+",
            r"(?:Improved|Reduced|Generated|Scaled|Doubled|Spearheaded|Architected|Built)[^.\n]+?(?:\.|\n|$)"
        ]
        for pat in achievement_patterns:
            for m in re.findall(pat, text_clean):
                clean_m = m.strip(" •-\n")
                if 25 < len(clean_m) < 220 and clean_m not in achievements:
                    achievements.append(clean_m)

        # Core Domain Charters
        core_domains = []
        if track == "DATA_SCIENCE":
            if any(w in text_lower for w in ["llm", "generative ai", "transformers", "rag"]):
                core_domains.append("Generative AI & LLMs")
            if any(w in text_lower for w in ["recommender", "ranking", "personalization"]):
                core_domains.append("Recommender & Ranking Systems")
            if any(w in text_lower for w in ["nlp", "bert", "text"]):
                core_domains.append("Natural Language Processing (NLP)")
            if any(w in text_lower for w in ["computer vision", "cv", "cnn", "image"]):
                core_domains.append("Computer Vision & Visual Search")
            if any(w in text_lower for w in ["mlops", "kubeflow", "kubernetes", "deployment"]):
                core_domains.append("MLOps & Production Platforms")
            if not core_domains:
                core_domains.append("Machine Learning & Deep Learning")
        else:
            if any(w in text_lower for w in ["growth", "marketplace", "demand", "supply"]):
                core_domains.append("Consumer Growth & Marketplaces")
            if any(w in text_lower for w in ["payment", "checkout", "fintech", "gateway"]):
                core_domains.append("Payments & Checkout Platforms")
            if any(w in text_lower for w in ["loyalty", "membership", "rewards", "passes"]):
                core_domains.append("Loyalty & Membership Systems")
            if any(w in text_lower for w in ["search", "discovery", "personalisation", "intent"]):
                core_domains.append("Search, Personalisation & Discovery")

        summary = (
            f"{track.replace('_', ' ').title()} Leader with {yoe:.0f}+ years of experience, "
            f"currently {current_title} at {current_company}. Expertise in {', '.join(core_domains[:3])}. "
            f"Targeting Higher roles ({', '.join(target_higher_roles[:2])}) and Similar roles ({', '.join(target_similar_roles[:2])})."
        )

        return CandidateProfile(
            name=name,
            email=email,
            phone=phone,
            location=location,
            track=track,
            current_title=current_title,
            current_company=current_company,
            years_of_experience=yoe,
            team_size_managed=team_size,
            seniority_level=f"{current_title} ({yoe:.0f}+ YoE)",
            core_domains=core_domains,
            skills=extracted_skills[:25],
            quantified_achievements=achievements[:6],
            target_higher_roles=target_higher_roles,
            target_similar_roles=target_similar_roles,
            raw_text=text_clean,
            summary=summary
        )
