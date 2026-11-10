"""PR #18 hostile, observational regression probes.

These tests intentionally ASSERT behaviors that should not be mistaken for
successful memory-index validation. Passing audit tests show a gap exists.
All modifications are to disposable local copies of the candidate snapshot.
The candidate PR is NOT modified.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import validate_seed


class ReconciliationHostileProbes(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "reconciled"
        shutil.copytree(
            ROOT, self.root,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        self.catalog = self.root / "memory/projects/INDEX.md"
        self.catalog_entry = (
            "| [cosmicdance-4-2-0/Auralprinter]"
            "(cosmicdance-4-2-0/auralprinter/INDEX.md) |"
            " Audio reference platform, development principles, and checkpoint continuity |"
        )
        self.assertIn(self.catalog_entry, self.catalog.read_text())

    def test_a01_escaped_catalog_link_falsely_registers_imported_memory(self):
        """Failing-condition proof: literal escaped bracket still counts as link."""
        original = self.catalog.read_text()
        self.catalog.write_text(
            original.replace(
                self.catalog_entry,
                self.catalog_entry.replace(
                    "[cosmicdance-4-2-0/Auralprinter]",
                    "\\[cosmicdance-4-2-0/Auralprinter]"
                )
            ), encoding="utf-8"
        )
        self.assertEqual(
            [], validate_seed.validate(self.root),
            "BUG PROOF: structural validator should reject a non-link registration"
        )

    def test_a02_raw_html_pre_catalog_link_falsely_registers_imported_memory(self):
        """Failing-condition proof: a Markdown link inside HTML pre is not navigable."""
        original = self.catalog.read_text()
        non_link = (
            "<pre>\n"
            "[cosmicdance-4-2-0/Auralprinter]"
            "(cosmicdance-4-2-0/auralprinter/INDEX.md)\n"
            "</pre>"
        )
        self.catalog.write_text(
            original.replace(self.catalog_entry, non_link), encoding="utf-8"
        )
        self.assertEqual([], validate_seed.validate(self.root))

    def test_a03_roster_url_can_point_to_nonexistent_branch_and_ci_still_passes(self):
        """Gap proof only: existing tests check URL shape, not actual GitHub refs."""
        manifest = self.root / "agents/ROSTER_V1.json"
        data = json.loads(manifest.read_text())
        member = data["members"][0]
        self.assertEqual("mothlight", member["id"])
        member["profile_url"] = member["profile_url"].replace(
            "agents/mothlight-v1/", "agents/deliberately-nonexistent-audit-ref/"
        )
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover",
             "-s", "tests", "-p", "test_engineering_party_roster.py", "-v"],
            cwd=self.root, capture_output=True, text=True, check=False
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertEqual([], validate_seed.validate(self.root))

    def test_safe_control_unmodified_import_is_structurally_valid(self):
        """Positive control for exact checked-out PR snapshot; no agent is launched."""
        self.assertEqual([], validate_seed.validate(self.root))
        data = json.loads((self.root / "agents/ROSTER_V1.json").read_text())
        self.assertEqual(7, len(data["members"]))
        self.assertEqual("PROPOSED_NOT_EMBODIED", data["schema"]["status"])


if __name__ == "__main__":
    unittest.main()
