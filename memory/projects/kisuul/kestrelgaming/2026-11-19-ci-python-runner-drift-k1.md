---
schema: 1
id: 2026-11-19-kestrelgaming-ci-python-runner-drift-k1
kind: lesson
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: claude-code-session-2026-11-19
created: 2026-11-19
updated: 2026-11-19
sources: "GitHub Actions runs 42786962942 (main 504da1d, 2026-11-10, green) and 44632391625 (PR #26 f55e69d, 2026-11-19, red); commit be7a4f6 / PR #22 (merged into skills/audio-dsp-core-foundation-2026-11-03); fix PR #27 (commits f711b6d, 28cf1c9); local unittest runs on Windows with CPython 3.12.11 (uv) and 3.14.4; user decision in the 2026-11-19 session."
---

# CI drifted off Python 3.12 with the runner image; pin it

## Summary

KestrelGaming's `validate` workflow ran bare `python3` on `ubuntu-latest`
with no interpreter pin. When the runner image moved from `ubuntu-24.04` to
`ubuntu-26.04`, the default `python3` changed under it.
`test_invalid_dates_and_reversed_dates` then failed on every branch based on
`main`. That test matched Python's own `date.fromisoformat` error wording,
which is not stable across versions. Memory content was not at fault.

**Lesson:** when CI fails on a memory-only change, first compare the
`Runner Image` lines of the last green run and the failing run
(`gh run view <id> --log | grep Image:`). Then check whether a known fix has
actually reached `main` (`git merge-base --is-ancestor <fix> origin/main`).

**Decision (user-stated, 2026-11-19):** fix both the tests and CI.
[PR #27](https://github.com/Kisuul/KestrelGaming/pull/27) makes two changes:

- It pins CI to CPython 3.12 with `actions/setup-python` and logs
  `python3 --version`.
- It brings the version-independent validator date message (`be7a4f6`)
  to `main`.

## Evidence

- **Observed, CI:** run 42786962942 used `ubuntu-24.04` and passed. Run
  44632391625 used `ubuntu-26.04` and failed, with the message `day 30 must
  be in range 1..28 for month 2 in year 2026`. That run did not log the
  runner's Python version. The three earlier UDB memory branches failed the
  same way on 2026-11-19.
- **Observed, an unmerged fix:** `be7a4f6` (PR #22) already fixed the
  diagnostic, but it merged into the long-lived audio branch
  `skills/audio-dsp-core-foundation-2026-11-03`, never `main`. Audio-branch CI
  stayed green while `main`-based branches broke.
- **Observed, this Windows machine:** the default `python` is 3.14.4 and uv
  provides 3.12.11. Before the fix, the date test failed on 3.14.4 and passed
  on 3.12.11. With PR #27's commits, it passes on both.
  `test_project_catalog_must_reach_project_index` fails on Windows under both
  versions, because the messages use `\` separators where the test expects
  `/`. It passes on Linux CI and is not addressed.
- **To run the suite on the reference interpreter here:**
  `uv run --no-project --python 3.12 python -m unittest discover -s tests`.
- **User-stated:** the user first put the failure down to their machine not
  matching the 3.12 test environment. The runner evidence showed that CI had
  drifted too. They then decided: "Update the tests and ci as you
  originally wanted."
- **Alternatives considered:** pinning CI alone would restore green but leave
  local 3.14 runs red. The date fix alone would make the tests
  version-independent but leave CI's interpreter free to drift again. PR #27
  does both.
- **Hypothesis, minor:** after one branch switch on this machine, three
  edited memory files were left behind as untracked copies, byte-identical
  to the committed versions. The likely cause is that an editor held them
  open. Compare such leftovers with the commit before deleting them.

## Revisit when

PR #27 merges or is closed, the workflow's Python pin changes, or the
Windows path-separator test is fixed.
