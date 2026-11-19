---
schema: 1
id: 2026-11-19-udb-d1-atomic-ticket-jobs-d1
kind: handoff
scope: project:idiw-net/universal_discord_bot
status: active
evidence: observed
author: claude-code-session-2026-11-18
created: 2026-11-19
updated: 2026-11-19
sources: "Work order github.com/IDIW-NET/Universal_Discord_Bot/issues/15 (D1/D0); draft PR #17, branch feature/0.5.0-d1-atomic-ticket-jobs, D1 commit 4d1a586 on master 61fdf41, then master 6491be9 (PR #16) merged in; checks run locally on CPython 3.12.11."
---

# UDB D1: atomic ticket, opening event and inactivity job

## Summary

**Goal and acceptance criteria:** issue #15. A ticket created through
`/ticket open` or the `ticket.create.v1` provider commits with its opening
event and exactly one `tickets.inactivity_check` job, or none of them commit.
Same-owner replays add nothing, and audit stays optional. The work order also
required a D0 contract note, 15 adversarial acceptance cases, and a draft PR
for hostile audit with no merge.

**Task outcome:** PARTIAL

Implemented, verified locally, and opened as draft
[PR #17](https://github.com/IDIW-NET/Universal_Discord_Bot/pull/17) at the
user's request. Awaiting CI, hostile audit and owner decision.

**Authorized scope and boundaries (historical; recheck on resume):** scheduler
joined-insert API, Tickets store/cog wiring, tests, D0 docs. Not authorized:
Intake product files, contract semantics, `contracts/` edits, retry policy
(D2), backfill, migrations, version or release.

**Target repository, branch, and commit:** `IDIW-NET/Universal_Discord_Bot`,
branch `feature/0.5.0-d1-atomic-ticket-jobs`.

**Memory revision loaded:** this project's PROFILE and the 2026-11-18
type-gate handoff on branch `memory/udb-type-gate-coverage-20261118`.

## Evidence

**Confirmed observations with sources:**

- On master, `TicketsCog._after_create()` called `scheduler.create_job()` in a
  separate transaction after commit and swallowed failures. A test with a
  trigger rejecting `scheduler_jobs` showed `DID NOT RAISE StorageError`: the
  ticket was committed and reported created with no job.
- `inactivity.py` imports `TicketStore`, so the job policy moved to a pure
  `modules/tickets/inactivity_policy.py`.
- Three existing tests encoded the old outcome (`(1, 1, 1, 0)`) and were
  updated to D1: `test_ticket_creation_boundary.py`,
  `test_intake_ticket_flow.py` and `test_tickets_commands.py`.
- PR #16 merged while D1 was in flight, and the only conflict was
  `CHANGELOG.md` `[Unreleased]`. It was resolved by merging master into the
  branch, with no force-push.

**Decisions and rationale:**

- `SchedulerService.insert_job_in_transaction(conn, ...) -> int` shares
  validation and SQL with `create_job()` and never locks, commits, rolls back
  or re-reads. It rejects a connection outside an open transaction via
  `StorageService.holds_transaction()`, which checks connection identity and
  that the lock is held but not lock ownership. This is documented.
- `TicketStore(storage, scheduler=...)` is optional. The guarantee covers the
  host-wired cog path; a bare store schedules nothing (D0 point 6).
- A `ValueError` from job validation is converted to `StorageError`, so it
  surfaces as a creation failure.
- `contracts/ticket_creation.py`'s "Audit and scheduling are best effort after
  commit" is now inaccurate for the bundled provider. It was left unchanged
  because it is out of scope, and flagged in the PR.

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| New and updated tests on unchanged master | Red as designed (defining case: `DID NOT RAISE StorageError`) | Windows, CPython 3.12.11 |
| Targeted D1, Tickets, Intake-ticket, C2a and scheduler suites | 155 passed | Same |
| Full verify on D1 before merging master | 1739 passed; ruff clean; mypy 98 + 25 files; doctor OK | Same |
| New gate on the merged tree | `python -m mypy` 127 files; guard and doc tests pass | Same |
| Full verify on the merged tree | See PR #17 body and CHANGELOG | Same |

**Persistence:** UDB work is pushed in draft PR #17. This record is committed
locally on the KestrelGaming memory branch.

## Next action

**Open blockers or risks:** CI and the hostile audit are pending. D2 owns
handler idempotency, retries, recovery and post-commit rescheduling on other
mutations. Any repair of pre-D1 tickets without jobs needs its own plan.

**Next useful step:** watch CI on #17 and respond to audit findings. After
merge, archive this handoff and update the PROFILE's verification-gate note.

## Revisit when

PR #17 is audited, merged or closed, or D2 begins.
