---
name: math-verification
description: Construct independent numerical oracles, analytical fixtures, invariants, boundary tests and defensible error budgets for math-heavy engineering implementations.
---

# Mathematical verification — evidence before claims

## Activate when

Use for any numerical method whose correctness, precision, calibration or reproducibility matters, especially DSP, graphics, simulations, geometry, statistics, optimizers or unit conversions. Mathematical verification is a supporting procedure, not an installed automatic prover. For numerical pitfalls use [numerical analysis](../math-numerical-analysis/SKILL.md).

## Procedure

1. **Write a contract.** Specify units, domains, dimensions/shapes, normalization, boundary conditions, indices, tolerance, timebase, finite-value policy and failure semantics. Distinguish analytical identity, model assumption, implementation behavior and standard-specific conformance.
2. **Select unrelated oracle types.** Prefer exact `fractions.Fraction` for rational arithmetic, decimal/high-precision evaluation when independent precision is helpful, symbolic derivation, hand-solvable analytical cases, published vectors with explicit provenance, or a genuinely independent implementation. Two wrappers around the same code path are **not independent** oracles.
3. **Freeze and document fixtures.** Every fixture includes inputs, expected results, units, derivation/source, numeric representation, tolerances and reason for the test. Pin external versions when numbers are library-generated and do not silently update golden values after regressions.
4. **Exercise properties and boundaries.** Check invariants (norm/energy preservation only under the applicable transform), dimensional consistency, linearity where assumed, scale and sign metamorphisms, reversibility when valid, random seeded cases, empty/degenerate/near-singular inputs, nonfinite and extreme magnitudes. Property-based sampling is a search technique, not exhaustive proof.
5. **Choose comparison metric responsibly.** For exact integers/rationals require exact equality. For approximations use explicit absolute and relative tolerances, derived from a conditioning/error budget; near zero need an absolute floor. Reject nonfinite outcomes unless the contract expects them. Avoid a single generous tolerance that masks faults.
6. **Separate evidence layers.** Unit/fixture pass, independent library comparison, application integration, performance/latency, instrument/standards conformance and formal proof are separate claims. Record which actually happened and on what revision.
7. **Review failures, not just successes.** Preserve counterexamples and seed/configuration; reproduce failure before reducing tolerance or modifying a golden; report unresolved gaps, including unexecuted checks.

## Worked example

Solve `[[3,1],[1,2]] · [x,y] = [9,8]`. The exact determinant is `5`; Cramer's rule yields `x = 2` and `y = 3`. Independently substitute to obtain `[9,8]` with zero residual over rationals. A floating solver can be checked against this result **without relying on its own inverse routine**. For near-singular cases, a low residual does not bound forward error without sensitivity analysis.

## Acceptance gate

The [fixture policy](references/FIXTURE_POLICY.md) is followed, positive and adversarial fixtures exist, expected results are independently derived or their shared dependencies identified, and CI results are tied to an exact commit. Standard-library demonstrations do **not** establish independent comparison against a production implementation. Never label synthetic test passing as compliance with IEEE, ISO, IEC, ITU, W3C or instrument standards.

## References

- [Python `fractions`](https://docs.python.org/3/library/fractions.html) — exact rational oracles.
- [Python `decimal`](https://docs.python.org/3/library/decimal.html) — configurable decimal arithmetic.
- [Python `unittest`](https://docs.python.org/3/library/unittest.html) — repeatable test harness.
- [NIST TN 1297](https://www.nist.gov/publications/guidelines-evaluating-and-expressing-uncertainty-nist-measurement-results-1994-edition) — measurement uncertainty is not the same as algorithmic tolerance.

**Limitations:** deterministic tests do not establish general proofs, device calibration, security properties, host behavior or external standards compliance.
