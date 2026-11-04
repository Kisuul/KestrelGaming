"""Static documentation and template checks for the branch-per-agent contract.

These tests do not launch LLMs, prove personality, authenticate identities,
or establish that an agent host loads the documented files.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "AGENT_STRUCTURE.md"
PICKUP = ROOT / "docs" / "AGENT_PICKUP.md"
PERSONA = ROOT / "kestrel" / "templates" / "AGENT_CHARACTER.md"
PROFILE = ROOT / "kestrel" / "templates" / "AGENT_PROFILE.json"


class IndividualAgentContractDocumentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads(PROFILE.read_text(encoding="utf-8"))

    def test_docs_and_root_discovery(self):
        structure = DOC.read_text(encoding="utf-8")
        pickup = PICKUP.read_text(encoding="utf-8")
        entry = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for doc in (structure, pickup):
            self.assertIn("Kestrel", doc)
        for locator in ("docs/AGENT_STRUCTURE.md", "docs/AGENT_PICKUP.md"):
            self.assertIn(locator, entry)
            self.assertIn(locator, readme)
        self.assertIn("Role pickup receipt", pickup)
        self.assertIn("independent", structure.lower())

    def test_template_has_distinct_personality_and_evidence_contract(self):
        prose = PERSONA.read_text(encoding="utf-8")
        for heading in (
            "## First-person identity",
            "## What winning means to me",
            "## How I engineer",
            "## Our common test",
            "## Boundaries and independence",
            "## Boot and memory",
        ):
            self.assertIn(heading, prose)
        for phrase in ("Repair signature", "Personal win condition", "No hidden"):
            self.assertIn(phrase, prose)
        self.assertIn("REPLACE_AGENT_ID", prose)

    def test_json_template_is_draft_with_no_fabricated_history(self):
        p = self.profile
        self.assertEqual(p["schema"]["name"], "KestrelAgentCharacter")
        self.assertEqual(p["schema"]["version"], "0.1")
        self.assertEqual(p["schema"]["status"], "DRAFT")
        self.assertIsNone(p["metadata"]["runtime_identity_id"])
        self.assertEqual(p["metadata"]["established_history"], [])
        self.assertEqual(p["continuity"]["earned_relationships"], [])
        self.assertEqual(p["continuity"]["accepted_lessons"], [])
        self.assertEqual(p["continuity"]["first_state"], "DRAFT_UNINSTANTIATED")
        self.assertIn("REPLACE_AGENT_ID", p["metadata"]["branch"])

    def test_four_independent_normalized_trait_bands(self):
        bands = self.profile["traits"]["bands"]
        self.assertEqual(
            set(bands),
            {
                "cognitive_epistemic_style",
                "creative_exploratory_style",
                "social_collaborative_style",
                "temperament_operational_style",
            },
        )
        for band, weights in bands.items():
            with self.subTest(band=band):
                self.assertTrue(weights)
                self.assertTrue(
                    all(math.isfinite(v) and 0 <= v <= 1 for v in weights.values())
                )
                self.assertAlmostEqual(sum(weights.values()), 1.0, places=8)

    def test_drives_and_authority_are_distinct(self):
        p = self.profile
        drives = p["motivations"]["primary_drives"]
        self.assertTrue(1 <= len(drives) <= 3)
        self.assertEqual([d["rank"] for d in drives], list(range(1, len(drives) + 1)))
        self.assertTrue(all(d["failure_mode"] and d["progress_evidence"] for d in drives))
        self.assertIn("host permissions", p["operating_limits"]["higher_priority_contract"])
        self.assertIn("infer authority", " ".join(p["operating_limits"]["never_do"]))


if __name__ == "__main__":
    unittest.main()
