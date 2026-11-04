# Core mathematics — reference fixtures

These bounded examples support the [six procedural skills](../../docs/MATH_CURRICULUM.md).
The [executable suite](../test_math_foundations.py) exercises Python's standard library
and test-local policy helpers. It supplies no production units engine, solver or agent
runtime. Follow the [fixture policy](../../skills/math-verification/references/FIXTURE_POLICY.md).

## Representation and comparisons

Floating examples target binary64, round-to-nearest, with gradual underflow. The
runtime test checks radix 2, significand 53, maximum exponent 1024 and reported
rounding mode 1; NUM-05 checks the smallest subnormal. This explicit target does not
establish compatibility with every Python implementation or backend. Exact rational
references use `Fraction`. Decimal contexts are specified below. Unlabelled arithmetic
is dimensionless, phase angles are radians, and dimension vectors have seven SI base
exponents in curriculum order. Matrices use column vectors.

For approximate comparisons, `(r,a)` below means Python's symmetric rule
`abs(actual-reference) <= max(r*max(abs(actual),abs(reference)),a)`.
The absolute bound `a` has the result's units; `r` is dimensionless. Equality means
exact Python equality. The margins are fixture-specific engineering choices, not
proved libm bounds or universal tolerances. The near-zero case demonstrates the need for an absolute floor. The deliberately
defaulted Euler negative comparison demonstrates a trap, not acceptance policy.

## Numbered cases

Methods have the corresponding `test_numNN_`, `test_dimNN_`, `test_linNN_`,
`test_cmpNN_`, `test_staNN_` or `test_verNN_` prefix, except VER-03, whose full name
is `test_explicit_nonfinite_comparison_gate`. Additional methods follow in the next table.

| ID | Input and mathematical contract | Reference / derivation and acceptance | Negative case or limit |
| --- | --- | --- | --- |
| NUM-01 | Represented values `[1e16,1,-1e16]` | Integer/rational sum exactly 1; `fsum` equals 1 | Sequential expression equals 0; not exact recovery of arbitrary real inputs |
| NUM-02 | Norm of two-component `[1e308,1e308]` | Pythagoras: finite `sqrt(2)*1e308`; `(2e-15,0)` | Naive square is infinite; reference shares `math.sqrt`, not independent libm certification |
| NUM-03 | `x=1e-16`, `log(1+x)` and `exp(x)-1` | Taylor expansion gives `x+O(x*x)`; stable functions versus `x` with `(1e-15,0)` | Both naive expressions round to zero in target runtime |
| NUM-04 | `sqrt(1+x)-1`, represented `x=1e-16` | Rationalized `x/(sqrt(1+x)+1)`; `Decimal.from_float(x)`, precision 80, decimal square root reference; `(1e-15,0)` | Naive result 0; independent decimal reference positive but finite-precision |
| NUM-05 | Underflow regrouping and smallest subnormal | `(1e-200*1e-200)*1e200=0`; regrouped product versus `1e-200` with `(1e-15,0)`; exact `Fraction(math.ulp(0))=2^-1074` | Half smallest subnormal rounds to 0, doubling stays nonzero; regrouping is specific to these inputs |
| DIM-01 | `1000 samples / (48000 samples/s)` | Exact `1/48 s`; display `0.0208333333333333 s` with `(0,4e-17 s)` | Nominal fixed rate, not clock calibration |
| DIM-02 | Acceleration `(1,0,-2,0,0,0,0)` times mass `(0,1,0,0,0,0,0)` | Guarded component addition gives exact force `(1,1,-2,0,0,0,0)` | Shape negatives in supplementary table |
| DIM-03 | Temperature points `0 °C`, `100 °C` | Decimal offset `273.15`: `273.15 K`, `373.15 K`, interval `100 K`, exact in default precision 28 | No production point/interval type is implemented |
| DIM-04 | Positive amplitude ratio 2 and related power ratio 4 | `20 log10(2)` versus `10 log10(4)` with `(1e-15,0 dB)`; versus `6.020599913279624 dB` with `(0,2e-15 dB)` | Requires square-law model and compatible references; shared log kernel limits independence |
| LIN-01 | `A=[[3,1],[1,2]], b=[9,8]` | Exact determinant 5, solution `(2,3)` and separately substituted `Ax=b` | Cramer's rule is a tiny rational oracle, not production solver advice |
| LIN-02 | `A=[[1,2],[2,4]]` | Exact determinant 0 from dependent rows | Tests algebraic singularity, not numerical rank detection |
| LIN-03 | `A=diag(1,epsilon)`, `epsilon=10^-12`, `b=(1,epsilon)`, true `(1,1)`, candidate `(1,0)` | Exact infinity-norm residual `epsilon`, forward error 1, condition `1/epsilon`, normalized backward residual `epsilon/2` | Small residual hides large error; no floating solver exercised |
| CMP-01 | `z=3+4i` | Exact modulus 5 and conjugate product 25; polar round-trip components `(1e-14,0)` | Pythagoras is an anchor; round trip alone is self-consistency |
| CMP-02 | Mathematical `exp(i*pi)=-1` | Finite real component versus -1 with `(0,1e-14)` and imaginary versus 0 with `(0,2e-15)` | Represented pi and libm residuals; shared assertion is challenged below |
| CMP-03 | `complex(-1,+0.0)`, `complex(-1,-0.0)` | Python phase exactly `+math.pi` and `-math.pi` | Runtime branch-side convention, not universal principal range |
| STA-01 | `[1,2,3,4,5]` | Mean 3, squared deviations 10, sample variance 2.5, population-form variance 2; iid-assumed SEM versus `sqrt(0.5)` with `(0,1e-15)` | Original units for mean/SEM, squared units for variance; data do not establish iid |
| STA-02 | Two independent equiprobable replacement draws from `{0,1}` | Exact four variances `0,1/2,1/2,0`, expectation `1/4` | Complete enumeration verifies this finite model only |
| STA-03 | Equiprobable `Y=-1,+1`; observe dependent pair `(Y,Y)` | Each sample variance 0; exact variance of sample means 1 | Differs from iid known-variance result `1/2`; repeated readings do not prove certainty |
| VER-01 | Rational `1/3+1/6` | Exactly `1/2` | Exact rational anchor, not an external implementation comparison |
| VER-02 | Rotate `(3,4)` through `pi/2` | Analytic `(-4,3)`; finite components `(0,2e-15)` and norm `(2e-15,0)` | Analytic anchor plus metamorphic norm, not norm alone |
| VER-03 | Test-local finite comparison gate | Finite 1 succeeds with `(1e-12,0)` | NaN and either infinity raise `ValueError` before `isclose` |

## Supplementary methods

Together the two tables account for all 31 mathematics tests. The helpers live only
in the test file and are not exported application behavior.

| Full test method | Inputs, contract, derivation and acceptance | Negative / scope |
| --- | --- | --- |
| `test_binary64_prerequisites` | `sys.float_info`: exact `(radix,mant_dig,max_exp,rounds)=(2,53,1024,1)` | Fail for a different declared floating target |
| `test_absolute_floor_is_required_near_zero` | `1e-12` versus 0 fails relative `1e-6`, succeeds with absolute `1e-11` | NaN is not close to itself; demonstrates near-zero floor |
| `test_decimal_reference_is_not_binary_float` | Decimal strings `0.1+0.2=0.3`, context precision 30, exact | Binary expression differs from binary 0.3; not a general accuracy ranking |
| `test_incompatible_dimensions_rejected_in_reference_gate` | Canonical length `2+3=5`; length plus duration raises `ValueError`; matching malformed two-entry dimensions also raise | Guard assumes compatible quantity kind and canonical scale; does not test kind or unit conversion |
| `test_malformed_dimension_vectors_rejected_before_zip` | Empty, six-entry and eight-entry vectors against valid and equally malformed operands; every order raises `ValueError` | Tests length, not finite/type validation of exponent values |
| `test_transform_order_is_not_interchangeable` | `A` scales x by 2, `B` rotates 90°; column vector `(1,0)` | Exact `ABx=(0,1)` versus `BAx=(0,2)` |
| `test_euler_absolute_budget_rejects_default_relative_tolerance_trap` | Shared CMP-02 assertion rejects real `-1+5e-10`, imaginary `3e-15`, NaN or infinity | Old default relative tolerance admits wrong real value; regression protects actual CMP-02 gate |
| `test_phase_of_zero_not_used_as_measurement` | Test-local `phase_or_none(0j)` is `None`; phase of `3+4j` versus `atan2(4,3)` with `(1e-15,0 rad)` | Shared-kernel check, not a calibrated measurement threshold |
| `test_sample_variance_requires_two_observations` | Single observation `[7]` | `statistics.variance` raises `StatisticsError` |
| `test_near_singular_rounding_is_distinct_from_exact_math` | Exact matrix `[[1,1],[1,1+2^-53]]` has determinant `2^-53`; represented `1+2^-53` rounds to 1 | Floating determinant 0: representation changed the input problem |

## Execution and limitations

The completion run uses CPython 3.12.14 on Linux. The
[completion handoff](../../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-03-math-package-completion-r02.md)
records actual commands, results and revision provenance. Earlier unsupported
local-run claims remain retracted in the
[historical audit](../../memory/projects/kisuul/kestrelgaming/2026-11-03-math-skills-independent-audit.md).
CI uses the runner's system Python; there is no cross-runtime matrix.

Not every prose example has an automated check: quantity kinds, invalid dB references,
clock errors, decompositions, inference coverage and measurement thresholds need
task-specific evidence. The [behavioral scenarios](../../kestrel/evals/MATH_SCENARIOS.md)
specify agent-level checks, explicitly unexecuted until an independent harness records
trials. Reference fixture passes do not establish host activation, skill effectiveness,
production implementation correctness, formal proof, calibration or standards conformance.

## Sources

[Python 3.12 math](https://docs.python.org/3.12/library/math.html),
[cmath](https://docs.python.org/3.12/library/cmath.html),
[statistics](https://docs.python.org/3.12/library/statistics.html),
[fractions](https://docs.python.org/3.12/library/fractions.html),
[decimal](https://docs.python.org/3.12/library/decimal.html) and
[float_info](https://docs.python.org/3.12/library/sys.html#sys.float_info)
define demonstrated API semantics.
[BIPM SI Brochure, 9th edition](https://www.bipm.org/en/publications/si-brochure/)
supplies quantity/unit conventions, not fixture conformance certification.
