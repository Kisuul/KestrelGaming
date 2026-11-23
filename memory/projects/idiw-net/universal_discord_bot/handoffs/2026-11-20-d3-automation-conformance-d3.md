---
schema: 1
id: 2026-11-20-udb-d3-automation-conformance-d3
kind: handoff
scope: project:idiw-net/universal_discord_bot
status: archived
evidence: observed
author: claude-code-session-2026-11-20
created: 2026-11-20
updated: 2026-11-23
sources: "Work order UDB-D3 (pasted by the user on 2026-11-20). PR #29, branch test/0.5.0-d3-automation-conformance: fc665b2 (tests) and 5c6584e (docs) on master a58a67e; second-audit revision d68884f (tests) and 8cfe8e8 (docs); merged as 5681471 at 2026-11-23T22:50Z (gh pr view 29). First audit: PR review at 5c6584e (GO). Second audit: PR review 6029972436 at 5c6584e (claude-code-session-2026-11-23, read-only). Checks run locally on CPython 3.12.11, SQLite 3.49.1, discord.py 2.7.1, mypy 1.20.2; GitHub Actions runs 44873097786 (5c6584e) and 45281636235 (8cfe8e8)."
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

PR #29 merged as `5681471` on 2026-11-23 after two audits and one test/doc
revision. No production defect was found. Archived on merge: its lessons are in
the [project profile](../PROFILE.md).

**Authorized scope and boundaries (historical; recheck on resume):**

- **Allowed:** new tests, minimal test-helper changes, a conformance report,
  and `[Unreleased]` CHANGELOG and ROADMAP lines.
- **Excluded:** production changes, schema, migrations, dependencies, version
  bumps, live smoke tests, merging, and marking D3 merged or accepted.
- The second audit was requested read-only. The revision, its push and the PR
  description update were each separately approved by the user.

**Target repository, branch, and commit:** `IDIW-NET/Universal_Discord_Bot`,
branch `test/0.5.0-d3-automation-conformance`, base `a58a67e`. Commits:

- `fc665b2`: tests, the originally tested head;
- `5c6584e`: docs only;
- `d68884f`: second-audit test revision;
- `8cfe8e8`: second-audit docs revision, the final head;
- merge `5681471` on `master`.

**Memory revision loaded:** KestrelGaming `main` at `8331a4d` (2026-11-20) and
`d7949c3` (2026-11-23).

## Evidence

**Confirmed observations with sources:**

- **What D3 delivered:**
  - `tests/test_automation_conformance.py`: 9 tests. They reuse
    `_bot`/`_assert_clean`/`startup_spies` from `test_capability_lifecycle.py`,
    and `OfflineInteraction`/`click`/`interaction_for` from
    `test_intake_ticket_flow.py`.
  - `docs/D3_AUTOMATION_CONFORMANCE.md`, the evidence matrix, with a
    "Revision after the second audit" section.
- **No production defect found.** Every D3 scenario passed on unchanged code at
  `a58a67e`, and again after the revision.
- **Controlled-clock technique.** Patch `datetime` in `modules.tickets.store`
  and `modules.tickets.inactivity` only, starting 30 days in the past.
  - Those are the only Tickets files that read the clock (grep at `5c6584e`).
  - It works across restarts because extension unload drops only
    `modules.tickets.cog` from `sys.modules`.
- **Running the real scheduler loop offline.** Patch `wait_until_ready` on the
  instance with an `asyncio.Event` gate so the started loop runs a tick.
  `UDBBot.close()` then cancels a stalled tick through `scheduler.stop()`.
- **Proving that the UPDATE ran before the INSERT.** A `TEMP` trigger whose
  `WHEN` requires the flag to be set rejects the flag-event INSERT only after
  the conditional UPDATE is visible in the same transaction.
- **Second audit (2026-11-23, read-only, review 6029972436).** No production
  defect, nothing merge-blocking. It found:
  - an undisclosed substitution: `_bot()` builds `SchedulerService` with
    `shutdown_timeout_seconds=0.01`, against the production 10 s. The first
    audit's note that D3-06 "waits for the real scheduler stop timeout" was
    wrong;
  - the claim "commands run their checks" failed for `/intake ticket`: the
    shared `preview()` helper calls `command.callback` without
    `_check_can_run`;
  - weak oracles: D3-05's `"unavailable"` also matched
    `Submission unavailable`; D3-08's doctor WARNING came only from
    `unhandled_due`, because `recent=0` was an artifact of injected tick times;
  - disclosure gaps (hand-built `AppContext`, re-implemented audit selection,
    bypassed argument transformation and `on_error`, private discord.py hooks)
    and missing positive log-capture controls.
- **Revision (`d68884f`, `8cfe8e8`).** D3 drives `/intake ticket` through
  `_command()`; exact reasons are asserted; positive log controls were added;
  every substitution is disclosed in the module, report and PR description.
- **Sensitivity.** Eight source mutations at `a58a67e` were each detected.
  Two more for the revision (absent provider reported as
  `Submission unavailable`; a `/intake ticket` check that denies everyone) were
  passed by the original module and caught by the revised one.

**Hypotheses and assumptions:** `flag_inactive()` compares ISO timestamps as
text (`last_activity_at <= ?`). Upgraded 0.4.6 rows in another format would
compare wrongly. Not verified: the 0.4.6 format was not checked (no tags).

**Decisions and rationale:**

- **Commit split.** Tests and docs in separate commits, so the report can name
  a tested head; repeated for the revision.
- **Limitation pin kept.** D3-06 still asserts the lost audit is `[]`, labelled
  as a pin rather than a requirement, instead of weakening it to "at most one".
- **Report names no revision hashes.** It defers to the PR description, so the
  report stayed accurate after committing.

**Changed files and uncommitted state to preserve:** none. Everything is
merged on UDB `master` at `5681471`.

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| Full gate at `fc665b2` and at `5c6584e` | pytest 1922 passed; ruff check and format clean (244 files); mypy clean (127 files); doctor OK (13 checks) | Windows, CPython 3.12.11 |
| 8 source mutations at `a58a67e` | 8 of 8 detected | Scratch worktree, since removed |
| D3 tests with non-loopback connects and DNS refused | 9 passed, 0 attempts; 14 shutdowns with no pending task | Probe script in scratchpad |
| Second audit: D3 module at `5c6584e` | 9 passed in 18.94 s | Read-only; full gate not re-run |
| Full gate on the revised tree (tests as in `d68884f`) | 1922 passed in 292 s; ruff, format, mypy clean; doctor OK | Same machine |
| After the final doc edits | docs invariants, doctor-script and D3 tests: 49 passed; doctor OK; `git diff --check` clean | Same machine |
| 2 revision mutations at `5c6584e` | Original module passed both; revised module caught both | Scratch worktree, since removed |
| GitHub Actions Verify | success on `5c6584e` (44873097786) and `8cfe8e8` (45281636235) | ubuntu-latest, Python 3.12 |

**Persistence:** UDB work merged on `master` at `5681471`. This record is
updated on the KestrelGaming branch `memory/udb-d3-merged-2026-11-23`; its Git
history shows whether it reached `main`.

## Next action

**Open blockers or risks:** none for D3. Accepted by design, not defects:
superseded inactivity checks pile up as no-ops, and a flag audit lost before
completion is not recreated.

**Next useful step:**

1. A status-reconcile docs PR: the ROADMAP status table, `AGENTS.md`,
   `README.md`, and the report's "Status when written" line (still "proposed").
2. The separate 0.5.0 release-readiness gate:
   - upgrade from 0.4.6 databases, including the timestamp-format hypothesis
     above;
   - `scheduler_jobs` retention (nothing deletes rows; each ticket activity
     adds a job);
   - an operator note that a hung audit call holds the sequential scheduler
     loop until shutdown;
   - operator procedures, explicitly authorized dev-guild testing, and the
     lockstep version bump.

## Revisit when

The status-reconcile PR or the release-readiness gate starts. Compare `master`
with this record before relying on it.
