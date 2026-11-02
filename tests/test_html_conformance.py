"""Contract tests for the Nu checker dispatch gate (not a substitute for vnu)."""
from pathlib import Path
from unittest import mock
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/kestrel-html-conformance/scripts"))
from check_html import collect_files, main  # noqa: E402


class HtmlGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def html(self, name="out/index.html"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("<!doctype html><title>Example</title>", encoding="utf-8")
        return path

    def test_collects_nested_html_and_xhtml_only(self):
        html = self.html()
        xhtml = self.html("out/sub/extra.xhtml")
        (self.root / "out" / "script.js").write_text("<html>")
        self.assertEqual(collect_files([self.root / "out"]), sorted([html.resolve(), xhtml.resolve()]))

    def test_empty_directory_fails_closed(self):
        self.assertEqual(main([str(self.root)]), 2)

    def test_missing_and_non_html_inputs_fail_closed(self):
        self.assertEqual(main([str(self.root / "no.html")]), 2)
        other = self.root / "style.css"
        other.write_text("p{}")
        self.assertEqual(main([str(other)]), 2)

    @mock.patch("check_html.subprocess.run")
    @mock.patch("check_html.shutil.which", return_value="/usr/bin/vnu")
    def test_pass_requires_successful_checker(self, which, run):
        path = self.html()
        run.return_value.returncode = 0
        self.assertEqual(main([str(path)]), 0)
        command = run.call_args.args[0]
        self.assertEqual(command[:2], ["/usr/bin/vnu", str(path.resolve())])
        self.assertEqual(command[-1], str(path.resolve()))
        self.assertNotIn("--exit-zero-always", command)

    @mock.patch("check_html.subprocess.run")
    @mock.patch("check_html.shutil.which", return_value="/usr/bin/vnu")
    def test_checker_error_fails(self, which, run):
        run.return_value.returncode = 1
        self.assertEqual(main([str(self.html())]), 1)

    @mock.patch("check_html.subprocess.run", side_effect=OSError("cannot start"))
    @mock.patch("check_html.shutil.which", return_value="/usr/bin/vnu")
    def test_checker_launch_failure_is_blocked(self, which, run):
        self.assertEqual(main([str(self.html())]), 2)

    @mock.patch("check_html.shutil.which", return_value=None)
    def test_missing_checker_is_blocked(self, which):
        self.assertEqual(main([str(self.html())]), 2)

    @mock.patch("check_html.subprocess.run")
    @mock.patch("check_html.shutil.which", return_value="/usr/bin/vnu")
    def test_strict_warnings_flag(self, which, run):
        run.return_value.returncode = 0
        self.assertEqual(main(["--warnings-as-errors", str(self.html())]), 0)
        self.assertIn("--Werror", run.call_args.args[0])

    def test_symlink_is_blocked_not_skipped(self):
        outside = self.html("outside.html")
        linked = self.root / "linked.html"
        try:
            linked.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Creating symlinks is not supported")
        self.assertEqual(main([str(linked)]), 2)
        self.assertEqual(main([str(self.root)]), 2)

    def test_invalid_jar_fails_closed(self):
        self.assertEqual(main(["--jar", str(self.root / "missing.jar"), str(self.html())]), 2)


if __name__ == "__main__":
    unittest.main()
