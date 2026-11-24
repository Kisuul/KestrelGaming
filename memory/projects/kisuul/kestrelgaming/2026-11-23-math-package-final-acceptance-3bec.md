---
schema: 1
id: 2026-11-23-math-package-final-acceptance-3bec
kind: decision
scope: project:kisuul/kestrelgaming
status: active
evidence: user-stated
author: kestrel-claude-opus-5-5
created: 2026-11-23
updated: 2026-11-23
sources: "User decision in the 2026-11-23 session (chose final acceptance without the behavioral pilot); PR #3 merged as c268a4d on 2026-11-04 with owner comment 'Accepted for Kestrel Core, provisionally'; main 7820ebc re-verified locally on Windows 10 with CPython 3.12.11 (uv) and 3.14.4; GitHub Actions run 45285176215 green at 7820ebc; portability fix on branch skills/math-acceptance-2026-11-23."
---

# Mathematics package — final acceptance for Kestrel Core

## Summary

**Decision (user-stated, 2026-11-23):** the six core mathematics procedures
delivered by [PR #3](https://github.com/Kisuul/KestrelGaming/pull/3) are accepted
for Kestrel Core. This replaces the provisional acceptance the owner commented on
PR #3 on 2026-11-04.

Acceptance covers the modules as bounded procedural documents together with their
31 arithmetic fixtures, as mapped in the [curriculum](../../../../docs/MATH_CURRICULUM.md).
It does **not** claim measured agent improvement, host activation, or a production
numerical runtime. The [behavioral pilot](../../../../kestrel/evals/MATH_SCORECARD.md)
(7 scenarios, 42 paired runs) remains **NOT RUN**. It is tracked as separate
evaluation work and is not a condition of this acceptance.

## Evidence

**Observed, `main` at `7820ebc`, Windows 10, 2026-11-23:**

- `python tools/validate_seed.py` (CPython 3.12.11): passed.
- `python -m unittest discover -s tests -p test_math_foundations.py`: 31 passed on
  both CPython 3.12.11 and 3.14.4.
- `python -m unittest discover -s tests`: 84 run, **1 failure** on both versions,
  `test_project_catalog_must_reach_project_index`. PR #3 (commit `57b6f857`) added
  an exact-path assertion joined with `/`; the validator reports
  `path.relative_to(root)`, which uses `\` on Windows. Linux CI was unaffected
  (run 45285176215 succeeded at `7820ebc`). This was a portability defect in the
  test, not in any mathematical claim.
- Fix on branch `skills/math-acceptance-2026-11-23`: build the expected path with
  `Path(PROJECT, "INDEX.md")`. The assertion stays exact; validator logic is unchanged.
  Afterwards the full suite ran 84 tests, **OK**, 2 skipped (symlink creation is
  unavailable on this host) on both versions. A negative probe confirmed the exact
  error is absent with the catalog intact and present with the catalog edge removed.
  `git diff --check`: clean.

**Options considered (user chose the first):**

1. Accept now on structural, arithmetic and audit evidence; keep the pilot as
   separate evaluation work.
2. Run an exploratory pilot from the same session. Rejected for now: the host's
   workspace instructions direct every session to boot Kestrel memory, so a
   baseline arm would see the math skills. The scorecard requires runs without
   enforced isolation to be marked contaminated, and the 42 runs are costly.
3. Keep acceptance provisional until an isolated harness runs the full pilot.

**Rationale (inferred):** the package's own claims are limited to procedure content
and small arithmetic examples, which the checks above and the
[2026-11-04 adversarial audit](2026-11-04-math-core-adversarial-audit-v01.md)
support. The pilot measures a different claim, uplift over a baseline, that the
package explicitly does not make.

**Carried-forward limits:** the dimension and `phase_or_none` helpers remain
test-local guards, not validators (see the audit's counterexamples A and B). No
production numerical target, Python 3.9–3.11 run, calibration or standards
conformance has been verified. The [completion handoff](handoffs/2026-11-03-math-package-completion-r02.md)
holds the original delivery evidence. Integration of the fix branch into `main` is
recorded by its pull request, not by this record.

**Lesson:** an exact path in a validator message should be built with `Path` (or
the message normalized with `as_posix()`); CI on one OS hides separator assumptions.

## Revisit when

A math skill or fixture changes; the behavioral pilot runs under enforced isolation
(publish results separately and link them here); a test-local helper is promoted to
a reusable validator; a counterexample contradicts a documented mathematical
statement; or a production numerical target appears.
