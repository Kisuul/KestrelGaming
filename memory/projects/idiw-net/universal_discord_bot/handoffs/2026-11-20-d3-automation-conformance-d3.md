---
schema: 1
id: 2026-11-20-udb-d3-automation-conformance-d3
kind: handoff
scope: project:idiw-net/universal_discord_bot
status: active
evidence: observed
author: claude-code-session-2026-11-20
created: 2026-11-20
updated: 2026-11-20
sources: "Work order UDB-D3 (pasted by the user in the session). Draft PR #29, branch test/0.5.0-d3-automation-conformance: fc665b2 (tests) and 5c6584e (docs) on master a58a67e. Checks run locally on CPython 3.12.11, SQLite 3.49.1, discord.py 2.7.1, mypy 1.20.2; GitHub Actions run 44873097786."
---

# UDB D3: offline workflow and automation conformance

## Summary

**Goal and acceptance criteria:** work order UDB-D3 is a conformance task,
not a feature task. It proves that the merged 0.5.0 pieces (A/B, C1, C2a,
C2b, D0/D1, D2a–D2e) hold their contracts when used together, through real
offline `UDBBot` startup, restart and SQLite state. It covers eight areas,
D3-01 to D3-08:

- direct ticket creation;
- a consented Intake ticket;
- restart and replay;
- the activity timeline;
- disabled-module preservation;
- interruption and replay;
- rollback when the flag event is rejected;
- mixed defective and valid jobs.

It may change only tests and docs. A defect would mean HOLD plus a separate
corrective work order.

**Task outcome:** COMPLETE

This covers this session's scope. Draft PR #29 is open, but the independent
hostile audit and the owner's merge decision are still pending.

**Authorized scope and boundaries (historical; recheck on resume):**

- **Allowed:** new tests, minimal test-helper changes, a conformance report,
  and `[Unreleased]` CHANGELOG and ROADMAP lines.
- **Excluded:** production changes, schema, migrations, dependencies, version
  bumps, live smoke tests, merging, and marking D3 merged or accepted.

**Target repository, branch, and commit:** `IDIW-NET/Universal_Discord_Bot`,
branch `test/0.5.0-d3-automation-conformance`. Base is `a58a67e`, which matched
the verified base, so there were no intervening changes. Commits:

- `fc665b2`: tests, the tested head;
- `5c6584e`: docs only, the final head.

Pushed, with [PR #29](https://github.com/IDIW-NET/Universal_Discord_Bot/pull/29) open as a draft.

**Memory revision loaded:** KestrelGaming `main` at `8331a4d`: the UDB
PROFILE and the D2b handoff.

## Evidence

**Confirmed observations with sources:**

- **What D3 delivered:**
  - `tests/test_automation_conformance.py`: 9 tests. They reuse
    `_bot`/`_assert_clean`/`startup_spies` from `test_capability_lifecycle.py`,
    and `OfflineInteraction`/`preview`/`click` from `test_intake_ticket_flow.py`.
  - `docs/D3_AUTOMATION_CONFORMANCE.md`, the evidence matrix.
- **No production defect found.** Every D3 scenario passed on unchanged code at
  `a58a67e`.
- **Controlled-clock technique.** Patch `datetime` in `modules.tickets.store`
  and `modules.tickets.inactivity` only, starting 30 days in the past.
  - This lets the commands stamp day 0 and day 3, and still leaves day-0 jobs
    overdue for the real scheduler loop and the live `/doctor`.
  - It works across restarts because extension unload drops only
    `modules.tickets.cog` from `sys.modules`. The store and inactivity modules
    stay cached.
- **Running the real scheduler loop offline.** It never ticks by itself,
  because it waits in `bot.wait_until_ready()`.
  - Patching that method on the instance with an `asyncio.Event` gate lets the
    started loop run its first tick.
  - `UDBBot.close()` then cancels a stalled tick through `scheduler.stop()`'s
    timeout. That is the real shutdown path.
- **Proving that the UPDATE ran before the INSERT.** A `TEMP` trigger whose
  `WHEN` requires `(SELECT inactivity_flagged_at ...) IS NOT NULL` rejects the
  flag-event INSERT only after the conditional UPDATE is visible in the same
  transaction. The rejection itself therefore proves the UPDATE ran, and the
  unchanged row proves it rolled back.
- **Sensitivity check.** Eight source mutations were applied one at a time in
  a scratch worktree at the base, and each made its D3 test fail.
  - On Windows, read and write files as bytes in such scripts, because
    `Path.write_text` rewrites line endings.
- **Gate runtime.** The full suite now runs 1922 tests in about 6 minutes on
  this machine, down from the roughly 10 minutes recorded at D2b.

**Hypotheses and assumptions:** none affecting the result. Whether the
controlled-clock and readiness-gate substitutions are acceptable is for the
audit to decide; the report and PR list them.

**Decisions and rationale:**

- **Commit split.** The tests are one commit and the docs another, so the
  report can name a tested head. The gate re-ran on the final head.
- **Commit hygiene.** The tests commit was amended once before any push, to
  add the D3-05 no-write assertion and a permanent pending-task check
  (`_assert_shut_down`).
- **Status docs.** ROADMAP describes D3 without a "merged" row. AGENTS.md and
  README are untouched and are left for a post-merge reconcile PR, matching
  #20 and #28.
- **Review requests.** No GitHub reviewers were requested, because the work
  order named none. The PR body asks for the hostile audit.

**Changed files and uncommitted state to preserve:** UDB: none uncommitted.
This record lives on the KestrelGaming branch
`memory/udb-d3-automation-conformance-2026-11-20`.

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| Full gate in a clean worktree at `fc665b2` | pytest 1922 passed; ruff check and format clean (244 files); mypy clean (127 files); doctor OK (13 checks) | Windows, CPython 3.12.11 |
| Same gate at the final head `5c6584e` | Identical results; tree clean afterwards | Same |
| 8 source mutations at `a58a67e` | 8 of 8 detected | Scratch worktree, since removed |
| D3 tests with non-loopback connects and DNS refused | 9 passed, 0 attempts; 14 shutdowns with no pending task, no stray thread | Probe script in scratchpad |
| GitHub Actions on PR #29, run 44873097786 | Verify passed (`success`) on `5c6584e` | ubuntu-latest, Python 3.12 |

**Persistence:**

- **UDB:** pushed, with PR #29 open as a draft.
- **This handoff:** pushed, with the user's approval, to the KestrelGaming
  branch `memory/udb-d3-automation-conformance-2026-11-20` for review. Its Git
  history shows whether it has been integrated into `main`.

## Next action

**Open blockers or risks:**

- **Audit outcome:** the hostile audit has not happened yet.
- **Accepted by design, not defects:**
  - superseded inactivity checks pile up as no-ops;
  - a flag audit lost before completion is not recreated.

**Next useful step:**

1. Answer the audit findings on PR #29. A real defect gets its own corrective
   work order; D3 goes on HOLD and its tests are not weakened.
2. After merge, open a status-reconcile docs PR for the ROADMAP table,
   `AGENTS.md`, `README.md` and the report's "Status when written" line.
3. Then the separate 0.5.0 release-readiness gate:
   - upgrade from 0.4.6 databases;
   - operator procedures;
   - explicitly authorized dev-guild testing;
   - the lockstep version bump.

## Revisit when

PR #29 is audited, changed or merged, or the release-readiness gate starts. On
resume, compare `master` and the PR head with this record before relying on it.
