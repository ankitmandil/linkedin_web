from typing import Dict, Any
from core.resume_parser import CandidateProfile
from core.linkedin_client import LinkedInJob

class OutreachGenerator:
    """Generates hyper-personalized outreach pitches across Data Science, Product, and Engineering tracks."""

    def generate_connection_note(
        self,
        candidate: CandidateProfile,
        job: LinkedInJob,
        hiring_manager: Dict[str, Any]
    ) -> str:
        """Generates a LinkedIn connection request note strictly under 300 characters."""
        hm_name = hiring_manager.get("name", "there").split()[0]
        
        if candidate.track == "DATA_SCIENCE":
            note = (
                f"Hi {hm_name}, saw {job.company}'s opening for {job.title}. "
                f"With {candidate.years_of_experience:.0f}+ yrs in AI/ML & LLM platforms at {candidate.current_company}, "
                f"I'd love to connect and explore how my deep learning & recommendation architecture experience can add value!"
            )
        else: # PRODUCT
            note = (
                f"Hi {hm_name}, saw {job.company}'s hiring for {job.title}. "
                f"As a GPM with {candidate.years_of_experience:.0f}+ yrs leading 6 PMs & driving ₹1,500 Cr GMV at {candidate.current_company}, "
                f"I'd love to connect and explore how my marketplace & platform experience can add value!"
            )

        if len(note) > 300:
            note = (
                f"Hi {hm_name}, saw {job.company}'s opening for {job.title}. "
                f"With {candidate.years_of_experience:.0f}+ yrs in {candidate.track.replace('_', ' ').title()} at {candidate.current_company}, "
                f"I'd love to connect and explore synergies!"
            )
        return note

    def generate_inmail_pitch(
        self,
        candidate: CandidateProfile,
        job: LinkedInJob,
        hiring_manager: Dict[str, Any]
    ) -> str:
        """Generates an executive InMail / Email message tailored to the role and hiring manager."""
        hm_name = hiring_manager.get("name", "Hiring Leader").split()[0]
        hm_title = hiring_manager.get("title", "Leadership")
        comp = job.company
        title = job.title

        if candidate.track == "DATA_SCIENCE":
            charter_focus = (
                "• Production AI & Scale: Spearheaded core recommendation and ranking engines serving 20M+ DAU, "
                "improving conversion and generating ₹120 Cr+ in incremental GMV through two-tower deep retrieval.\n"
                "• GenAI & LLMs: Architected end-to-end LLM fine-tuning pipelines (LoRA/vLLM) and dense retrieval RAG architectures, reducing query abandonment by 28%.\n"
                f"• Technical & Team Leadership: Mentored and led teams of {candidate.team_size_managed or '8'} Data Scientists and ML Engineers, establishing MLOps standards with Kubeflow, MLflow, and Triton."
            )
        else:
            charter_focus = (
                "• Marketplace & Growth Scale: Expanded marketplace conversion from 12% to 17% (+5pp), contributing ~₹1,500 Cr incremental GMV across ~35M tickets/month.\n"
                "• Payments & Platform Reliability: Reduced payment failure rate by 3pp & increased checkout conversion from 55% to 64% (+9pp), contributing ~₹20 Cr incremental revenue and ₹365 Cr GMV.\n"
                f"• Team Leadership: Built and mentored a team of {candidate.team_size_managed or '6'} PMs across career stages, defining hiring rubrics and governing data/AI experimentation org-wide."
            )

        inmail = f"""Subject: Regarding {title} at {comp} — {candidate.name} ({candidate.current_title}, {candidate.years_of_experience:.0f}+ YoE)

Hi {hm_name},

I hope this message finds you well. I noticed that {comp} is actively looking for a {title}. Given your leadership as {hm_title}, I wanted to reach out directly.

Currently, I serve as {candidate.current_title} at {candidate.current_company}. With {candidate.years_of_experience:.0f}+ years of experience building and scaling high-impact initiatives, I bring a proven track record of translating complex problems into scalable business and technical outcomes:

{charter_focus}
• Strategic Execution: Experience leading cross-functional teams across engineering, product, and leadership, driving measurable top-line metrics and operational efficiency.

I would love to learn more about the strategic priorities for the {title} charter at {comp} and share how my background can help accelerate your team's goals.

Do you have 15 minutes for a brief introductory conversation next week?

Best regards,

{candidate.name}
{candidate.email} | {candidate.phone}
LinkedIn: {candidate.summary}
"""
        return inmail.strip()
