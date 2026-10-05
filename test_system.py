import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import unittest
from pathlib import Path
from core.resume_parser import ResumeParser
from core.matcher import OpportunityMatcher
from core.hiring_manager_finder import HiringManagerFinder
from core.outreach_generator import OutreachGenerator
from core.linkedin_client import LinkedInJob

class TestProductHiringManagerSystem(unittest.TestCase):

    def setUp(self):
        self.pm_resume = Path("sample_resumes/twisha_prasad.txt").read_text(encoding="utf-8")
        self.ds_resume = Path("sample_resumes/aryan_sharma_data_science_lead.txt").read_text(encoding="utf-8")
        self.parser = ResumeParser()
        self.matcher = OpportunityMatcher()
        self.hm_finder = HiringManagerFinder()
        self.outreach_gen = OutreachGenerator()

    def test_resume_parser_pm(self):
        cand = self.parser.parse(self.pm_resume)
        self.assertEqual(cand.name, "TWISHA PRASAD")
        self.assertEqual(cand.track, "PRODUCT")
        self.assertGreaterEqual(cand.years_of_experience, 12.0)
        self.assertIn("Director of Product", cand.target_higher_roles)
        self.assertIn("Group Product Manager", cand.target_similar_roles)
        print("[PASS] ResumeParser (PM) test passed!")

    def test_resume_parser_ds(self):
        cand = self.parser.parse(self.ds_resume)
        self.assertEqual(cand.track, "DATA_SCIENCE")
        self.assertGreaterEqual(cand.years_of_experience, 11.0)
        self.assertIn("Director of Data Science", cand.target_higher_roles)
        self.assertIn("Lead Data Scientist", cand.target_similar_roles)
        self.assertIn("Python", cand.skills)
        print("[PASS] ResumeParser (Data Science) test passed!")

    def test_matcher_granularity_and_skills(self):
        cand = self.parser.parse(self.ds_resume)
        job = LinkedInJob(
            job_id="999",
            title="Director Data Science",
            company="Meesho",
            location="Bengaluru",
            url="https://in.linkedin.com/jobs/view/999",
            full_description="Looking for Director of Data Science with 10+ years experience in Python, PyTorch, Transformers, Deep Learning, and MLOps to lead our search and recommendation ranking teams."
        )
        match_data = self.matcher.evaluate_match(cand, job)
        self.assertEqual(match_data["role_level_category"], "Higher Role")
        self.assertIn("Pytorch", [s.title() for s in match_data["matched_skills"]])
        self.assertGreater(match_data["match_score"], 60)
        print(f"[PASS] Matcher JD test passed! Score: {match_data['match_score']}%, Matched Skills: {match_data['matched_skills']}")

    def test_hiring_manager_finder_ds(self):
        hm = self.hm_finder.find_hiring_manager("Meesho", "Director Data Science", candidate_track="DATA_SCIENCE")
        self.assertIn("linkedin.com/in/", hm["linkedin_url"])
        self.assertTrue(len(hm["name"]) > 2)
        print(f"[PASS] HiringManagerFinder (DS) test passed! Found: {hm['name']} ({hm['title']}) -> {hm['linkedin_url']}")

if __name__ == "__main__":
    unittest.main()
