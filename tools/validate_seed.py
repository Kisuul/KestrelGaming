#!/usr/bin/env python3
"""Read-only Kestrel contract, Markdown-link, memory-record, and skill checks.

Python 3.9+, standard library only. This checks structure, not factual accuracy,
external URLs, heading anchors, host behavior, secrets, or authorization.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

REQUIRED = (
    "README.md", "AGENTS.md", "KESTREL.md", "CONTRIBUTING.md",
    "kestrel/PROJECT_PROFILE.md", "kestrel/PERMISSIONS.md",
    "kestrel/VERIFICATION.md", "kestrel/STATE_PROTOCOL.md",
    "kestrel/MEMORY_PROTOCOL.md", "kestrel/evals/SCENARIOS.md",
    "kestrel/evals/SCORECARD.md", "kestrel/templates/MEMORY.md",
    "kestrel/templates/PROJECT.md", "kestrel/templates/HANDOFF.md",
    "docs/INTEGRATION.md", "docs/PROJECT_POINTER.md", "docs/PROVENANCE.md",
    "docs/DESIGN_NOTES.md", "memory/INDEX.md", "memory/shared/INDEX.md",
    "memory/projects/INDEX.md", "memory/agents/INDEX.md", "skills/INDEX.md",
    "skills/kestrel-recall/SKILL.md", "skills/kestrel-remember/SKILL.md",
)
FIELDS = {"schema", "id", "kind", "scope", "status", "evidence", "author",
          "created", "updated", "sources"}
ENUMS = {
    "kind": {"fact", "lesson", "decision", "profile", "handoff"},
    "status": {"draft", "active", "superseded", "archived"},
    "evidence": {"observed", "inferred", "hypothesis", "user-stated", "unverified"},
}
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
COMPONENT = re.compile(r"[a-z0-9][a-z0-9._-]*")
LINK = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")


def prose(text: str) -> str:
    """Remove fenced examples and inline code from the supported Markdown subset."""
    output = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
        elif marker:
            fence = marker[1]
        else:
            output.append(line)
    return re.sub(r"(`+).*?\1", "", "\n".join(output))


def frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse the documented flat scalar subset, never arbitrary YAML objects."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("Missing frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise ValueError("Unclosed frontmatter") from None
    data = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        value = value.strip()
        if not sep or not re.fullmatch(r"[a-z][a-z0-9_-]*", key):
            raise ValueError("Expected flat key: value frontmatter")
        if key in data:
            raise ValueError(f"Duplicate frontmatter key: {key}")
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except ValueError:
                raise ValueError(f"Invalid quoted scalar: {key}") from None
        elif not value or value[0] in "[{'&*!|>" or ": " in value or " #" in value:
            raise ValueError(f"Expected plain or double-quoted scalar: {key}")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Empty/non-string scalar: {key}")
        data[key] = value
    return data, "\n".join(lines[end + 1:])


def section(body: str, heading: str) -> str:
    match = re.search(r"^## " + re.escape(heading) + r"[ \t]*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
    return match[1].strip() if match else ""


def targets(source: Path, text: str, root: Path, errors: list[str]) -> set[Path]:
    found = set()
    for link in LINK.findall(prose(text)):
        target = re.sub(r'\s+"[^\"]*"$', "", link.strip()).strip("<>")
        try:
            parsed = urlsplit(target)
        except ValueError:
            errors.append(f"Malformed link: {source.relative_to(root)} -> {link}")
            continue
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        resolved = (source.parent / unquote(parsed.path)).resolve()
        if not resolved.is_relative_to(root):
            errors.append(f"Link escapes root: {source.relative_to(root)} -> {link}")
        elif not resolved.exists():
            errors.append(f"Broken relative link: {source.relative_to(root)} -> {link}")
        else:
            found.add(resolved)
    return found


def scope_for(path: Path, root: Path) -> tuple[str, Path]:
    parts = path.relative_to(root).parts
    if parts[:2] == ("memory", "shared") and len(parts) >= 3:
        return "shared", root / "memory/shared/INDEX.md"
    if parts[:2] == ("memory", "projects") and len(parts) >= 5:
        owner, repo = parts[2:4]
        if COMPONENT.fullmatch(owner) and COMPONENT.fullmatch(repo):
            return f"project:{owner}/{repo}", root.joinpath(*parts[:4], "INDEX.md")
    if parts[:2] == ("memory", "agents") and len(parts) >= 4 and SLUG.fullmatch(parts[2]):
        return f"agent:{parts[2]}", root.joinpath(*parts[:3], "INDEX.md")
    raise ValueError("Invalid memory scope path")


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for name in REQUIRED:
        if not (root / name).is_file():
            errors.append(f"Missing required file: {name}")

    texts, links = {}, {}
    for source in sorted(root.rglob("*.md")):
        parts = source.relative_to(root).parts
        if any(p.startswith(".") and p != ".github" for p in parts):
            continue
        if source.is_symlink() or not source.resolve().is_relative_to(root):
            errors.append(f"Symlinked Markdown is unsupported: {source.relative_to(root)}")
            continue
        try:
            texts[source] = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"Cannot read UTF-8 Markdown: {source.relative_to(root)} ({type(exc).__name__})")
            continue
        links[source] = targets(source, texts[source], root, errors)

    ids, replacements = {}, {}
    records = {p for p in texts if p.is_relative_to(root / "memory") and p.name != "INDEX.md"}
    for path in sorted(records):
        label = str(path.relative_to(root))
        try:
            data, body = frontmatter(texts[path])
            if set(data) != FIELDS:
                raise ValueError(f"Record fields differ: missing={sorted(FIELDS - set(data))}, extra={sorted(set(data) - FIELDS)}")
            if data["schema"] != "1":
                raise ValueError("Unsupported schema version")
            if not SLUG.fullmatch(data["id"]):
                raise ValueError("Invalid record ID")
            if data["id"] in ids:
                raise ValueError(f"Duplicate record ID: {data['id']}")
            ids[data["id"]] = path
            if re.search(r"REPLACE_|replace-(?:record|project|handoff)-id|YYYY-MM-DD", texts[path]):
                raise ValueError("Unfilled template placeholder")
            for field, allowed in ENUMS.items():
                if data[field] not in allowed:
                    raise ValueError(f"Invalid {field}: {data[field]}")
            for field in ("created", "updated"):
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data[field]):
                    raise ValueError(f"Invalid ISO date: {field}")
                date.fromisoformat(data[field])
            if data["updated"] < data["created"]:
                raise ValueError("Updated date precedes created date")
            expected, index = scope_for(path, root)
            if data["scope"] != expected:
                raise ValueError(f"Scope/path mismatch: expected {expected}")
            if path not in links.get(index, set()):
                raise ValueError(f"Record not indexed by {index.relative_to(root)}")
            for heading in ("Summary", "Evidence", "Revisit when"):
                if not section(prose(body), heading):
                    raise ValueError(f"Missing or empty section: {heading}")
            if data["kind"] == "handoff":
                if not expected.startswith("project:") or not section(body, "Next action"):
                    raise ValueError("Handoff needs project scope and Next action")
                if not re.search(r"^\*\*Task outcome:\*\*[ \t]*(IN PROGRESS|PARTIAL|BLOCKED|COMPLETE)[ \t]*$", body, re.M):
                    raise ValueError("Handoff needs an explicit Task outcome")
            if data["status"] == "superseded":
                replacement = targets(path, section(body, "Superseded by"), root, errors) & records
                if not replacement or path in replacement:
                    raise ValueError("Superseded record needs a link to another memory record")
                replacements[path] = replacement
        except ValueError as exc:
            errors.append(f"{label}: {exc}")

    # Detect cycles so a supersession chain cannot loop forever during recall.
    def visit(path: Path, active: set[Path], done: set[Path]) -> None:
        if path in active:
            errors.append(f"Supersession cycle: {path.relative_to(root)}")
            return
        if path in done:
            return
        for following in replacements.get(path, set()):
            visit(following, active | {path}, done)
        done.add(path)

    done: set[Path] = set()
    for path in replacements:
        visit(path, set(), done)

    # Every memory record/index must be discoverable from the memory entrypoint.
    reachable, pending = set(), [root / "memory/INDEX.md"]
    while pending:
        path = pending.pop()
        if path not in reachable:
            reachable.add(path)
            pending.extend(links.get(path, set()) - reachable)
    for path in sorted(texts):
        if path.is_relative_to(root / "memory") and path not in reachable:
            errors.append(f"Unreachable memory file: {path.relative_to(root)}")
        if path.match("memory/projects/*/*/INDEX.md") and not (path.parent / "PROFILE.md").is_file():
            errors.append(f"Project index needs PROFILE.md: {path.relative_to(root)}")
        for pattern, catalog in (("memory/projects/*/*/INDEX.md", "memory/projects/INDEX.md"),
                                 ("memory/agents/*/INDEX.md", "memory/agents/INDEX.md")):
            if path.match(pattern) and path not in links.get(root / catalog, set()):
                errors.append(f"Scope index not registered in {catalog}: {path.relative_to(root)}")
        if path.is_relative_to(root / "skills") and path.name == "SKILL.md":
            try:
                data, body = frontmatter(texts[path])
                if set(data) != {"name", "description"}:
                    raise ValueError("Skill needs name and description only")
                if not SLUG.fullmatch(data["name"]) or len(data["name"]) > 64 or data["name"] != path.parent.name:
                    raise ValueError("Invalid skill name or directory mismatch")
                if not body.strip() or "TODO" in texts[path]:
                    raise ValueError("Empty or unfinished skill")
                if path not in links.get(root / "skills/INDEX.md", set()):
                    raise ValueError("Skill not indexed")
            except ValueError as exc:
                errors.append(f"{path.relative_to(root)}: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    errors = validate(parser.parse_args().root)
    if errors:
        for message in errors:
            print("ERROR:", message)
        return 1
    print("Kestrel structural checks passed (files, local links, memory records, skills).")
    print("This does not validate memory truth, agent behavior, permissions, or external sources.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
