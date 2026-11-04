# Core mathematics — analytic fixture derivations (2026-11-03)

These are small, deliberately independent mathematical references for the [six skills](../../docs/MATH_CURRICULUM.md), not third-party conformance vectors. Python tests are in `tests/test_math_foundations.py`. A test passing means only that its recorded assertion held in that runtime.

| ID | Input | Expected / derivation | Covers |
| --- | --- | --- | --- |
| NUM-01 | Binary64 `(1e16+1)-1e16`; compensation over list `[1e16,1,-1e16]` | Expression rounds to `0`; `fsum` of the three representable values is `1` | Cancellation/compensated accumulation |
| NUM-02 | Euclidean norm of `[1e308,1e308]` | `sqrt(2)*1e308` is finite in binary64; naïve intermediate squaring overflows | Scaling |
| DIM-01 | `1000` samples at `48000` samples/second | `1000/48000=1/48` second, exact rational conversion | Rate dimensions |
| DIM-02 | acceleration `L T^-2` times mass `M` | force `M L T^-2` | Dimensional exponents |
| LIN-01 | `A=[[3,1],[1,2]], b=[9,8]` | determinant `5`, `x=2` and `y=3` by Cramer's rule, `Ax=b` | Solves and residual |
| LIN-02 | `A=[[1,2],[2,4]]` | determinant `0`, not invertible | Singular negative case |
| CMP-01 | `3+4i` | modulus `5` and `z conj(z)=25`, by Pythagoras | Polar/complex algebra |
| CMP-02 | `e^{iπ}` | exact mathematical value `-1`; finite arithmetic approximates | Euler phase |
| STA-01 | `[1,2,3,4,5]` | mean `3`; sum of squared deviations `10`; sample variance `10/(5-1)=2.5`; SEM under iid assumption `sqrt(0.5)` | Estimator semantics |
| STA-02 | Uniform independent replacement draws from `{0,1}`, sample size 2 | Enumerate `00,01,10,11`: sample variances `0,1/2,1/2,0`, expectation `1/4` equals population variance | Unbiasedness under specified model |
| VER-01 | `1/3 + 1/6` rational | exactly `1/2` | Exact oracle |
| VER-02 | Rotate `(3,4)` by 90° | approximately `(-4,3)` with unchanged Euclidean length 5 | Geometric metamorphic check |

The probability example `STA-02` assumes **independent draws with replacement** and the equal-probability two-point distribution; the expectation is not a claim for arbitrary sampling. Linear-algebra negatives here show algebraic singularity, **not** generic floating solver failure detection.

**Tolerances:** exact rationals and integer dimensions are compared exactly. Trigonometric/complex and large floating results use finite-value checks and tight, documented `isclose` bounds appropriate for these toy values. No tolerance in this file is an engineering acceptance threshold for arbitrary data.

**Primary specifications:** [Python math](https://docs.python.org/3/library/math.html), [Python fractions](https://docs.python.org/3/library/fractions.html), [Python statistics](https://docs.python.org/3/library/statistics.html), [BIPM SI](https://www.bipm.org/en/publications/si-brochure/).
