---
schema: 1
id: idiw-net-universal-discord-bot-profile
kind: profile
scope: project:idiw-net/universal_discord_bot
status: active
evidence: observed
author: claude-code-session-2026-11-18
created: 2026-11-18
updated: 2026-11-18
sources: "Inspected github.com/IDIW-NET/Universal_Discord_Bot (private) master at 61fdf41 on 2026-11-18: AGENTS.md, CONTRIBUTING.md, README.md, ROADMAP.md, CHANGELOG.md, pyproject.toml, .github/workflows/verify.yml, scripts/, tests/; executed checks listed in the 2026-11-18 type-gate handoff."
---

# IDIW-NET/Universal_Discord_Bot ("UDB")

## Summary

- **Repository and purpose:** UDB, the Universal Discord Bot. A modular,
  slash-command-first discord.py framework in Python 3.12. The runtime hosts
  modules and the modules do the work. Private repo in the `IDIW-NET` org;
  default branch `master`. The user calls it "UDB". (observed)
- **Access:** the `gh` CLI account `Kisuul` is a member of `IDIW-NET` and can
  read it. The public `cosmicdance-4-2-0` account cannot see it, so a 404 on
  `cosmicdance-4-2-0/...` means the wrong owner, not a missing repo. (observed)
- **Project-owned instructions (authoritative, read these first):**
  [AGENTS.md](https://github.com/IDIW-NET/Universal_Discord_Bot/blob/master/AGENTS.md),
  CONTRIBUTING.md (pre-PR checklist), ROADMAP.md (milestone scope is the
  contract), CHANGELOG.md (`Verification` blocks record commands actually run).
- **Workflow:** work arrives as GitHub issues titled "Codex handoff — <id>"
  (e.g. C2a, C2b, D1), implemented as one PR per work order and merged by the
  owner after review, often a hostile/independent audit. Version metadata
  stays at `0.4.6` while bounded 0.5.0 work merges as `[Unreleased]`. (observed)
- **Verification gate:** `pytest -q`, `ruff check .`, `ruff format --check .`,
  `mypy`, then `scripts/doctor.py`; `scripts/verify.py` runs the first four.
  CI (`.github/workflows/verify.yml`) runs all five on Python 3.12 without
  Discord secrets. No live-Discord tests by design. (observed)
- **Hard constraints:** stay inside the active work order; no casual
  dependencies; bump version mirrors in lockstep; `scripts/command_hygiene.py`
  can prune live Discord commands, so never run it without explicit operator
  intent. (observed from AGENTS.md)
- **Local setup that works on Windows:** `uv venv --python 3.12 .venv` then
  `uv pip install --python .venv\Scripts\python.exe -r requirements.txt`.
  The full suite takes about 6–7 minutes (1,650+ tests). (observed 2026-11-18)

## Evidence

Source inspection and executed checks at `61fdf41` on 2026-11-18, recorded in
[the type-gate handoff](handoffs/2026-11-18-type-gate-coverage-c7.md). The
claims about workflow conventions are inferred from issue and PR titles, not
stated by the owner.

## Revisit when

- Version metadata moves off `0.4.6`, or the 0.5.0 milestone closes.
- The mypy gate definition changes (`[tool.mypy] files` in `pyproject.toml`
  once the type-gate PR lands; `bot services modules` in CI before it).
- Org membership or repository visibility changes.
