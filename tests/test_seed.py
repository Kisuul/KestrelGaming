"""Regression tests for records, navigation, and the read-only validator."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_seed import validate  # noqa: E402

REPOSITORY = Path(__file__).resolve().parents[1]
RECORD = "memory/shared/2026-11-02-central-memory.md"
PROJECT = "memory/projects/kisuul/kestrelgaming"


class SeedValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        shutil.copytree(REPOSITORY, self.root,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", ".kestrel-work"))

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def replace(self, name, old, new):
        path = self.root / name
        self.assertIn(old, path.read_text(encoding="utf-8"))
        self.write(name, path.read_text(encoding="utf-8").replace(old, new))

    def append(self, name, text):
        self.write(name, (self.root / name).read_text(encoding="utf-8") + text)

    def assert_error(self, fragment):
        errors = validate(self.root)
        self.assertTrue(any(fragment in error for error in errors), errors)

    def second_record(self, index=True):
        text = (self.root / RECORD).read_text(encoding="utf-8")
        self.write("memory/shared/second.md", text.replace("id: 2026-11-02-central-memory", "id: second-record"))
        if index:
            self.append("memory/shared/INDEX.md", "\n[Second](second.md)\n")

    def handoff(self):
        text = (self.root / RECORD).read_text(encoding="utf-8")
        text = text.replace("id: 2026-11-02-central-memory", "id: test-handoff")
        text = text.replace("kind: decision", "kind: handoff")
        text = text.replace("scope: shared", "scope: project:kisuul/kestrelgaming")
        text += "\n**Task outcome:** PARTIAL\n\n## Next action\n\nInspect the current project revision.\n"
        name = PROJECT + "/handoffs/test.md"
        self.write(name, text)
        self.append(PROJECT + "/INDEX.md", "\n[Task](handoffs/test.md)\n")
        return name

    def test_repository_is_consistent(self):
        self.assertEqual(validate(REPOSITORY), [])

    def test_validation_does_not_modify_files(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(validate(self.root), [])
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_missing_required_file(self):
        (self.root / "KESTREL.md").unlink()
        self.assert_error("Missing required file: KESTREL.md")

    def test_broken_relative_link(self):
        self.append("README.md", "\n[Missing](not-here.md)\n")
        self.assert_error("Broken relative link")

    def test_encoded_escape_link(self):
        self.append("README.md", "\n[Outside](%2e%2e/outside.md)\n")
        self.assert_error("Link escapes root")

    def test_external_links_anchors_and_code_examples_are_not_checked(self):
        self.append("README.md", '\n[External](https://example.org/no-file)\n[Anchor](#none)\n'
                    '```md\n[Example](absent.md)\n```\n~~~md\n[Other](missing.md)\n~~~\n'
                    '`[Inline example](also-absent.md)`\n')
        self.assertEqual(validate(self.root), [])

    def test_missing_evidence_provenance_field(self):
        self.write(RECORD, "\n".join(line for line in (self.root / RECORD).read_text().splitlines()
                                     if not line.startswith("sources:")) + "\n")
        self.assert_error("missing=['sources']")

    def test_empty_evidence_section(self):
        self.replace(RECORD, "## Evidence", "## Source notes")
        self.assert_error("Missing or empty section: Evidence")

    def test_scope_mismatch_between_same_named_repositories(self):
        self.replace(PROJECT + "/PROFILE.md", "scope: project:kisuul/kestrelgaming",
                     "scope: project:another-owner/kestrelgaming")
        self.assert_error("Scope/path mismatch")

    def test_duplicate_record_ids(self):
        self.second_record()
        self.replace("memory/shared/second.md", "id: second-record", "id: 2026-11-02-central-memory")
        self.assert_error("Duplicate record ID")

    def test_invalid_dates_and_reversed_dates(self):
        original = (self.root / RECORD).read_text()
        for value, expected in [("2026-02-30", "day is out of range"), ("2026-10-01", "Updated date precedes")]:
            with self.subTest(value=value):
                self.write(RECORD, original.replace("updated: 2026-11-02", "updated: " + value))
                self.assert_error(expected)

    def test_unsupported_status_and_schema(self):
        self.replace(RECORD, "status: active", "status: complete")
        self.assert_error("Invalid status")
        self.replace(RECORD, "schema: 1", "schema: 2")
        self.assert_error("Unsupported schema")

    def test_unindexed_record(self):
        self.second_record(index=False)
        self.assert_error("Record not indexed")

    def test_project_catalog_must_reach_project_index(self):
        # Isolate the catalog edge: real skill/evidence docs may also link to a
        # project. Registration despite alternate paths is tested separately.
        self.write("memory/INDEX.md", "# Memory index\n\n[Projects](projects/INDEX.md)\n")
        self.write("memory/projects/INDEX.md", "# Project catalog\n")
        self.assert_error("Unreachable memory file: " + PROJECT + "/INDEX.md")

    def test_project_index_must_be_registered_even_if_linked_elsewhere(self):
        self.write("memory/projects/INDEX.md", "# Project catalog\n")
        self.append("memory/INDEX.md", "\n[Indirect](projects/kisuul/kestrelgaming/INDEX.md)\n")
        self.assert_error("Scope index not registered")

    def test_project_index_needs_profile(self):
        self.write("memory/projects/example/new/INDEX.md", "# New project\n")
        self.append("memory/projects/INDEX.md", "\n[New](example/new/INDEX.md)\n")
        self.assert_error("Project index needs PROFILE.md")

    def test_valid_handoff_then_missing_outcome(self):
        name = self.handoff()
        self.assertEqual(validate(self.root), [])
        self.replace(name, "**Task outcome:** PARTIAL", "**Task outcome:** Maybe done")
        self.assert_error("Handoff needs an explicit Task outcome")

    def test_handoff_requires_one_outcome(self):
        name = self.handoff()
        self.replace(name, "**Task outcome:** PARTIAL", "**Task outcome:** PARTIAL / COMPLETE")
        self.assert_error("Handoff needs an explicit Task outcome")

    def test_supersession_requires_replacement_and_accepts_valid_link(self):
        self.replace(RECORD, "status: active", "status: superseded")
        self.assert_error("Superseded record needs a link")
        self.second_record()
        self.replace("memory/shared/second.md", "status: superseded", "status: active")
        self.append(RECORD, "\n## Superseded by\n\n[Replacement](second.md)\n")
        self.assertEqual(validate(self.root), [])

    def test_supersession_cycle(self):
        self.second_record()
        for name in [RECORD, "memory/shared/second.md"]:
            self.replace(name, "status: active", "status: superseded")
        self.append(RECORD, "\n## Superseded by\n\n[Next](second.md)\n")
        self.append("memory/shared/second.md", "\n## Superseded by\n\n[Previous](2026-11-02-central-memory.md)\n")
        self.assert_error("Supersession cycle")

    def test_duplicate_frontmatter_keys_and_nested_yaml_rejected(self):
        original = (self.root / RECORD).read_text()
        self.replace(RECORD, "schema: 1", "schema: 1\nschema: 1")
        self.assert_error("Duplicate frontmatter key")
        self.write(RECORD, original.replace("author: Codex", "author: [Codex]"))
        self.assert_error("Expected plain or double-quoted scalar")

    def test_unfilled_template_rejected(self):
        self.replace(RECORD, "author: Codex", "author: REPLACE_AUTHOR")
        self.assert_error("Unfilled template placeholder")

    def test_skill_name_must_match_folder(self):
        self.replace("skills/kestrel-recall/SKILL.md", "name: kestrel-recall", "name: other-name")
        self.assert_error("Invalid skill name or directory mismatch")

    def test_skill_must_be_indexed(self):
        self.write("skills/INDEX.md", "# Skills\n")
        self.assert_error("Skill not indexed")

    def test_invalid_utf8_reported_without_crash(self):
        (self.root / RECORD).write_bytes(b"\xff\xfe\xff")
        self.assert_error("Cannot read UTF-8 Markdown")

    def test_symlink_markdown_rejected(self):
        outside = Path(self.tmp.name) / "outside.md"
        outside.write_text("# Not part of repository\n")
        link = self.root / "docs/symlink.md"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable on this platform")
        self.assert_error("Symlinked Markdown is unsupported")


if __name__ == "__main__":
    unittest.main()
