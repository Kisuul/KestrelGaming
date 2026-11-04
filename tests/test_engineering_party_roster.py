"""Static checks for the proposed engineering party manifest; no agent is run."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class EngineeringPartyRosterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = json.loads((ROOT / "agents/ROSTER_V1.json").read_text(encoding="utf-8"))

    def test_seven_distinct_characters_and_branches(self):
        people = self.m["members"]
        self.assertEqual(len(people), 7)
        self.assertEqual(len({p["id"] for p in people}), 7)
        self.assertEqual(len({p["branch"] for p in people}), 7)
        self.assertEqual(len({p["first_move"] for p in people}), 7)
        self.assertEqual(len({p["review_question"] for p in people}), 7)

    def test_each_branch_is_an_agent_home(self):
        for p in self.m["members"]:
            with self.subTest(agent=p["id"]):
                self.assertEqual(p["branch"], "agents/" + p["id"] + "-v1")
                self.assertIn("/agents/" + p["id"] + "/AGENT.md", p["entrypoint_url"])
                self.assertIn("/agents/" + p["id"] + "/PROFILE.json", p["profile_url"])

    def test_roster_grants_no_permissions(self):
        self.assertEqual(self.m["schema"]["status"], "PROPOSED_NOT_EMBODIED")
        for p in self.m["members"]:
            self.assertIsNone(p["agent_runtime_id"])
            self.assertFalse(p["permissions_granted"])
            self.assertFalse(p["behavioral_certified"])

    def test_every_member_has_a_different_success_condition(self):
        self.assertEqual(len({p["win"] for p in self.m["members"]}), 7)
        self.assertIn("No ensemble task", self.m["evaluation_status"])

if __name__ == "__main__":
    unittest.main()
