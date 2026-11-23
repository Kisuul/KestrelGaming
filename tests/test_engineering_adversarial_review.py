"""Independently check the declared synthetic adversarial review specimens.

No real application is evaluated. This does not establish LLM behavioral skill.
"""
from __future__ import annotations

import difflib
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/engineering-adversarial-review"
PROBE = SKILL / "scripts/fixture_probe.py"
SPEC = importlib.util.spec_from_file_location("adversarial_fixture_probe", PROBE)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(module)


class AdversarialReviewFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = module.evaluate()
        cls.rows = {row["case"]: row for row in cls.result["rows"]}

    def test_all_local_unit_checks_remain_green(self):
        for row in self.rows.values():
            with self.subTest(case=row["case"]):
                self.assertTrue(row["baseline_unit_green"])
                self.assertTrue(row["head_unit_green"])

    def test_cross_boundary_regression_discriminated(self):
        row = self.rows["A"]
        self.assertTrue(row["baseline_acceptance"])
        self.assertFalse(row["head_acceptance"])
        self.assertEqual(row["classification"], "introduced-regression")

    def test_tolerance_weakening_discriminated(self):
        row = self.rows["B"]
        self.assertTrue(row["baseline_acceptance"])
        self.assertFalse(row["head_acceptance"])
        base = module._load("baseline", "b")
        head = module._load("head", "b")
        self.assertGreater(head.TOLERANCE, base.TOLERANCE)
        self.assertGreater(abs(head.gain(1.0) - module.ACCEPTED_GAIN),
                           module.ACCEPTED_GAIN_ABS_ERROR)

    def test_preexisting_failure_is_not_a_new_regression(self):
        row = self.rows["C"]
        self.assertFalse(row["baseline_acceptance"])
        self.assertFalse(row["head_acceptance"])
        self.assertEqual(row["classification"], "pre-existing-defect")
        base = module._load("baseline", "c")
        head = module._load("head", "c")
        self.assertEqual(base.decode_csv(""), head.decode_csv(""))

    def test_clean_decoy_does_not_produce_confirmed_bug(self):
        row = self.rows["D"]
        self.assertTrue(row["baseline_acceptance"])
        self.assertTrue(row["head_acceptance"])
        self.assertEqual(row["classification"], "no-confirmed-defect")
        self.assertIn("FIXME", (SKILL / "fixtures/head/case_d.py").read_text())

    def test_fixture_revisions_are_visibly_distinct(self):
        for case in module.CASES:
            with self.subTest(case=case):
                baseline = (SKILL / f"fixtures/baseline/case_{case}.py").read_text().splitlines()
                head = (SKILL / f"fixtures/head/case_{case}.py").read_text().splitlines()
                diff = list(difflib.unified_diff(baseline, head))
                self.assertTrue(diff)

    def test_probe_is_read_only_on_fixture_sources(self):
        before = module._hash_fixture_sources()
        self.assertTrue(module.verified(module.evaluate()))
        self.assertEqual(before, module._hash_fixture_sources())

    def test_standalone_command_runs_from_any_directory(self):
        completed = subprocess.run([sys.executable, str(PROBE), "--json"],
                                   cwd=str(SKILL), capture_output=True, text=True,
                                   check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"fixture_set": "synthetic-only"', completed.stdout)


if __name__ == "__main__":
    unittest.main()
