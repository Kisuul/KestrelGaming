---
schema: 1
id: 2026-11-19-udb-d2b-recovery-safe-inactivity-d2b
kind: handoff
scope: project:idiw-net/universal_discord_bot
status: archived
evidence: observed
author: claude-code-session-2026-11-19
created: 2026-11-19
updated: 2026-11-19
sources: "Work order UDB-D2b (pasted by the user in the session; no GitHub issue). PR #21, branch feature/0.5.0-d2b-recovery-safe-inactivity, commits f2b5497 (tests) and bd8068e (implementation) on master 39f02c2, merged as 8e8e303 at 2026-11-20T01:16Z after two GO audits. Checks run locally on CPython 3.12.11, SQLite 3.49.1, discord.py 2.7.1, mypy 1.20.2; GitHub Actions run 44646820073."
---

# UDB D2b: bounded retry and recovery-safe Tickets inactivity

## Summary

**Goal and acceptance criteria:** work order UDB-D2b. A Tickets inactivity job
may run again after an interrupted attempt, but it must produce at most one
flag and one staff-only event for the same inactivity state. The other
criteria:

- New jobs get three attempts through both creation paths.
- An invalid payload, or contradictory guild provenance, fails permanently.
- Ordinary failures retry within the budget.
- Interrupted claims recover according to the remaining budget.
- No-op cases complete normally.
- D1 and D2a guarantees stay intact.

This is not exactly-once execution and not guaranteed delivery.

**Task outcome:** COMPLETE

Delivered as draft [PR #21](https://github.com/IDIW-NET/Universal_Discord_Bot/pull/21)
at `bd8068e`. A hostile audit and a Kestrel audit both returned GO with no
merge-blocking defects. The owner merged it on 2026-11-20 UTC as `8e8e303`.
The record was archived when written, because its lessons went straight into
the [PROFILE](../PROFILE.md) and are listed below.

**Authorized scope and boundaries (historical; recheck on resume):**

- **Allowed:** `modules/tickets/inactivity_policy.py`, `modules/tickets/inactivity.py`, `services/scheduler.py`, tests, the scheduler and Tickets docs, and `CHANGELOG.md`.
- **Excluded:** migrations, new job statuses, rewriting persisted attempts, an outbox, operator retry commands, D3, merge, release and deployment.
- **Memory:** the order also excluded Kestrel memory updates without separate authorization. The user gave that authorization for this record.

**Target repository, branch, and commit:** `IDIW-NET/Universal_Discord_Bot`,
branch `feature/0.5.0-d2b-recovery-safe-inactivity` (base `39f02c2`, head
`bd8068e`), merged as `8e8e303`.

**Memory revision loaded:** KestrelGaming `main` at `8ef71b5`: the UDB PROFILE
and the D1 and D2a handoffs.

## Evidence

**Confirmed observations with sources:**

- **Both creation paths read one constant.** `TicketStore._insert_required_inactivity_job()` and `TicketsCog._schedule_inactivity_check()` both use `INACTIVITY_MAX_ATTEMPTS`, so changing it reached both.
- **Requiring the envelope guild was safe.** Every historical job path has set the envelope `guild_id` since Tickets was introduced (`809fad1`), so requiring it strands no legitimate row.
- **A baseline defect was confirmed by a direct probe.** On `39f02c2`, a job with envelope guild 1001 and payload guild 2002 flagged the guild 2002 ticket and completed. On the branch, it fails with `NonRetryableJobError` and leaves the ticket untouched.
- **Replay safety comes from unchanged code.** `flag_inactive()` writes the flag and its event in one transaction, conditional on `inactivity_flagged_at IS NULL`. `recover_abandoned_jobs()` sets `run_at` to the recovery time.
- **Staleness moves with retries.** The handler measures staleness from `job.run_at`, and retry and recovery move it forward. A replay therefore asks whether the ticket is stale as of the replay. The PR documents this, and the audit accepted it.
- **Test hygiene lesson.** If a test fails an assertion before closing its `StorageService`, the aiosqlite worker thread outlives the event loop. It later raises "Event loop is closed", which pytest reports as an ERROR in an unrelated later test's setup. An autouse fixture that closes leftover storage fixes it.
- **Suite runtime.** Locally the full suite took about 600 s for 1,826 tests. The whole CI job took 38 s on Linux.

**Hypotheses and assumptions:** the slow local suite is likely caused by
Windows file I/O or antivirus scanning of temp files. This was not confirmed.
Bot-lifecycle tests each take 1–1.6 s, so shutdown is not the cause.

**Decisions and rationale:**

- **One narrow marker.** `NonRetryableJobError` is a plain `Exception`, deliberately not a `ValueError`. It routes to the existing `fail_job(..., retry=False)`, adding no new state or failure path. Only the raised exception's type counts, and only the type name is stored or logged.
- **Fixed reason codes.** Tickets raises the marker before any store access, with the codes `invalid_payload`, `invalid_envelope_guild` and `guild_mismatch`. It logs the code and the job ID only.
- **Tests first.** Tests were committed separately before the implementation, so the red-then-green history stays visible.
- **Status docs left alone.** `AGENTS.md`, the `ROADMAP.md` table and README "What comes next" still described D2b as planned at merge, on purpose.

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| New and revised tests on unchanged `39f02c2` | 51 failed and 27 passed; the classification module failed to import the marker | Windows, CPython 3.12.11 |
| Targeted D2b, D1 and D2a files on the branch | 124 passed | Same |
| `python scripts/verify.py` on the final tree | pytest 1826 passed; ruff check and format clean (240 files); mypy clean (127 files) | Same |
| `python scripts/doctor.py` | OK, 13 checks | Same |
| Contradictory-guild probe, baseline vs. branch | Baseline flagged the other guild's ticket; the branch failed the job permanently | Temporary worktree, since removed |
| GitHub Actions run 44646820073 | Local quality gate passed (38 s) | ubuntu-latest, Python 3.12 |
| PR #21 audits | Two GO reviews of head `bd8068e`, no blocking defects | Reviews posted on the PR |

**Persistence:** UDB work merged via PR #21 as `8e8e303`. This record lives on a
KestrelGaming memory branch; its Git history shows whether it has been
integrated.

## Next action

**Open blockers or risks:** none blocking. These residual risks were accepted
by the audits:

- Retry is bounded, not guaranteed.
- Rows stored before D2b keep a single attempt.
- An audit record lost after the commit is not recreated.
- A replay measures staleness from the moved `run_at`.
- The Kestrel audit suggested one hardening test, not yet written: reject the staff-only event INSERT after the conditional UPDATE and assert that the flag rolls back.

**Next useful step:**

1. Open a narrow docs PR reconciling the D2b status lines in `README.md`, `AGENTS.md` and the `ROADMAP.md` merged table. Both audits asked for this after merge.
2. Work orders filed on 2026-11-19 from a read-only review:
    - [#22](https://github.com/IDIW-NET/Universal_Discord_Bot/issues/22) (D2c): commit follow-up checks in the activity transaction.
    - [#23](https://github.com/IDIW-NET/Universal_Discord_Bot/issues/23) (D2d): isolate unreadable scheduler rows.
    - [#24](https://github.com/IDIW-NET/Universal_Discord_Bot/issues/24) (D2e): recent-failure diagnostics.

    Each issue carries recommended defaults for the owner to confirm, and D2e runs after D2d.
3. Review findings not filed as issues:
    - Retention, and de-duplication of superseded checks.
    - Reminders' separate dispatcher.
    - Duplicated cog helpers (`admin`'s `_guild_id` has already drifted).
    - Project status repeated across many docs.
    - The version kept in five places.
    - CI hardening (SHA pins, `permissions`, timeouts).
    - Dev tools listed in `requirements.txt`.

## Revisit when

D2c, D2d or D2e starts, the status docs are reconciled, or one of the residual
risks above shows up in practice.
