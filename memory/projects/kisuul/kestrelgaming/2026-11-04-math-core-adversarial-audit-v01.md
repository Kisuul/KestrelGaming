---
schema: 1
id: 2026-11-04-math-core-adversarial-audit-v01
kind: lesson
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: Ven
created: 2026-11-04
updated: 2026-11-04
sources: "Kisuul/KestrelGaming main c268a4d0be121738cbfdb0d7a90de7874299c0f2; GitHub Actions 41786592890; independently executed bounded probes, CPython 3.13.5/Linux on 2026-11-04."
---

# Adversarial mathematics-core audit — 2026-11-04

## Summary

**Outcome: PARTIAL (bounded positive results, no universal proof/refutation).**
At [main revision c268a4d0be12](https://github.com/Kisuul/KestrelGaming/commit/c268a4d0be121738cbfdb0d7a90de7874299c0f2)
the math core consists of [six procedural skills](../../../../docs/MATH_CURRICULUM.md),
[31 educational math fixtures](../../../../tests/test_math_foundations.py)
and [unexecuted behavioral evaluations](../../../../kestrel/evals/MATH_SCENARIOS.md).
The package **is not a production numerical runtime**.

No contradiction was established in the selected mathematical examples independently
examined. Two counterexamples demonstrate that explicitly **test-local helpers**
are not complete validators. Since those helpers explicitly advertise narrower
behavior, this is not evidence of a shipped numerical-library defect.

## Evidence

### Source, CI and independent execution

- Inspected the six math procedures, fixture inventory, Python test module,
  and behavioral evaluation scoring criteria at the pinned revision.
- [GitHub Actions run 41786592890](https://github.com/Kisuul/KestrelGaming/actions/runs/41786592890)
  at that commit succeeded. Job logs report **67 tests passed**, including
  **31 math tests**. These are CI results, not an independently executed
  full checkout in the audit environment.
- Independently executed a read-only Python probe under **CPython 3.13.5/Linux**.
  Confirmed: exact sum `1e16 + 1 - 1e16 = 1` versus naive floating result
  `0`; rationalized `sqrt(1+x)-1` at represented `x=1e-16` returns
  `5e-17` with approximately `1.25e-33` absolute error against
  an 80-digit `Decimal.from_float` oracle; absolute-only `math.isclose`
  requires `rel_tol=0`; the exact LIN-03 residual/forward-error contrast;
  signed-zero principal phases; and the difference between four independent
  values and eight duplicated storage rows.
- This probe transcribed two limited test helpers but did **not** execute the
  original full repository suite. A first draft of the probe incorrectly
  compared a floating sample-variance result to an exact fraction. That was
  corrected to compare rational inputs; the corrected independent probe passed.
  The probe mistake was **not** a Kestrel test failure.

### Counterexample A — the dimension helper checks length, not type/finiteness

The `dimension_vector` and `multiply_dimensions` functions in
[the test module](../../../../tests/test_math_foundations.py) accept
seven-entry dimension vectors containing `True`, `float("inf")`,
or `1j` as exponent values. The first component of their computed
product becomes `1`, `inf`, or `1j` respectively. A general interface
requiring seven finite real exponents would reject these values.

**Scope:** [The fixture inventory](../../../../tests/fixtures/MATH_FOUNDATION_VECTORS.md)
explicitly says these helpers test vector **length only**; exponent types,
finiteness, unit scale and quantity kind are not implemented. This is
evidence against treating a length-only helper as a complete validator,
not against the helper's declared behavior.

### Counterexample B — the zero-phase example lacks a nonfinite guard

The nested `phase_or_none` helper in the test named
`test_phase_of_zero_not_used_as_measurement` returns `0.0`
for `complex(float("inf"), 1.0)` on the checked CPython runtime.
A finite-only phase interface would reject that input.

**Scope:** The helper tests that exact zero has no reportable phase;
it is not exported as a validated phase API. The
[complex-number procedure](../../../../skills/math-complex-numbers/SKILL.md)
already requires explicit finite-input policy.

### One exact positive anchor and external references

For `A=diag(1,10^-12)`, `b=(1,10^-12)` and candidate `(1,0)`,
exact rational arithmetic gives residual infinity norm `10^-12`,
relative forward error `1`, condition number `10^12` and normwise
backward-error indicator `5e-13`. The
[linear-algebra skill](../../../../skills/math-linear-algebra/SKILL.md)
correctly warns that small residual does not imply high solution accuracy.

[Python math.isclose](https://docs.python.org/3.12/library/math.html#math.isclose)
and [Python cmath](https://docs.python.org/3.12/library/cmath.html)
document the tolerance and signed-zero conventions.
[NIST TN 1297](https://www.nist.gov/pml/nist-technical-note-1297)
provides a measurement-uncertainty framework; it does not certify the
sampling assumptions or error budgets of these fixtures.

### Boundaries not verified

There is no production numerical implementation here to prove correct
over an API domain. No independent LU/QR/SVD solver, physical calibration,
standards conformance, Python runtime matrix, or general floating-point
accuracy theorem was verified. The [seven behavioral scenarios and proposed
42-run paired pilot](../../../../kestrel/evals/MATH_SCORECARD.md)
are explicitly **NOT RUN**; there is no demonstrated agent-skill uplift.
Finite fixture passes do not logically prove universal correctness.

## Next checks

1. If either test-local helper is to become a reusable validator, specify its
   full contract and test rejection of malformed, Boolean, nonfinite and
   complex values before promoting it; do not imply that this PR implements one.
2. Execute the preregistered blinded behavioral pilot, preserving separate
   evaluator answers, outputs, failure cases and cost measurements.
3. When a production numerical target exists, use independently derived
   differential, boundary and adversarial tests with justified tolerances.

This PR only records the audit and indexes it. It does not change skills,
tests, production code, permissions, CI, or operating contracts.

## Revisit when

A math skill or fixture changes, a full numerical implementation is introduced,
the behavioral trials run, backend/runtime expectations expand, or an independent
counterexample contradicts a documented mathematical statement.
