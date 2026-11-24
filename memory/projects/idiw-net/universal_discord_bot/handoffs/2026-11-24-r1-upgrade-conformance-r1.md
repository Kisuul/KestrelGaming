---
schema: 1
id: 2026-11-24-udb-r1-upgrade-conformance-r1
kind: handoff
scope: project:idiw-net/universal_discord_bot
status: active
evidence: observed
author: claude-code-session-2026-11-24
created: 2026-11-24
updated: 2026-11-24
sources: "Work order UDB-R1 (pasted by the user on 2026-11-23). UDB master 6416256 (merge of PR #30) and historical 818964f (v0.4.6, merge of PR #6), read locally. Local branch test/0.5.0-r1-upgrade-conformance. Checks run on Windows 10, CPython 3.12.11, SQLite 3.49.1, discord.py 2.7.1, aiosqlite 0.22.1; results in the table below."
---

# UDB R1: 0.4.6 to current upgrade and migration conformance

## Summary

**Goal and acceptance criteria:** work order UDB-R1 asks whether databases
written by UDB 0.4.6 upgrade safely to current unreleased `master`. It is
test-first and bounded, with eight areas R1-01 to R1-08:

- an authentic 0.4.6 fixture;
- a successful upgrade;
- restart idempotency;
- conflicting Intake source references;
- a corrected-conflict retry;
- timestamp compatibility;
- scheduler continuity;
- privacy and isolation.

Each area must be PASS, FAIL or BLOCKED. A product defect would mean HOLD plus
a separate corrective work order.

**Task outcome:** IN PROGRESS

All eight areas PASS locally, with R1-D1 recorded and no HOLD. The draft PR
waits for the user's push approval; nothing has been pushed.

**Authorized scope and boundaries (historical; recheck on resume):**

- **Allowed:** tests, a deterministic fixture builder and fixtures,
  `docs/R1_UPGRADE_CONFORMANCE.md`, and one CHANGELOG `[Unreleased]` line.
- **Excluded:** production code, schema, migrations, dependencies, profiles,
  version metadata, repair commands, backfills, R2 work, merging and releasing.
- **Remote writes:** the work order allows a draft PR only if the environment
  authorizes it. The user's approval is still needed before pushing.

**Target repository, branch, and commit:** `IDIW-NET/Universal_Discord_Bot`,
local branch `test/0.5.0-r1-upgrade-conformance` from `6416256`.

**Memory revision loaded:** KestrelGaming `main` at `e43f0aa`.

## Evidence

**Confirmed observations with sources:**

- **0.4.6 wrote no Intake-sourced tickets.** Its only creator was
  `/ticket open`, which writes `source='manual'`; the README called
  `source`/`source_ref` "present for future intake linkage". Store-API callers
  could still write Intake rows.
- **0.4.6 inactivity jobs** came from the cog, after commit and not atomically,
  with `max_attempts=1` and an envelope guild equal to the payload guild. D2b's
  stricter validation accepts them.
- **Timestamp formats.** 0.4.6 and current code write every ticket and
  scheduler instant canonically (`isoformat(timespec="seconds")` in UTC). The
  D3 hypothesis that upgraded 0.4.6 rows compare wrongly is refuted for
  ordinary 0.4.6 writes.
- **Defensive data-quality defect R1-D1 (low).** Four parseable noncanonical
  forms are judged by their text, not their instant, in `flag_inactive()` and
  `list_inactive_tickets()`: `Z` at the exact threshold, `+05:30`, `-05:00`
  and a space separator. They need manually altered or imported rows. They are
  kept as strict `xfail(raises=AssertionError)` tests.
- **Ledger.** Only `tickets_0002_unique_intake_source_ref` is new. Every 0.4.6
  ledger hash equals today's SQL hash for that id.
- **Upgrade side effects.** The upgrade changes only `udb_meta.set_at`, the
  appended ledger row, and the recovery of the abandoned 0.4.6 `running` job
  (failed, attempt used; the same rule 0.4.6 had).
- **Duplicate references.** Startup fails with module, migration id and column
  names only. Nothing partial is left, and the whole process stops. The README's
  count query is accurate.
- **Docs observations, not changed:** `OPERATOR_GUIDE.md`'s generic "Migration
  'X' failed" advice (adjust the SQL, bump the id) is wrong for this data
  conflict. The CHANGELOG line saying the migration "reports conflicting
  historical rows" overstates it.

**Decisions and rationale:**

- **Fixture as a text dump.** It is an `iterdump()` dump of a database written
  by the real 0.4.6 runtime, from a pinned worktree run with `python -I`. CI
  needs no Git history or network. `build_udb_0_4_6.py --check` proves the
  dump's provenance.
- **Writes through 0.4.6 code.** 0.4.6 command callbacks run through 0.4.6's own
  test double `_GuildInteraction` after their registered checks. The only
  substitution is a controlled clock in the 0.4.6 storage, scheduler, audit and
  store modules, for determinism.
- **Full snapshot diff.** Every table and `sqlite_master` are compared before
  and after the upgrade, with named allowed changes, rather than spot checks.

**Changed files and uncommitted state to preserve:** in UDB:

- `tests/test_upgrade_conformance.py`
- `tests/upgrade_fixtures/build_udb_0_4_6.py`
- `tests/upgrade_fixtures/udb_0_4_6_baseline.sql`
- `tests/upgrade_fixtures/udb_0_4_6_duplicate_refs.sql`
- `docs/R1_UPGRADE_CONFORMANCE.md`
- `CHANGELOG.md`

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| Builder `--write`, then `--check` against a clean `818964f` worktree | Byte-identical rebuild of both fixtures; `--check` passed again on the final tree | Scratch worktree |
| R1 module | 22 passed, 4 xfailed; also with `--log-level=INFO` | Same machine |
| R1 module with non-loopback connects and DNS refused | 22 passed, 4 xfailed; 0 attempts | Pytest plugin in the scratchpad |
| Full `pytest -q`, first run | 1 failed, 1943 passed, 4 xfailed: R1-05 counted the failed attempt's INFO record once earlier modules had enabled INFO. Test-order bug in the new test; fixed by clearing the capture before the retry | Same machine |
| Full `pytest -q`, after the fix | 1944 passed, 4 xfailed in 360.58 s | Same machine |
| `ruff check .`, `ruff format --check .`, `mypy`, `scripts/doctor.py` on the final tree | Clean; 246 files formatted; mypy 127 files; doctor Overall OK (13) | Same machine |
| 10 planted defects (non-unique index, backfill, ledger before SQL, recovery retrying used attempts, raised budgets, exclusive threshold, leaked refs, cleared flags, no recovery, `julianday()` fix) | 10 of 10 changed the result; the `julianday()` fix flipped exactly the 4 xfails | Scratch worktree, since removed |

**Lesson:** a test that asserts on `caplog` records after an earlier startup in
the same test must clear or scope the capture. Earlier modules in the full
suite leave the `udb` logger at INFO, so a module-only run can hide the leak.

**Persistence:** UDB commits `4b15056` (tests and fixtures, the tested head)
and `5b2740d` (docs) exist only on the local branch
`test/0.5.0-r1-upgrade-conformance`; not pushed. This record is on the
KestrelGaming branch `memory/udb-r1-upgrade-conformance-2026-11-24`, local only.

## Next action

**Open blockers or risks:** the user's approval to push and open the draft PR.
R1-D1 needs a corrective work order only if noncanonical rows are to be
supported.

**Next useful step:** independent hostile audit of the R1 PR, then R2
(operational risk disposition).

## Revisit when

The R1 PR opens, is audited or merges, or `tickets_0002` or the inactivity
comparison changes. Compare `master` with this record before relying on it.
