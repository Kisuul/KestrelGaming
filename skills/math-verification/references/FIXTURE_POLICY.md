# Mathematical fixture and independent-oracle policy

Apply this policy when using [math-verification](../SKILL.md). The [fixture catalog](../../../tests/fixtures/MATH_FOUNDATION_VECTORS.md) maps the included examples to their executable assertions; it is not a production API specification.

## Minimal fixture record

Record the following directly or by an explicit shared convention, without inventing absent evidence:

| Field | Required content |
| --- | --- |
| Identity and claim | Stable fixture ID, purpose, mapped test name and the specific mathematical/runtime claim |
| Contract | Domain, units or dimensionless kind, shape/order, normalization, boundary and failure semantics |
| Input | Exact literals or generation rule; distinguish intended decimal values from represented binary inputs |
| Expected output | Value/property and an independently checkable derivation or a pinned source/version/configuration |
| Oracle | Arithmetic type, precision/context, shared dependencies and expected uncertainty/error where known |
| Comparator | Exact equality or explicit metric, both relative and absolute terms, units, finite policy and rationale |
| Falsification | Plausible wrong result or boundary that must fail; identify when a shared negative fixture supplies this check |
| Execution | Exact command, checked revision/source state, runtime/backend version and observed result; otherwise NOT RUN |

An unmeasured bound is **unknown**, not zero. A locally edited source state may be described by its starting commit and diff; it is not the unchanged commit. A subsequent memory-only commit does not retroactively become the tested revision. Historical execution logs can remain in a linked handoff rather than being copied into every fixture row.

## Oracle selection and dependence

| Oracle | Useful evidence | Shared assumption or limitation to report |
| --- | --- | --- |
| Hand algebra / symbolic derivation | Small exact examples, dimensions, identities | Arithmetic/transcription can be wrong; review a second way |
| `Fraction` from integers or strings | Exact rational reference values | Repeating the same wrong formula is still wrong; constructing from float exactly preserves its prior rounding |
| `Decimal` from strings with explicit context | Decimal inputs and higher-precision rounding checks | Finite context and rounding remain; `Decimal(float)` imports the binary value; decimal transcendental error is not automatically zero |
| Different numerical algorithm/library | Differential implementation check | Inspect shared kernels, normalizations and copied formulas; agreement is not proof |
| Published normative/reference vector | A specified convention and domain | Pin edition, input/output encoding, method and applicability; a tutorial is not a conformance suite |
| Metamorphic property | Relationships across inputs when exact answers are difficult | State prerequisites; several wrong algorithms may satisfy the same property |
| Round trip or own residual | Internal consistency and some integration faults | Matching errors can cancel; not an independent oracle and may not constrain forward error |

For a high-impact claim, combine evidence that fails differently. Exact `Ax=b` substitution and a separately derived solution are stronger together than two residual implementations. For an FFT, matching inverse/forward normalization can conceal an incorrect amplitude convention. Domain skills must supply calibration and sampling contracts.

## Exact comparison semantics

**Exact integers/rationals:** require equality for the specified arithmetic. A floating approximation equal to a rounded expected literal is not an exact-real proof.

**Finite scalar approximations:** choose an application metric. If using Python `math.isclose`, acceptance is

`abs(actual-expected) <= max(absolute, relative*max(abs(actual),abs(expected)))`.

`absolute` has the output's units; `relative` is dimensionless. This **max** rule is not the additive rule used by some other APIs. Specify both values at every assertion: `rel_tol=0` for absolute-only, `abs_tol=0` for relative-only. Python's default relative term is `1e-9`, so supplying only `abs_tol=1e-14` does not enforce an absolute-only threshold near magnitude `1`. In particular, an error of `5e-10` near `-1` passes that default call and must fail an absolute-only `1e-14` contract. When the expected value is exactly zero, a pure relative test rejects nonzero results for `relative<1`; choose a justified absolute floor when nonzero error is allowed.

**Nonfinite and signed-zero policy:** finite-output contracts must check finiteness before comparison. Python equates like-signed infinities under `isclose`; NaN is never close, including to itself. If infinity is expected, check sign/value explicitly. Ordinary equality treats signed zeros as equal; branch-sensitive interfaces need an additional sign check. An API's returned phase at zero does not establish a physical phase.

**Vectors/complex values:** validate equal shape before iteration; `zip` alone silently drops trailing entries. Declare componentwise or normwise comparison, the chosen norm and scaling, and whether component tolerances have distinct units. Norm preservation does not check orientation. A threshold for one scalar does not automatically bound a vector norm.

**ULP comparisons:** document representation, rounding and a tested distance convention across signs, zero, subnormals and exponent boundaries; reject nonfinite values unless expressly expected. `ulp(expected)` changes with magnitude, so a multiple of it is a local spacing budget, not a universal relative-error bound. Use ULP gates for appropriate representation/API contracts, not as a substitute for physical uncertainty or conditioning analysis.

## Choosing and reviewing tolerances

Derive deterministic thresholds from the numerical method, input scale, conditioning, truncation and oracle error when possible. Combine compatible worst-case bounds without double counting. Where the included small transcendental examples use empirical margins instead, label them **fixture-specific heuristics**, identify the tested runtime and do not generalize them into universal error bounds. An oracle with unknown error cannot certify a tighter implementation bound merely by agreement.

Before accepting a comparator, test one clearly valid result and a plausible invalid result through it. Exact threshold-boundary tests must account for representation of the boundary itself. Keep a deliberately wrong algorithm/result separate from the implementation and freeze expected rejection before seeing its output.

For statistical checks, fix the sampling model, seed where applicable, sample count, acceptance probability, repeated-testing policy and deterministic alternatives. A fixed seed supplies reproducibility, not distributional validity. Treating correlated observations as iid is a model error that a tighter floating tolerance cannot repair.

## Evidence layers and scope

The included Python standard-library tests check selected arithmetic claims and small test-local policy examples. Those helpers are not exported production validators. Structural validation checks links and metadata, not mathematics. An independent application comparison requires a separate implementation; integration requires application-level cases; skill effectiveness requires agent-level trials. Record each separately and leave unexecuted layers explicit. A passing educational fixture is not IEEE, ISO, IEC, ITU, W3C or instrument conformance.

## Technical sources

- [Python `math.isclose`](https://docs.python.org/3/library/math.html#math.isclose)
- [Python `fractions`](https://docs.python.org/3/library/fractions.html)
- [Python `decimal`](https://docs.python.org/3/library/decimal.html)
- [Python `unittest`](https://docs.python.org/3/library/unittest.html)
- [NIST TN 1297, 1994 edition](https://www.nist.gov/pml/nist-technical-note-1297)
