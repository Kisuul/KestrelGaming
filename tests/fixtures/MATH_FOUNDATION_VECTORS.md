# Core mathematics — analytic fixture derivations (2026-11-03)

These are small, deliberately independent mathematical references for the [six skills](../../docs/MATH_CURRICULUM.md), not third-party conformance vectors. Python tests are in `tests/test_math_foundations.py`. A test passing means only that its recorded assertion held in that runtime.

| ID | Input | Expected / derivation | Covers |
| --- | --- | --- | --- |
| NUM-01 | Binary64 `(1e16+1)-1e16`; compensation over list `[1e16,1,-1e16]` | Expression rounds to `0`; `fsum` of the three representable values is `1` | Cancellation/compensated accumulation |
| NUM-02 | Euclidean norm of `[1e308,1e308]` | `sqrt(2)*1e308` is finite in binary64; naïve intermediate squaring overflows | Scaling |
| NUM-03 | `x=1e-16`, `log(1+x)` and `exp(x)-1` | Naïve binary64 evaluates zero; `log1p(x)` and `expm1(x)` are approximately `x` | Small-argument stability |
| DIM-01 | `1000` samples at `48000` samples/second | `1000/48000=1/48` second, exact rational conversion | Rate dimensions |
| DIM-02 | acceleration `L T^-2` times mass `M` | force `M L T^-2` | Dimensional exponents |
| DIM-03 | Temperature points `0 °C` and `100 °C` | `273.15 K` and `373.15 K`; difference `100 K` | Affine units |
| DIM-04 | Referenced amplitude ratio `2`, related power ratio `4` | `20 log10(2) = 10 log10(4) ≈ 6.020599913279624 dB` | Log ratios |
| LIN-01 | `A=[[3,1],[1,2]], b=[9,8]` | determinant `5`, `x=2` and `y=3` by Cramer's rule, `Ax=b` | Solves and residual |
| LIN-02 | `A=[[1,2],[2,4]]` | determinant `0`, not invertible | Singular negative case |
| CMP-01 | `3+4i` | modulus `5` and `z conj(z)=25`, by Pythagoras | Polar/complex algebra |
| CMP-02 | `e^{iπ}` | exact mathematical value `-1`; finite arithmetic approximates | Euler phase |
| CMP-03 | Negative real axis with signed imaginary zero | Python `cmath.phase(-1+0j)=+π`, phase with `-0j` imaginary component is `-π` | Principal branch |
| STA-01 | `[1,2,3,4,5]` | mean `3`; sum of squared deviations `10`; sample variance `10/(5-1)=2.5`; SEM under iid assumption `sqrt(0.5)` | Estimator semantics |
| STA-02 | Uniform independent replacement draws from `{0,1}`, sample size 2 | Enumerate `00,01,10,11`: sample variances `0,1/2,1/2,0`, expectation `1/4` equals population variance | Unbiasedness under specified model |
| VER-01 | `1/3 + 1/6` rational | exactly `1/2` | Exact oracle |
| VER-02 | Rotate `(3,4)` by 90° | approximately `(-4,3)` with unchanged Euclidean length 5 | Geometric metamorphic check |
| VER-03 | Compare `NaN` or `±Inf` | Test-local finite-value guard rejects them before `isclose` | Invalid result policy |

**Provenance and scope:** Core expected values come from integer/rational algebra, small exhaustive enumeration, trigonometric identities or Taylor expansions; `math`, `cmath` and `statistics` are the standard-library behavior being demonstrated. These are NOT comparisons against a separate implementation of a Kestrel production numerical algorithm. Independent arithmetic spot-checks on 2026-11-03 reproduced the key values for NUM-01/02/03, DIM-01/03/04, LIN-01, CMP-02 and STA-02. Earlier claims of a separate local run of the entire committed test file were unsupported and retracted.

The fixture IDs correspond to `test_numNN_`, `test_dimNN_`, `test_linNN_`, `test_cmpNN_`, `test_staNN_` and `test_verNN_` methods in [the test suite](../test_math_foundations.py). Additional tests show boundary policies and invariants; their small policy helpers are defined inside tests, not exported as production code. CI uses the Ubuntu runner's system Python without pinning or reporting the exact Python patch version. This suite does not establish support across all Python 3.9+ versions or non-Python backends.

The probability example `STA-02` assumes **independent draws with replacement** and the equal-probability two-point distribution; the expectation is not a claim for arbitrary sampling. Linear-algebra negatives here show algebraic singularity, **not** generic floating solver failure detection.

**Tolerances:** exact rational and dimensional-exponent cases use exact equality. NUM-02 uses relative `2e-15`; NUM-03 relative `1e-15`; DIM-01 absolute `4e-17`; DIM-04 relative `1e-15` and absolute `2e-15`; CMP-01 relative `1e-14`; CMP-02 absolute `1e-14` (real) and `2e-15` (imaginary); VER-02 absolute `2e-15` for components and relative `2e-15` for norm. Inspect the [exact assertions](../test_math_foundations.py) for guard-specific comparisons. These bounds are specific to the fixture inputs; they are not justified universal error bounds for other data or libraries.

**Primary specifications:** [Python math](https://docs.python.org/3/library/math.html), [Python fractions](https://docs.python.org/3/library/fractions.html), [Python statistics](https://docs.python.org/3/library/statistics.html), [BIPM SI](https://www.bipm.org/en/publications/si-brochure/).
