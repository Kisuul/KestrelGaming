---
name: math-verification
description: Construct independent numerical oracles, analytical fixtures, invariants, boundary tests and defensible error budgets for math-heavy engineering implementations.
---

# Mathematical verification — evidence before claims

## Activate when

Use when mathematical correctness, precision or reproducibility matters: numerical implementations, unit conversions, geometry, simulation, statistics or calibration calculations. This is a supporting verification procedure. Measurement models and standards requirements remain with the domain skill. Load [numerical analysis](../math-numerical-analysis/SKILL.md) when diagnosing finite arithmetic; use the [curriculum](../../docs/MATH_CURRICULUM.md) for shared notation.

## Required inputs

Identify the claim under test, mathematical contract, target implementation/revision, input domain and units/shapes, representation/backend, expected failure behavior and required accuracy. Distinguish an identity from an assumption about data, a runtime convention, an implementation claim and a normative conformance claim. A reference value without its conventions cannot resolve a disagreement.

## Decision procedure

1. **Write falsifiable acceptance criteria first.** Name the output and metric, absolute/relative terms and units, near-zero policy, finite/exception semantics and boundaries. Include at least one plausible wrong answer that must fail. If no production implementation exists, call the result an educational arithmetic fixture rather than an implementation test.
2. **Choose an oracle for the failure being sought.** Derive a small exact case before comparing larger numerical results. Use rationals for rational operations, high precision for rounding investigations, independent algorithms for implementation defects and authoritative vectors for specified conventions. Record shared dependencies; a second wrapper around the same kernel is not independent. See the [oracle table](references/FIXTURE_POLICY.md).
3. **Freeze traceable fixtures.** Record inputs, expected result, derivation, units/shape, oracle precision and provenance, comparison semantics, negatives and mapped test name. A generated golden needs the generating version/configuration and independent review. Do not regenerate expectations to match a regression.
4. **Check the comparator itself.** In Python, `math.isclose(a,b)` accepts when `abs(a-b) <= max(abs_tol, rel_tol*max(abs(a),abs(b)))` for finite values. Specify both tolerances. For an absolute-only `1e-14` gate, `rel_tol=0` is required: `isclose(-1+5e-10,-1,abs_tol=1e-14)` otherwise passes via the default `1e-9` relative term. Test that counterexample and a valid value through the intended gate.
5. **Exercise wrong and boundary cases.** Cover relevant zero/empty/malformed, scale/sign, near-singular, nonfinite and range-limit cases. Add metamorphic properties only where their prerequisites hold: a rotation preserves norm; an arbitrary matrix need not. A round trip can conceal matching forward/inverse faults, and identity alone may admit a completely wrong implementation.
6. **Execute and diagnose.** Capture exact revision, command, runtime/backend and observed result. Preserve a failing input/seed; distinguish oracle, implementation, comparator and model failures before changing anything. Random sampling explores cases but does not prove a property. Statistical acceptance needs its sampling and false-rejection model fixed in advance.
7. **Report each evidence layer separately.** State which claims are supported by fixtures, independent implementation comparison, integration, physical calibration or behavioral trials. Mark unexecuted checks and absent oracles explicitly. Historical CI is evidence only for its tested revision; an arithmetic fixture pass does not demonstrate agent skill effectiveness.

## Worked oracle and adversarial check

For `A=[[3,1],[1,2]]`, `b=[9,8]`, rational Cramer's rule gives determinant `5`, `x=2`, `y=3`. Substitution checks `3*2+3=9` and `2+2*3=8`. A production solver can be compared with this frozen answer without invoking its inverse routine. Substitution is an invariant check, not an independent solver; near singularity, low residual alone cannot bound forward error.

Likewise, norm preservation cannot determine a rotation's direction: both `(+90 degrees)` and `(-90 degrees)` preserve length. For the column vector `(3,4)`, a positive quarter turn in the stated Cartesian convention must also give `(-4,3)`. Test orientation and norm, rather than declaring correctness from norm alone.

## Output and acceptance gate

Produce a claim-to-evidence mapping: contract and inputs, chosen oracle and shared dependencies, comparator and budget, positive/negative cases, executed checks with revision/runtime, observed errors and remaining gaps. Follow the [fixture policy](references/FIXTURE_POLICY.md). The [catalog](../../tests/fixtures/MATH_FOUNDATION_VECTORS.md) covers a bounded educational set; it does not establish a production numerical library, agent behavior, general proof, physical calibration or standards compliance.

## Technical references

- [Python `math.isclose`](https://docs.python.org/3/library/math.html#math.isclose): exact API formula, defaults and nonfinite rules.
- [Python `fractions`](https://docs.python.org/3/library/fractions.html) and [`decimal`](https://docs.python.org/3/library/decimal.html): rational and decimal reference arithmetic.
- [Python `unittest`](https://docs.python.org/3/library/unittest.html): repeatable fixture execution.
- [NIST TN 1297, 1994 edition](https://www.nist.gov/pml/nist-technical-note-1297): measurement uncertainty; it does not prescribe arbitrary algorithmic comparison tolerances.
