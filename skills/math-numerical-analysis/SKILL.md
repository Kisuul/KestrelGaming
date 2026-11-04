---
name: math-numerical-analysis
description: Diagnose and prevent numerical cancellation, loss of precision, overflow, underflow, unstable algorithms and misleading tolerances in engineering calculations.
---

# Numerical analysis — trustworthy finite arithmetic

## Activate when

Use when implementing or reviewing floating-point calculations, accumulations, logarithmic ratios, solvers, filters, simulation steps, thresholds, fixed-point/binary representations or precision-sensitive tests. Consult [math-verification](../math-verification/SKILL.md) for evidence and [dimensional analysis](../math-dimensional-analysis/SKILL.md) when quantities carry units. Do not load for purely symbolic or unrelated tasks.

## Procedure

1. **Specify mathematical problem and numeric representation.** Define function, input domain, scale, output quantity, acceptable error, input uncertainty and exact-vs-approximate requirements. Distinguish a poorly *conditioned problem* from an *unstable implementation*. Check host rounding, storage type, intermediate precision and range; do not claim universal IEEE 754 behavior.
2. **Separate error sources.** Identify representation/quantization, rounding, input noise, truncation/model approximation and algorithmic convergence. Error propagation can magnify perturbations even if the implementation is stable. State an absolute/relative or ULP-based budget and justify it for each output, including zero.
3. **Avoid cancellation and premature overflow.** Algebraically reformulate when justified; consider `log1p(x)` for `log(1+x)` near zero, `expm1(x)` for `exp(x)-1`, and scaled norms (`hypot`). Accumulate with pairwise/compensated methods where appropriate; do not apply compensators to claim an exact result.
4. **Control domain and scale.** Explicitly handle empty input, ±0, subnormals, NaN, infinities, overflow, underflow and sign. State whether to reject, propagate or flag each. Keep physical quantities and their units explicit until safe conversion. For tiny products, changing multiplication order may affect underflow; for huge squares, rescale before squaring.
5. **Assess conditioning.** For `f(x)` evaluate sensitivity of the *problem* to a small perturbation in `x`. For linear systems check singularity/condition number and residual; small residual alone does not imply a small forward error. Prefer stable library solvers to explicitly computing an inverse.
6. **Design independent checks.** Compare simple analytical cases, exact rationals or high-precision decimal calculations, metamorphic invariants, and boundary/negative cases. Keep the reference independent of the implementation under test where feasible. Record precision, backend, tolerances and observed results.
7. **Report limits.** State precision and domain assumptions, range tested, how tolerances were derived, whether CI ran, and untested extreme values. Pass/fail is per assertion; do not generalize to all inputs or runtimes.

## Worked example

A binary64 evaluation of `(10^16 + 1) - 10^16` rounds the intermediate addition so the result becomes `0` rather than exact `1`. Summing the *three inputs* with `math.fsum([1e16, 1.0, -1e16])` gives `1.0` on a normal Python binary64 runtime. This is an **order/algorithm demonstration**, not a blanket promise for arbitrary precision or platforms. Separately, `math.hypot(1e308, 1e308)` can evaluate a finite magnitude where naïve `sqrt(x*x+y*y)` overflows. For `x=1e-16`, `log(1+x)` and `exp(x)-1` can round to zero in binary64, whereas `log1p(x)` and `expm1(x)` retain a result near `x`.

## Acceptance gate

The computation's quantity/domain/representation are explicit; at least one independently derived reference and a scale-sensitive negative case are exercised; error thresholds are defensible; nonfinite values have a defined policy; claims are bounded to the tested environment. Use [frozen math fixtures](../../tests/fixtures/MATH_FOUNDATION_VECTORS.md).

## References

- [Python `math` functions](https://docs.python.org/3/library/math.html) — `fsum`, `hypot`, `log1p`, `expm1`, `isclose`.
- [Python floating-point tutorial](https://docs.python.org/3/tutorial/floatingpoint.html) — representation and rounding.
- [NumPy linear algebra conditioning](https://numpy.org/doc/stable/reference/generated/numpy.linalg.cond.html) — condition numbers, backend conventions.

**Limitations:** examples assume a binary floating-point runtime; no performance or compliance standard is certified.
