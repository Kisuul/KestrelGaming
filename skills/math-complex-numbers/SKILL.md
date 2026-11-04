---
name: math-complex-numbers
description: Work with rectangular and polar complex numbers, conjugates, phasors and Euler exponentials while declaring phase and sign conventions.
---

# Complex numbers — phase without ambiguity

## Activate when

Use for Fourier-domain arithmetic, phasors, impedance, oscillations, analytic signals, complex transforms or 2D rotations represented by complex multiplication. This skill provides arithmetic, **not** a DFT normalization or a signal-processing convention.

## Procedure

1. Declare `z=a+ib` with `i²=-1`, and phase angle unit (radians by default). Define whether the representation denotes a value, phasor, sampled spectrum or geometric rotation.
2. Convert with `r=sqrt(a²+b²)` and `θ=atan2(b,a)` (principal branch); reconstruct with `z=r(cos θ+i sin θ)`. Prefer scaled magnitude (`hypot`) for extreme values; phase of zero is undefined, not a measured zero.
3. For products/magnitudes, use `z conj(z)=|z|²` when numerically safe; explain branch cuts for logarithms, roots and complex powers.
4. For frequency-domain work, declare exponent sign (`e^{-i2πkn/N}` or opposite), forward/inverse scaling, bin frequencies, sample origin, one-sided/two-sided handling and phase reference in the *domain* skill. Never invent an FFT calibration here.
5. Test rectangular/polar round trips away from the zero singularity, conjugate symmetry only for real-input transforms under matching conventions, and analytic values from independent calculations.

## Worked example

`z=3+4i` has magnitude `5` and `z conj(z)=25`; angle is `atan2(4,3)`. Euler's identity gives `e^{iπ}=-1` mathematically; a floating computation returns a tiny residual imaginary component, not an exact zero. On the negative real axis, signed imaginary zero affects Python's principal phase: `cmath.phase(complex(-1, +0.0))=+π`, while `cmath.phase(complex(-1, -0.0))=-π`.

## Acceptance gate

Sign, units and phase origin are declared; values near axes and zero are covered; reference examples match analytic identities with explicit tolerances.

## References

- [Python `cmath`](https://docs.python.org/3/library/cmath.html) — branches, phase, polar, rect and exp.
- [SciPy FFT reference](https://docs.scipy.org/doc/scipy/reference/fft.html) — transform conventions when a DSP-specific procedure needs them.

**Limits:** phasor sign and FFT scaling are application conventions; no generic complex-number rule alone resolves them.
