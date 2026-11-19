---
schema: 1
id: 2026-11-19-udb-d2a-safe-dispatch-d2a
kind: handoff
scope: project:idiw-net/universal_discord_bot
status: active
evidence: observed
author: claude-code-session-2026-11-19
created: 2026-11-19
updated: 2026-11-19
sources: "Work order github.com/IDIW-NET/Universal_Discord_Bot/issues/18 (D2a); draft PR #19, branch feature/0.5.0-d2a-safe-dispatch, commit 1a14e3d on master 10ae6eb (D1/PR #17 merged); checks run locally on CPython 3.12.11, SQLite 3.49.1, discord.py 2.7.1, mypy 1.20.2."
---

# UDB D2a: safe scheduler dispatch and missing-handler preservation

## Summary

**Goal and acceptance criteria:** issue #18. A due pending job with no
registered handler must stay pending with no attempt consumed, must not starve
dispatchable work, and a handler that vanishes between selection and invocation
must not run, with only that dispatch's own claim released. The order also
required negative tests first, an `unhandled_due_count` diagnostic, and a draft
PR for hostile audit. It forbade merge, release, deployment and D2b.

**Task outcome:** PARTIAL

Implemented, verified locally and in CI, and opened as draft
[PR #19](https://github.com/IDIW-NET/Universal_Discord_Bot/pull/19).
Awaiting hostile audit and owner decision.

**Authorized scope and boundaries (historical; recheck on resume):** the
`services/scheduler.py` dispatch path, `services/diagnostics.py`, tests and
scheduler docs. The order also allowed one optional docstring fix in
`contracts/ticket_creation.py`. Not authorized: schema or migration, public job
rewriting, multi-process leases, handler revocation, the max-attempts or retry
policy, D2b's permanent-error taxonomy, version, release.

**Target repository, branch, and commit:** `IDIW-NET/Universal_Discord_Bot`,
branch `feature/0.5.0-d2a-safe-dispatch`, commit
`1a14e3d34e09b835a27be046f3acbd1bec5fd695` on `master` `10ae6eb`.

**Memory revision loaded:** the UDB PROFILE, the archived type-gate handoff and
the D1 handoff, on branch `memory/udb-type-gate-coverage-20261118` at `de39aa9`.

## Evidence

**Confirmed observations with sources:**

- On `10ae6eb`, `process_due_once()` claimed a job (`attempts += 1`) before it
  looked up the handler. A job with no handler was then failed terminally as
  `unknown_job_type`. Because `list_due_jobs()` ignored handlers, older
  unhandled rows filled the batch ahead of dispatchable rows.
- `claim_job()` is the only writer of `status='running'`, and every later
  transition changes `status`. That makes `(id, running, claimed_at, attempts)`
  a sound compare-and-swap identity within one process.
- A checkout made under `core.autocrlf=true` before `.gitattributes` landed
  left index stat sizes from the CRLF files. `git status` then showed 242
  "modified" files with empty diffs. `git add -u` fixed the stat entries; no
  content changed.

**Decisions and rationale:**

- Eligibility is decided in SQL with
  `job_type IN (SELECT value FROM json_each(?))`. This binds one JSON array, so
  there is no `IN ()` and no host-parameter limit. An empty registry returns
  `[]` without running a query. `list_due_jobs()` is unchanged. The query plan
  walks the existing `status_run_idx` with no temp sort.
- The handler is looked up again before each claim. After the claim it must
  be the same object (`is`). If not, private `_release_claim()` runs:
  `attempts - 1`, `claimed_at` cleared, `updated_at` stamped, `run_at`, payload
  and `last_error` kept. A SQLite failure leaves the row `running` and records
  `claim_release_failed`.
- `SchedulerTickResult` gained `handler_unavailable` and `released`.
  `SchedulerDiagnosticSnapshot` gained the required field
  `unhandled_due_count`. A positive count is a `scheduler.jobs` WARNING, never
  an ERROR.
- `test_unknown_job_type_is_failed_safely` was revised to
  `..._preserved_pending_not_failed`, not deleted.

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| New and revised tests on unchanged `10ae6eb` code | 27 failed, 12 passed (the in-flight tests document behaviour that was already correct) | Windows, CPython 3.12.11 |
| Offline evidence script (separate `sqlite3` reads, EXPLAIN QUERY PLAN) | 1,200 older orphan rows byte-identical while one eligible job ran with `limit=1`; release and failure rows as in the PR body | Same; SQLite 3.49.1 |
| Full gates on `1a14e3d`, clean tree | pytest 1774 passed; ruff check and format clean (238 files); mypy 127 files; doctor OK, 13 checks | Same |
| GitHub Actions run 44621528075 on `1a14e3d` | success; same five results (confirms `json_each` on CI's Linux SQLite) | ubuntu-latest, Python 3.12 |

**Persistence:** UDB work is pushed in draft PR #19. This record is committed
locally on KestrelGaming branch `memory/udb-d2a-safe-dispatch-20261119`.

## Next action

**Open blockers or risks:** none blocking audit. Residual risks are listed
in the PR:

- Claim identity has one-second resolution.
- A failed release leaves Tickets jobs to fail at recovery.
- The dispatch query now depends on `json_each`.
- Per-tick cost is linear in older unhandled rows.
- A pre-existing malformed handled-type row fails every tick.

Handler idempotency, retry policy and permanent errors belong to D2b.

**Next useful step:** answer hostile-audit findings on #19. After
merge, archive this handoff. Then note in the PROFILE that scheduler dispatch
is handler-aware.

## Revisit when

PR #19 is audited, merged or closed, or D2b begins.
