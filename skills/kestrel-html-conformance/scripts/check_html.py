#!/usr/bin/env python3
"""Fail-closed batch HTML validation using the upstream Nu Html Checker (vnu).

This wrapper does not implement an HTML validator. It invokes an explicitly
installed official vnu command or vnu.jar, and propagates any failure.
Requires Python 3.9+; for --jar, Java 17+ (per upstream).
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

HTML_EXTENSIONS = frozenset({".html", ".htm", ".xhtml", ".xht"})


def collect_files(inputs: list[Path]) -> list[Path]:
    """Enumerate actual HTML sources; refuse missing/non-HTML explicit inputs."""
    selected: set[Path] = set()
    for path in inputs:
        if path.is_symlink():
            raise ValueError(f"Symlinked input is not supported: {path}")
        if not path.exists():
            raise ValueError(f"Input does not exist: {path}")
        if path.is_file():
            if path.suffix.lower() not in HTML_EXTENSIONS:
                raise ValueError(f"Not an HTML file: {path}")
            selected.add(path.resolve())
        elif path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_symlink():
                    raise ValueError(f"Symlink in input tree is not supported: {candidate}")
                if candidate.is_file() and candidate.suffix.lower() in HTML_EXTENSIONS:
                    selected.add(candidate.resolve())
        else:
            raise ValueError(f"Not a regular file or directory: {path}")
    if not selected:
        raise ValueError("No HTML files found; validation cannot pass on an empty set")
    return sorted(selected)


def checker_command(vnu: str, jar: Path | None) -> list[str]:
    if jar is not None:
        if not jar.is_file():
            raise ValueError(f"Nu checker JAR not found: {jar}")
        java = shutil.which("java")
        if not java:
            raise ValueError("Java missing; a vnu.jar requires Java 17+")
        return [java, "-jar", str(jar.resolve())]
    executable = shutil.which(vnu)
    if not executable:
        raise ValueError(f"Nu checker executable not found: {vnu}")
    return [executable]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", type=Path, nargs="+", help="HTML files or directories to validate")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--vnu", default="vnu", help="Path/name of installed Nu CLI (default: vnu)")
    source.add_argument("--jar", type=Path, help="Path to official vnu.jar (Java 17+)")
    parser.add_argument("--warnings-as-errors", action="store_true", help="Make warnings fail the gate")
    args = parser.parse_args(argv)

    try:
        files = collect_files(args.paths)
        command = checker_command(args.vnu, args.jar)
    except (ValueError, OSError) as exc:
        print(f"HTML validation BLOCKED: {exc}", file=sys.stderr)
        return 2

    # Do NOT use --exit-zero-always, --filterfile, --filterpattern, or --no-langdetect.
    # Explicitly pass the enumerated HTML files, with no skip/filter flags.
    if args.warnings_as_errors:
        command.append("--Werror")
    command.extend(str(path) for path in files)
    print(f"Validating {len(files)} HTML file(s) with Nu Html Checker...", flush=True)
    try:
        completed = subprocess.run(command, check=False)
    except OSError as exc:
        print(f"HTML validation BLOCKED: checker could not start: {exc}", file=sys.stderr)
        return 2
    if completed.returncode != 0:
        print(f"HTML validation FAILED or INDETERMINATE: vnu exit {completed.returncode}", file=sys.stderr)
        return 1
    print(f"HTML validation PASSED: Nu checker returned success for {len(files)} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
