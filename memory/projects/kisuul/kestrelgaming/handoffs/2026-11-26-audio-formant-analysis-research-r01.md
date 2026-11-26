---
schema: 1
id: 2026-11-26-audio-formant-analysis-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch a435c790546b7aefc8ba35ba18be1d7c235f916f; Praat Burg and LPC manuals; Vallabha and Tuller (2002); executed pole conversion, AR fit, and sparse-tone checks with NumPy 2.3.5 and SciPy 1.17.0."
---

# Skill 61 research for formant analysis

## Summary

**Task outcome:** COMPLETE

Estimate resonances of the spectral envelope in a declared
speech frame. Keep the excitation, fitted model order,
analysis rate, and frequency ceiling visible. A pole has
an angle and radius. Its value as a formant candidate depends
on the support and the model. The checks recover known poles
and show how a sparse harmonic signal can give unsupported
resonance candidates.
[Praat formant analysis](https://praat.org/manual/Sound__To_Formant__burg____.html)

## Evidence

### Fit and qualify an envelope

Record the tap, sample rate, analysis resampling, frame
center, window, pre-emphasis and prediction order. The
analysis ceiling limits the band used to fit the model.
Record the rate after resampling. Use frames with enough
usable samples and excitation. A periodic source with high
fundamental frequency has widely spaced harmonics. A fitted
peak can follow a harmonic while the true envelope peak
lies between harmonics. Test alternate plausible ceilings
and orders and inspect what changes. Track candidate
continuity without filling frames that lack evidence.
[Vallabha and Tuller (2002), abstract](https://doi.org/10.1016/S0167-6393(01)00049-8) ·
[Analysis support](../../../../../skills/audio-spectrogram-waterfall/references/STFT_WATERFALL_CONTRACT.md#frame-geometry) ·
[Pitch and excitation](2026-11-26-audio-pitch-tracking-research-r01.md)

Declare the sign convention. For a real order-$p$ predictor,
use $e[n]=x[n]+\sum_{k=1}^{p}a_kx[n-k]$ and
$A(z)=1+\sum_{k=1}^{p}a_kz^{-k}$. The all-pole response is
proportional to $1/A(z)$. Find the roots of $z^pA(z)$.
For a conjugate pair with upper root $z=r e^{j\theta}$,
$0<r<1$ and $0<\theta<\pi$, use

$$
f=\frac{f_s\theta}{2\pi},
\qquad
B=-\frac{f_s\log r}{\pi}.
$$

$B$ is the bandwidth parameter implied by pole damping.
The measured width of a peak of the complete response can
also depend on neighboring poles and zeros. Compare the
fitted envelope and peak support as two checks on the root.
Record any reflection or stabilization of invalid roots as
a model change. Use explicit gates for edge frequencies,
tiny or broad bandwidths, low input level, and nearly
singular coefficient fits.
[Praat LPC to formants](https://praat.org/manual/LPC__To_Formant.html)

### Executed checks and portable fixtures

Use 16 kHz. To construct the synthetic AR model, set
$r=\exp(-\pi B/f_s)$ and $\theta=2\pi f/f_s$ for each pair
$(f,B)$ below, include its conjugate, and multiply the
monic factors. The coefficients are in descending powers
of $z$. Treat the generated model as an arithmetic
reference.

| Probe | Verified result |
| --- | --- |
| Use frequency/bandwidth pairs `(550,75)`, `(1550,110)` and `(2600,150)` Hz. Solve the resulting sixth-order polynomial and convert its upper roots. | Maximum absolute error across recovered frequencies and bandwidths was about `8.8e-11` Hz. |
| Drive $1/A$ with 50,000 standard normal samples, NumPy PCG64 seed 610061. Drop the first 2,048 outputs and fit an untapered order-six predictor by least squares. | The estimated frequency/bandwidth pairs were approximately `(550.872,73.343)`, `(1549.834,109.943)` and `(2597.409,152.792)` Hz. |
| Fit the same least-squares rule at order four to 2,048 samples of $\cos(2\pi n/40)+0.3\cos(2\pi n/20)$. | The roots give angles at approximately 400 and 800 Hz, with radii within `1e-10` of unity. The data consist of two tones. The near-zero damping is a cue to withhold a formant interpretation. |

The replay uses NumPy 2.3.5 and SciPy 1.17.0. The known
coefficients qualify the conversion independently of the fit.
The longer white-noise run checks the specified AR model.
Vowel accuracy, short-frame bias, and use with high-pitched
or noisy speech need further evaluation.

## Next action

Implement the coefficient-to-candidate stage with explicit
rate, root, frequency and bandwidth policies. Compare the
roots with a response plot or peak computation. Give Gauge
known poles, sparse excitation, near-unit radii, rate
changes and inadequate frames. Evaluate a pinned LPC
estimator with independent annotated or synthetic speech
before selecting default window and ceiling values.

## Revisit when

The frame geometry, resampling, pre-emphasis, predictor,
order, ceiling, candidate tracking, or speech domain changes.
