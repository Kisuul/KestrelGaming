"""Pinned official PixiJS Agent Skills integrity and discovery tests (offline)."""
from pathlib import Path
import hashlib
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "third_party/pixijs-skills/manifest.json"


class PixiVendorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_upstream_pin_and_import_counts(self):
        self.assertEqual(self.manifest["upstream_commit"], "83760c6f53462ca9cecd68055041f5a8c94758ce")
        self.assertEqual(len(self.manifest["files"]), 65)
        skills = [r for r in self.manifest["files"] if r["path"].endswith("/SKILL.md")]
        self.assertEqual(len(skills), 26)

    def test_imported_file_set_is_exact(self):
        expected = {r["path"] for r in self.manifest["files"]}
        actual = {
            file.relative_to(ROOT).as_posix()
            for directory in (ROOT / "skills").iterdir()
            if directory.is_dir() and (directory.name == "pixijs" or directory.name.startswith("pixijs-"))
            for file in directory.rglob("*.md")
        }
        self.assertEqual(actual, expected)

    def test_all_imported_blobs_match_pinned_sha(self):
        for entry in self.manifest["files"]:
            with self.subTest(path=entry["path"]):
                data = (ROOT / entry["path"]).read_bytes()
                self.assertEqual(len(data), entry["size"])
                object_bytes = f"blob {len(data)}\0".encode("ascii") + data
                self.assertEqual(hashlib.sha1(object_bytes).hexdigest(), entry["sha"])

    def test_catalog_routes_to_all_imported_skills(self):
        index = (ROOT / "skills/INDEX.md").read_text(encoding="utf-8")
        router = (ROOT / "skills/pixijs/SKILL.md").read_text(encoding="utf-8")
        for entry in self.manifest["files"]:
            if not entry["path"].endswith("/SKILL.md"):
                continue
            skill = entry["path"].split("/")[1]
            self.assertIn(f"({skill}/SKILL.md)", index)
            if skill != "pixijs":
                self.assertIn(f"../{skill}/SKILL.md", router)

    def test_mit_notice_retained(self):
        license_text = (ROOT / "third_party/pixijs-skills/LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", license_text)
        self.assertIn("Copyright (c) 2026 PixiJS", license_text)
        self.assertIn("Permission is hereby granted", license_text)


if __name__ == "__main__":
    unittest.main()
