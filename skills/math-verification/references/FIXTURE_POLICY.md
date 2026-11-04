# Mathematical fixture and independent-oracle policy

## Minimal fixture schema

Record **fixture ID, purpose, mathematical contract, inputs and units, expected output, derivation/source, reference representation, tolerance, negative or boundary cases, backend/version, and observed test command/commit**. Keep expected outputs separate from the implementation path under review.

## Oracle selection

| Oracle | Strong for | Independence caveat |
| --- | --- | --- |
| Hand calculation / symbolic identity | Small exactly solvable examples | Human transcription can be wrong; review arithmetic |
| `fractions.Fraction` | Rational arithmetic, linear systems with rational coefficients | Same rational formula can reproduce a conceptual error |
| `decimal.Decimal` with specified context | Cross-radix checks, high-precision intermediate | Decimal precision is finite, not automatically exact for transcendental functions |
| Independently written implementation | Algorithmic divergence | Check it does not share the same kernel/normalization bug |
| External published or library-generated vector | Cross-implementation behavior | Pin version, method, conventions, citation, license if necessary |

Test properties of algorithms at different scales and signs; include empty, zero, near-zero, ill-conditioned, overflow/underflow, nonfinite and representation-boundary inputs as appropriate. Avoid accidental input filtering that discards the difficult cases.

### Comparisons

- Exact types: equality, with no floating tolerance.
- Approximate types: require finite unless the contract explicitly expects nonfinite. Choose absolute and relative tolerances independently; specify a near-zero floor rather than relying on relative error there.
- Statistical checks: specify seed, number of samples, acceptance probability, repeated-testing considerations and deterministic alternatives. Do not turn probabilistic acceptance into a universal guarantee.
- Standard conformance: use the actual normative document and conformance suite/conditions, not just a suggestive formula.

## Included examples

The [fixture derivations](../../../tests/fixtures/MATH_FOUNDATION_VECTORS.md) and `tests/test_math_foundations.py` use only the Python standard library to illustrate independently checkable results. They are an **educational reference test set**, not a comprehensive verifier. A target application's behavior requires its own integration cases and failure telemetry.

## Sources

- [Python `fractions`](https://docs.python.org/3/library/fractions.html)
- [Python `decimal`](https://docs.python.org/3/library/decimal.html)
- [Python `unittest`](https://docs.python.org/3/library/unittest.html)
- [NIST TN 1297](https://www.nist.gov/publications/guidelines-evaluating-and-expressing-uncertainty-nist-measurement-results-1994-edition)
