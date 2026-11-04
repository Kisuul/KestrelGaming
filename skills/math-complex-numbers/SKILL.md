---
name: math-complex-numbers
description: Work with rectangular and polar complex numbers, conjugates, phasors and Euler exponentials while declaring phase and sign conventions.
---

# Complex numbers — phase without ambiguity

## Activate when

Use for rectangular/polar arithmetic, phasors, oscillations, impedance, complex transforms or planar rotations. Follow the shared [curriculum conventions](../../docs/MATH_CURRICULUM.md). A domain skill owns the measurement model, FFT normalization and calibration.

## Required inputs

Declare `z=a+ib`, `i²=-1`, the units of both components, radians or another explicit angle unit, the phase reference and the physical/geometric meaning. Record dtype/backend, finite-value policy and the chosen branch for argument/log/root/power operations. For measurements supply a magnitude/noise threshold in the same units as `|z|`; an arbitrary numeric epsilon is not a measurement policy.

## Procedure

1. **Check the domain.** Components being added must have compatible units. Handle NaN/Inf according to the declared operation policy rather than allowing a successful round trip to validate them. For division require a nonzero denominator and inspect its scale; do not replace a reliable complex library's scaled division with naïve squared-magnitude arithmetic.
2. **Compute magnitude safely.** Mathematically `r=√(a²+b²)`; numerically prefer a scaled library magnitude such as `hypot(a,b)`. Squaring components or evaluating `z conj(z)` can overflow/underflow even when `r` is representable. Cancellation in sums occurs componentwise; inspect real and imaginary errors separately and use stable accumulation where appropriate. Load [numerical analysis](../math-numerical-analysis/SKILL.md) when scale or cancellation is material.
3. **Decide whether phase is reportable.** For `z≠0`, principal phase is `atan2(b,a)`; for exact zero, mathematical phase is undefined. A measurement may also have unresolved phase at nonzero magnitude below its declared noise/resolution threshold. Require a finite, nonnegative threshold with units and report invalid/unresolved phase explicitly; do not present a library's phase-of-zero convention as a physical observation. A threshold is domain evidence, not a universal constant.
4. **Select and preserve the branch.** Reconstruct with `z=r(cos θ+i sin θ)`. Principal argument jumps at the negative real axis; principal log/root/power inherit branch choices. Python `cmath` uses signed zero to select a side of several cuts. Do not assume `log(z₁z₂)=log(z₁)+log(z₂)` on principal branches or that phase is a globally continuous scalar. Compare directions using a wrapped angular difference when appropriate; unwrapping requires an additional continuity/sampling model.
5. **Fix the exponential sign at the interface.** Multiplication by `e^{+iθ}` rotates the usual `(real,imaginary)` plane counterclockwise by `θ`; `e^{-iθ}` rotates the other way. A phasor convention may choose either time-exponential sign. The domain procedure must declare DFT exponent sign, forward/inverse scaling, frequencies, time origin and one-sided handling before interpreting spectral phase. Complex arithmetic alone cannot choose these.
6. **Verify with independent anchors and boundary cases.** Check a nonzero rectangular/polar example, exact algebra, and a zero/branch/scale negative. A round trip through shared functions tests self-consistency, not an independent convention. For complex errors specify component bounds or `|actual-reference|` explicitly; phase error needs an angular metric and valid magnitude. Use [math verification](../math-verification/SKILL.md) for finite checks and explicit absolute/relative tolerance semantics.

## Worked and adversarial examples

| Input / tempting mistake | Correct decision and independently checkable result |
| --- | --- |
| `z=3+4i` | Pythagoras gives `|z|=5`; `(3+4i)(3-4i)=25`. Polar phase is `atan2(4,3)`, and multiplication by `i` gives `-4+3i`, a positive 90° rotation. |
| Demand exact floating `exp(iπ) == -1` | Euler's identity is exact mathematically; represented `π` and library rounding leave residuals. The fixture uses explicit component comparisons; an absolute-only bound requires `rel_tol=0`, including for the real component near `-1`. |
| `z=10^308 + i10^308`; form `a*a+b*b` | Under binary64 the intermediate squares overflow, although `|z|≈1.4142135623730951×10^308` is representable. Use scaled magnitude; `|z|²` itself is outside the finite range. |
| Report phase `0` for `0j`, or a precise phase below measurement noise | Return undefined/unresolved phase under the stated policy. A mathematical nonzero argument remains defined, but its measurement interpretation can be unreliable. |
| Negative axis, signed imaginary zero | Python gives `phase(complex(-1,+0.0))=+π`, `phase(complex(-1,-0.0))=-π`; `sqrt` selects `+i` and `-i`, respectively. These are branch-side conventions; equality of direction does not make raw phase scalars equal. |
| `θ₁=π-ε`, `θ₂=-π+ε`, `0<ε≪1`; subtract raw phases | Raw difference is nearly `2π`; the shortest directional separation is `2ε`. Use a wrapped difference for direction, and do not infer unwrapped motion from two samples. |
| Principal logarithms of `z₁=z₂=-1+0i` | `Log(z₁)+Log(z₂)=2πi` while `Log(z₁z₂)=Log(1)=0`; principal complex logarithm is not globally additive. |

## Output and acceptance gate

Return component units, representation, exponent sign, branch/range, phase reference and zero/threshold policy; then the result, independent anchor, boundary check and actual error metric/tolerances. Accept only when those choices fit the domain interface and finite results satisfy the specified bounds. The [fixture catalog](../../tests/fixtures/MATH_FOUNDATION_VECTORS.md) checks selected arithmetic and Python branch behavior; it does not verify a domain calibration or every backend's complex semantics.

## References

- [Python `cmath`](https://docs.python.org/3/library/cmath.html) — branch cuts and signed zeros, `phase`, `polar`, `rect`, `sqrt`, `log` and `exp`; inspect the deployed Python version when relying on runtime behavior.
- [Python `math.hypot`](https://docs.python.org/3/library/math.html#math.hypot) — scaled Euclidean magnitude and version-dependent accuracy notes.

**Limits:** this is a procedure for complex arithmetic and conventions, not full complex analysis. FFT normalization, sampling, physical phase resolution and phasor sign remain domain decisions; finite examples do not establish universal numerical accuracy.
