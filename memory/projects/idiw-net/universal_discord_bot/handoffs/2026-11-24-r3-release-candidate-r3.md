---
schema: 1
id: 2026-11-24-udb-r3-release-candidate-r3
kind: handoff
scope: project:idiw-net/universal_discord_bot
status: active
evidence: observed
author: claude-code-session-2026-11-24
created: 2026-11-24
updated: 2026-11-24
sources: "Work order UDB-R3 (pasted by the user on 2026-11-24). Draft PR #34 (gh pr create output; ccd PR status: open, draft, mergeable). UDB master 9d762c8 (merge of PR #33), read locally: services/storage.py bootstrap and apply_migrations, bot/app.py _initialize_runtime, tests/test_upgrade_conformance.py, tests/test_version.py, tests/test_docs_invariants.py, tests/upgrade_fixtures/build_udb_0_4_6.py, AGENTS.md, CONTRIBUTING.md, README.md, ROADMAP.md, CHANGELOG.md. Local branch release/0.5.0-candidate. Checks run on Windows 10, CPython 3.12.11, SQLite 3.49.1; results in the table below."
---

# UDB R3: 0.5.0 release candidate

## Summary

**Goal and acceptance criteria:** work order UDB-R3 asks for the lockstep
`0.4.6` → `0.5.0` version update, an explicit historical version-transition
oracle in the upgrade tests, a `0.5.0` candidate changelog entry, documentation
reconciliation, an R4 dev-guild acceptance checklist (not run), and the report
`docs/R3_RELEASE_CANDIDATE.md` with acceptance matrix R3-01 to R3-12. The
feature set is frozen.

**Task outcome:** IN PROGRESS

All twelve requirements PASS locally; candidate disposition READY FOR
HOSTILE AUDIT, no HOLD. With the user's approval, the branch was pushed and
opened as draft PR #34; it is not merged or accepted. No tag, publication,
deployment or Discord access.

**Authorized scope and boundaries (historical; recheck on resume):**

- **Allowed:** the three version sources, version-specific tests, precise
  metadata-transition assertions, release docs, changelog, report, checklist.
- **Excluded:** new functionality, schema or migration changes, fixture
  changes, retention, stall detection, timeouts, concurrency, retry budgets,
  profiles, dependencies, live Discord, tags, publication, deployment, merge.
- **Remote writes:** a draft PR only if the user approves pushing for this work
  order. Earlier R1/R2 approvals do not carry over.

**Target repository, branch, and commit:** `IDIW-NET/Universal_Discord_Bot`,
branch `release/0.5.0-candidate` from `9d762c8`. Candidate commit `b621943` (one commit, 18 files).
Draft PR: https://github.com/IDIW-NET/Universal_Discord_Bot/pull/34.

**Memory revision loaded:** KestrelGaming branch
`memory/udb-r2-scheduler-risk-2026-11-24` at `aaae32c` (not yet on `main`).

## Evidence

**Confirmed observations with sources:**

- **Bootstrap order.** `StorageService.bootstrap()` upserts and commits
  `udb_meta.framework_version` before modules load and apply migrations
  (`bot/app.py` `_initialize_runtime`). So a failed `tickets_0002` migration
  on a 0.4.6 database leaves `framework_version = 0.5.0`; the ledger, not the
  version row, shows a completed upgrade. Now asserted in R1-04/R1-05.
- **Version consumers.** `/about` (diagnostics snapshot from
  `bot.__version__`), `/health` schema line (reads `udb_meta`), boot summary,
  `HTTPService` header (`DEFAULT_USER_AGENT`) all showed `0.5.0` in an offline
  probe. `tests/test_storage.py` already covers the upsert generically.
- **0.4.6 reference classification.** Reminders, settings, moderation, audit,
  announcements, welcome, `services/access.py`, `responses.py`,
  `workflows.py` and `profiles/` have no code diff between `818964f` and
  `9d762c8`, so "In `0.4.6`, …" behavior claims about them were moved to
  `0.5.0`. Historical, fixture-provenance and compatibility references were
  preserved; `0.4.1`–`0.4.5` introduction markers left alone.
- **Fixtures.** Blob hashes unchanged from base; builder `--check` against a
  clean `818964f` worktree passed (both dumps match 0.4.6 output).

**Decisions and rationale:**

- **`CANDIDATE_VERSION = "0.5.0"` hard-coded** in the upgrade test, not read
  from `bot.__version__`, so the oracle is independent and the next bump must
  revisit it. Added to the lockstep lists in AGENTS, CONTRIBUTING and README.
  `HISTORICAL_VERSION` is imported from the fixture builder.
- **Separate helpers:** `_assert_meta_version_transition` for the intentional
  0.4.6 → 0.5.0 change; `_assert_meta_set_at_only` kept for same-version
  restarts. No sleeps or timing assertions.
- **Changelog:** new `[0.5.0] — Release candidate (pending release approval)`
  with release summary and known limitations; empty `[Unreleased]` kept; R1,
  R2, D3 test-only bullets moved to a Tests section, shortened and linked to
  their reports; audit and verification evidence kept.
- **ROADMAP anchor renamed** to `#current-implementation-status-release-candidate`;
  all links updated.
- **R4 checklist** is a separate file, `docs/R4_ACCEPTANCE_CHECKLIST.md`, all
  rows NOT RUN.

**Changed files and uncommitted state to preserve:** none uncommitted in UDB. The PR description lives on PR #34.

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| Baseline `python -m pytest -q` at `9d762c8` (clean worktree) | 1958 passed, 4 xfailed, no skips | Windows |
| Full gate on `b621943` (clean detached worktree) | pytest 1959 passed, 4 xfailed (R1-D1); ruff check clean; ruff format 248 files; mypy 127 files clean; doctor OK (13), version 0.5.0 | Windows; Linux CI not yet run |
| `build_udb_0_4_6.py --source <818964f worktree> --check` | Both dumps match 0.4.6 output; fixture blobs identical to base | Windows |
| Offline probe: upgrade 0.4.6 fixture, call `/about`, `/health`, boot summary, HTTP header, read SQLite read-only | All report `0.5.0`; 10 ledger rows, hashes match code; integrity ok | Scratch test outside repo |
| Upgrade-module sensitivity, scratch worktree | Control 23 passed; pre-R3 oracle on 0.5.0 code: 2 failed; R3 tests on unbumped code: 5 failed; bootstrap keeps old value: 4; extra meta row: 8; wrong version value: 4 | Scratch worktree, since removed |
| Link and anchor check on changed Markdown | 166 links, none broken (one pre-existing false positive at `MODULES.md:171`) | Scratch script |

**Persistence:** UDB commit `b621943` is on the pushed branch
`release/0.5.0-candidate`, draft PR #34. This record is on the pushed
KestrelGaming branch `memory/udb-r3-release-candidate-2026-11-24`, stacked on
the unmerged R2 memory branch; its Git history shows whether it reached
`main`.

## Next action

**Open blockers or risks:** Linux CI on PR #34 (`Verify` run 45502918198)
had not finished when this was written; check `gh pr view 34`. Maintainer
dispositions listed in the R3 report section 8: R2 risk acceptance not
recorded; R1-D1 xfails; version written before migrations; final version
number on a candidate; Windows-only local evidence.

**Next useful step:** confirm Linux CI on PR #34, then an independent
hostile audit. R4 needs separate explicit authorization.

## Revisit when

The R3 PR opens, is audited or merges, R4 is authorized, or UDB's version,
bootstrap order or upgrade tests change. Compare `master` with this record
before relying on it.
