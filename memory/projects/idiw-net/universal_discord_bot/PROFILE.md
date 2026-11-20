---
schema: 1
id: idiw-net-universal-discord-bot-profile
kind: profile
scope: project:idiw-net/universal_discord_bot
status: active
evidence: observed
author: claude-code-session-2026-11-18
created: 2026-11-18
updated: 2026-11-19
sources: "Inspected github.com/IDIW-NET/Universal_Discord_Bot (private) master at 61fdf41 on 2026-11-18: AGENTS.md, CONTRIBUTING.md, README.md, ROADMAP.md, CHANGELOG.md, pyproject.toml, .github/workflows/verify.yml, scripts/, tests/; executed checks listed in the 2026-11-18 type-gate handoff. Status and scheduler notes rechecked on master 39f02c2 (2026-11-19): AGENTS.md, ROADMAP.md, MODULES.md, docs/SCHEDULER_CONTRACT.md, pyproject.toml version, gh pr view 19/20, gh issue list. D2b notes from PR #21 (gh pr view 21: merged as 8e8e303, two GO reviews) and the checks in the D2b handoff."
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
  Work-order issues stay open after their PR merges (#11, #13, #15 and #18
  were all open on 2026-11-19), so judge status by PR state, not issue state.
  (observed)
- **Where merged status lives:** since PR #20 (`39f02c2`), ROADMAP.md's
  "Current implementation status (unreleased)" table and AGENTS.md list each
  merged 0.5.0 work order and what is still planned. Read those rather than
  rebuilding the list from memory. (observed)
- **Scheduler:** dispatch is handler-aware since D2a (PR #19, merged as
  `5336150`). Due jobs with no registered handler stay pending, consume no
  attempt and are counted as `unhandled_due` in `/health` and `/doctor`.
  [docs/SCHEDULER_CONTRACT.md](https://github.com/IDIW-NET/Universal_Discord_Bot/blob/master/docs/SCHEDULER_CONTRACT.md)
  is the project-owned contract. (observed; details in
  [the D2a handoff](handoffs/2026-11-19-d2a-safe-dispatch-d2a.md))
- **Retry and replay (D2b):**
  - PR #21 merged as `8e8e303` on 2026-11-20 UTC.
  - New Tickets inactivity jobs get three attempts. Rows stored earlier keep their own `max_attempts`.
  - A handler raises `services.scheduler.NonRetryableJobError` to fail a job terminally; other exceptions retry within the budget.
  - Tickets rejects malformed payloads, and envelope/payload guild mismatches, before touching the store.
  - Replays are safe because `flag_inactive()` is conditional and atomic.
  - D3 (offline automation conformance) is planned.
  - Follow-up gaps are filed as issues #22–#24 (D2c–D2e).
  - (observed; details in [the D2b handoff](handoffs/2026-11-19-d2b-recovery-safe-inactivity-d2b.md))
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
  On this Windows machine the full suite took about 10 minutes for 1,826
  tests on 2026-11-19; the whole CI job takes about 40 s on Linux. Run
  `pytest` on the touched files first. (observed)
- **Test hygiene:** close every `StorageService` a test opens, even on failure.
  Use an autouse fixture that closes leftovers. Otherwise the aiosqlite thread
  outlives its loop and pytest reports "Event loop is closed" as an ERROR in
  a later, unrelated test. (observed 2026-11-19)

## Evidence

Source inspection and executed checks at `61fdf41` on 2026-11-18, recorded in
[the type-gate handoff](handoffs/2026-11-18-type-gate-coverage-c7.md). The
claims about workflow conventions are inferred from issue and PR titles, not
stated by the owner. The merged-status, open-issue and scheduler notes were
rechecked on `master` at `39f02c2` on 2026-11-19 against the files and `gh`
queries named in `sources`. The D2b, test-runtime and test-hygiene notes come
from the D2b work and PR #21 (merged as `8e8e303`), recorded in its handoff.

## Revisit when

- Version metadata moves off `0.4.6`, or the 0.5.0 milestone closes.
- The mypy gate definition changes. Since PR #16 (merged 2026-11-19 at
  `6491be9`) it is plain `python -m mypy` over `[tool.mypy] files` in
  `pyproject.toml`, guarded by `tests/test_type_check_coverage.py`. Older
  CHANGELOG entries and issues still cite `mypy bot services modules`.
- D2c, D2d, D2e or D3 merges, or the scheduler contract changes.
- Org membership or repository visibility changes.
