---
schema: 1
id: 2026-11-24-udb-r2-scheduler-risk-r2
kind: handoff
scope: project:idiw-net/universal_discord_bot
status: active
evidence: observed
author: claude-code-session-2026-11-24
created: 2026-11-24
updated: 2026-11-24
sources: "Work order UDB-R2 (pasted by the user on 2026-11-24). UDB master 23cbdbd (merge of PR #31), read locally: services/scheduler.py, services/storage.py, services/audit.py, services/diagnostics.py, modules/tickets/store.py, modules/tickets/inactivity.py, docs/SCHEDULER_CONTRACT.md, OPERATOR_GUIDE.md. Local branch test/0.5.0-r2-scheduler-risk-conformance, commits 412100f (tests and helper) and 7ce915b (docs). Checks run on Windows 10, CPython 3.12.11, SQLite 3.49.1; results in the table below."
---

# UDB R2: scheduler retention and stalled-handler risks

## Summary

**Goal and acceptance criteria:** work order UDB-R2 asks for measurements and
characterizations, with a disposition (ACCEPT, DEFER or HOLD) for two risks:

- **R2-A:** terminal `scheduler_jobs` rows accumulate.
- **R2-B:** one handler that does not return blocks the sequential
  dispatcher.

Eight areas, R2-01 to R2-08, each PASS, FAIL or BLOCKED. Tests, measurement
code and docs only; no deletion, timeouts or concurrency.

**Task outcome:** IN PROGRESS

All eight areas PASS locally. The recommendation is ACCEPT plus DEFER for both
risks, with no HOLD. Nothing has been pushed and no PR has been opened.

**Authorized scope and boundaries (historical; recheck on resume):**

- **Allowed:** tests, measurement code, engineering docs, and one CHANGELOG
  line.
- **Excluded:** production scheduler changes, retention, timeouts,
  concurrency, schema, dependencies, retry budgets, version, deployment and
  release.
- **Remote writes:** a draft PR only with the user's approval for this work
  order. The R1 approval does not carry over.

**Target repository, branch, and commit:** `IDIW-NET/Universal_Discord_Bot`,
local branch `test/0.5.0-r2-scheduler-risk-conformance` from `23cbdbd`.
Commits `412100f` (tests and helper, the tested head) and `7ce915b` (docs).

**Memory revision loaded:** KestrelGaming `main` at `e43f0aa`, plus the
unmerged R1 memory branch, on which this branch is stacked.

## Evidence

**Confirmed observations with sources:**

- **Retention.** Nothing deletes terminal rows, and the transition APIs
  refuse them. Tickets adds one row per activity that leaves the ticket
  active: resolve, close, export and staff notes on resolved or closed
  tickets add none.
- **Query plans.** All hot queries use `scheduler_jobs_status_run_idx`;
  `recent_failed_count` visits every failed row.
- **Measured.** History costs about 360 bytes per row (35 MB at 100,000
  rows). Idle ticks (about 0.7 ms), a 25-job batch (about 0.1 s) and restart
  (about 11 ms) stay flat up to 100,000 rows. The diagnostic snapshot grows
  only with failed and pending rows: 22 ms with 3,000 failed and 3 ms with
  30. An external `BEGIN IMMEDIATE` makes a UDB write fail after 5.03 s
  (default busy timeout).
- **Stall.** One non-returning handler holds the batch and every later tick.
  `/health` and `/doctor` stay OK: `last_tick` freezes and `oldest_due`
  grows, but neither warns, and no running count exists. A handler that
  stalls inside `storage.transaction()` blocks all storage access.
- **Shutdown.** `stop()` sets the event and waits for the whole in-progress
  batch, up to the timeout. Jobs queued behind a stall that ends inside the
  window still run during shutdown.
- **Recovery.** A cancelled handler's row stays `running`. Recovery follows
  the stored budget, and the Tickets replay is a no-op. A lost audit is not
  recreated.
- **Doc inaccuracy.** The D2a contract says jobs "whose handler never returns
  stay pending and visible in diagnostics". A hung handler's row is in fact
  `running`, and diagnostics do not count it.

**Decisions and rationale:**

- **Bounded windows.** "Did not happen" claims use explicit bounded windows.
  A planted 0.2 s per-handler timeout first escaped the basic stall test and
  the Tickets audit test. Both now hold the stall 0.5 s and recheck.
- **Measurement in a helper.** Measurements live in
  `tests/scheduler_measurements/measure_r2.py` (not collected) rather than in
  CI assertions. A fixed-mix variant isolated completed history from failed
  and pending counts.

**Changed files and uncommitted state to preserve:** none uncommitted in UDB.

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| R2 module, four runs (one with `--log-level=INFO`) | 14 passed each | Windows |
| Full `pytest -q` | 1958 passed, 4 xfailed (R1-D1) | Windows |
| `ruff check .`, `ruff format --check .`, `mypy`, `scripts/doctor.py` | Clean; 248 files formatted; mypy 127 files; doctor OK (13) | Windows |
| Measurement helper, scaled and fixed mixes, 0-100,000 rows, 30 samples | Exit 0; figures in the R2 report | Local timings only |
| 11 planted defects (deletion, re-dispatch, no-await, timeout, budget, stop abandons batch, running counted as pending, audit before flag, recovery rewrites pending, resolved schedules, stop without waiting) | 11 of 11 caught, the timeout defect after tightening two tests | Scratch worktree, since removed |

**Persistence:** UDB commits are local only. This record is on the local
KestrelGaming branch `memory/udb-r2-scheduler-risk-2026-11-24`, stacked on
the unmerged R1 memory branch.

## Next action

**Open blockers or risks:** the user's approval to push and open the draft
PR. Linux CI has not run these tests.

**Next useful step:** a draft PR and independent audit. Then the
recommended follow-ups:

- stall observability: a running count, the oldest claim age, and a warning;
- an operator-documentation checkpoint (migration-failure advice, the D2a
  sentence, the CHANGELOG wording, scheduler guidance);
- a terminal-only retention API once a size requirement exists.

## Revisit when

The R2 PR opens, is audited or merges, or the scheduler dispatch, diagnostics
or retention behavior changes. Compare `master` with this record before relying
on it.
