---
schema: 1
id: idiw-net-universal-discord-bot-profile
kind: profile
scope: project:idiw-net/universal_discord_bot
status: active
evidence: observed
author: claude-code-session-2026-11-18
created: 2026-11-18
updated: 2026-11-24
sources: "Inspected github.com/IDIW-NET/Universal_Discord_Bot (private) master at 61fdf41 on 2026-11-18: AGENTS.md, CONTRIBUTING.md, README.md, ROADMAP.md, CHANGELOG.md, pyproject.toml, .github/workflows/verify.yml, scripts/, tests/; executed checks listed in the 2026-11-18 type-gate handoff. Status and scheduler notes rechecked on master 39f02c2 (2026-11-19): AGENTS.md, ROADMAP.md, MODULES.md, docs/SCHEDULER_CONTRACT.md, pyproject.toml version, gh pr view 19/20, gh issue list. D2b notes from PR #21 (gh pr view 21: merged as 8e8e303, two GO reviews) and the checks in the D2b handoff. D3 notes from PR #29 (gh pr view 29: merged as 5681471 on 2026-11-23), source read at 5c6584e (tests/test_capability_lifecycle.py, tests/test_intake_ticket_flow.py, services/scheduler.py, services/diagnostics.py, modules/tickets/store.py) and the checks in the D3 handoff. R1 notes from PR #31 (gh pr view 31: merged as 23cbdbd on 2026-11-24) and the R1 handoff; R2 notes from local commits 412100f and 7ce915b and the R2 handoff."
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
  - Follow-up gaps were filed as issues #22–#24 (D2c–D2e).
  - (observed; details in [the D2b handoff](handoffs/2026-11-19-d2b-recovery-safe-inactivity-d2b.md))
- **Offline conformance (D3):** PR #29 merged as `5681471` on 2026-11-23,
  tests and docs only, no production defect.
  `tests/test_automation_conformance.py` runs the merged 0.5.0 pieces together
  through real offline `UDBBot` restarts; `docs/D3_AUTOMATION_CONFORMANCE.md`
  maps its evidence and limits. The next steps are a status-reconcile docs PR
  and a separate 0.5.0 release-readiness gate. (observed; details in
  [the D3 handoff](handoffs/2026-11-20-d3-automation-conformance-d3.md))
- **Test-helper substitutions to disclose when citing tests as evidence**
  (observed at `5c6584e`):
  - `_bot()` in `tests/test_capability_lifecycle.py` hand-builds the
    `AppContext` (not `bot/main.py`), disables audit, uses manual sync and sets
    the scheduler's `shutdown_timeout_seconds=0.01` (production: 10 s).
  - `preview()` in `tests/test_intake_ticket_flow.py` calls the
    `/intake ticket` callback without `_check_can_run`.
  - Calling `command.callback` directly skips discord.py argument
    transformation and `UDBCommandTree.on_error`.
  - `/doctor`'s `scheduler.jobs` item gives `unhandled_due` precedence over
    recent failures, and counts "recent" against the real clock, so failures
    stamped with an injected tick time can read as old.
- **Release-gate candidates (from the D3 second audit, not defects):**
  nothing deletes `scheduler_jobs` rows and every ticket activity adds an
  inactivity job (observed); a hung audit call holds the sequential scheduler
  loop until shutdown (observed); `flag_inactive()` compares ISO timestamps as
  text, so upgraded 0.4.6 rows in another format could compare wrongly
  (hypothesis, refuted by R1 for rows 0.4.6 writes).
- **R1 upgrade conformance:** PR #31 merged as `23cbdbd` on 2026-11-24.
  0.4.6 databases upgrade cleanly; only `tickets_0002` is new. 0.4.6 writes
  canonical UTC timestamps. Noncanonical forms are a low defensive defect,
  R1-D1, kept as 4 strict `xfail`s. Fixtures are SQL dumps written by the
  0.4.6 runtime and rebuilt by `tests/upgrade_fixtures/build_udb_0_4_6.py`.
  (observed; details in
  [the R1 handoff](handoffs/2026-11-24-r1-upgrade-conformance-r1.md))
- **R2 scheduler risks:** local branch `test/0.5.0-r2-scheduler-risk-conformance`
  at the time of writing. History costs about 360 bytes per `scheduler_jobs`
  row and hot queries read `scheduler_jobs_status_run_idx`. A non-returning
  handler holds the loop while `/doctor` stays OK, and `stop()` lets the rest
  of an in-progress batch run inside its timeout. The recommendation is
  ACCEPT plus DEFER, with no HOLD. (observed; details in
  [the R2 handoff](handoffs/2026-11-24-r2-scheduler-risk-r2.md))
- **Timing lesson for tests:** stored UDB timestamps have one-second
  resolution, so fast Linux CI can put two startups in the same second.
  Never require `set_at` or similar values to change between operations.
  Also clear `caplog` between startups in one test: earlier modules leave
  INFO logging on. (observed in R1 CI)
- **Reviews:** PR #29 was opened, audited twice and merged from the same
  `Kisuul` account, so its audit reviews are COMMENTED, not approvals, and
  GitHub cannot show their independence (observed). Agents posting audits via
  `gh` as `Kisuul` on a `Kisuul` PR can only comment (inferred from GitHub's
  own-PR rule).
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
  On this Windows machine the full suite took about 5–7 minutes for 1,922
  tests on 2026-11-20 to 2026-11-23 (10 minutes for 1,826 on 2026-11-19);
  the whole CI job took about 40 s on Linux on 2026-11-19. Run `pytest` on
  the touched files first. (observed)
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
The D3, test-helper, release-gate and review notes come from the D3 work, its
second audit and PR #29 (merged as `5681471`), recorded in
[the D3 handoff](handoffs/2026-11-20-d3-automation-conformance-d3.md); the
test-helper and release-gate notes were read from source at `5c6584e`.

## Revisit when

- Version metadata moves off `0.4.6`, or the 0.5.0 milestone closes.
- The mypy gate definition changes. Since PR #16 (merged 2026-11-19 at
  `6491be9`) it is plain `python -m mypy` over `[tool.mypy] files` in
  `pyproject.toml`, guarded by `tests/test_type_check_coverage.py`. Older
  CHANGELOG entries and issues still cite `mypy bot services modules`.
- The scheduler contract changes, the test helpers named above change, or
  the 0.5.0 release-readiness gate starts.
- Org membership or repository visibility changes.
