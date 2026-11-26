---
schema: 1
id: 2026-11-26-audio-pitch-tracking-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 327ca13df3cef9193599762685f1350ae4df6900; de Cheveigne and Kawahara (2002), Mauch and Dixon (2014), mir_eval melody documentation; executed harmonic, interpolation, and direct/FFT difference checks below."
---

# Skill 39 research for pitch tracking

## Summary

**Task outcome:** COMPLETE

Start with monophonic fundamental frequency ($F_0$) candidates from
fixed-support lag differences. Declare the voicing policy separately
from period selection. Preserve candidate lags and frame support.
Use harmonic analysis to check an ambiguous candidate. The checks
include a missing fundamental, an even-harmonic ambiguity, a
fractional period and a DC-only frame.
[Harmonic analysis](../../../../../skills/audio-harmonic-analysis/SKILL.md)

## Evidence

### State the periodic signal model

For a periodic model, $F_0$ is the reciprocal of the shortest
supported repeating period. The strongest spectral partial can be
several multiples of $F_0$. When only even harmonics of a proposed
period occur, the shorter period also fits the observed signal.
Report what the signal supports and keep prior information about
the source visible. A single monophonic estimate cannot represent
multiple independent pitches in a mixture.
[YIN, §§II–III](https://www.ee.columbia.edu/~dpwe/e6820/papers/deChevK02-yin.pdf)

Declare the tap, sample rate, channel and input gain. Use complete
frames with an exact sample range and center. An integer-only search
for $f_{\min}\le F_0\le f_{\max}$ has lags from
$\lceil f_s/f_{\max}\rceil$ through $\lfloor f_s/f_{\min}\rfloor$.
Choose a fixed comparison span $W$ and read at least
$W+p_{\max}$ samples. Allow guard lag samples if the search includes
edge interpolation. Impose the frequency range on the final estimate.
At 48 kHz and $f_{\min}=50$ Hz, $p_{\max}=960$ samples. A 1,024-sample
frame then leaves only 64 samples of fixed comparison support. An
implementation can produce a number with that support even when the
evidence is weak. Verify low-frequency coverage over plausible clip
lengths and state the cost in latency.
[Complete-frame geometry](../../../../../skills/audio-spectrogram-waterfall/references/STFT_WATERFALL_CONTRACT.md#frame-geometry)

### Compare lags and qualify candidates

For the bounded baseline, use a fixed, untapered comparison.

$$
d(p)=\sum_{n=0}^{W-1}(x[n]-x[n+p])^2,\qquad
d'(p)=\frac{p\,d(p)}{\sum_{i=1}^{p}d(i)}\quad(p>0).
$$

The normalization needs lags starting at 1, even when the pitch
search starts higher. Define the convention at lag zero separately.
If the cumulative denominator is zero, record unsupported
periodicity. Silence and constant input give zero differences at
all lags. Gate low AC level with a declared measurement and keep
constant nonzero PCM distinct from observed silence.

Collect threshold-qualified local troughs in the search range.
Try the first supported trough, with a declared plateau and endpoint
policy. Log runner-up lags, trough depths, and harmonic evidence
for decisions about an octave. The YIN paper uses a global minimum
fallback when no trough passes. Label that fallback separately if
offered and give the caller an unvoiced or ambiguous state. Trough
depth is a periodicity measure. Calibrated voicing probabilities
require an additional model and evaluation.
[YIN, §§II.B–E](https://www.ee.columbia.edu/~dpwe/e6820/papers/deChevK02-yin.pdf)

For an interior convex trough with neighbors $y_-,y_0,y_+$, a
parabolic fit gives
$\delta=(y_--y_+)/[2(y_--2y_0+y_+)]$. Verify curvature, support and
the fitted period before using $f_s/(p+\delta)$. Specify whether
the fit uses $d$ or $d'$ and check its bias at fractional periods.
Within finite arithmetic, subtract samples before squaring or scale
the entire comparison consistently. An FFT equivalent uses
$d(p)=P_0+P_p-2R(p)$ with both energies and the linear cross-product
over the same $W$ pairs. Zero-pad for a linear correlation and check
near-zero differences where cancellation matters.
[Linear correlation](../../../../../skills/audio-cross-correlation/references/CROSS_CORRELATION_CONTRACT.md#verify-fft-and-refinements) ·
[Numerical stability](../../../../../skills/audio-numerical-stability/SKILL.md)

### Keep tracking and evaluation explicit

An isolated estimate can change octave or vanish during a transient.
A tracker may use candidate history, a maximum plausible transition,
or an unvoiced state. pYIN models candidate probabilities and uses
Viterbi decoding across frames. For live use, declare the commitment
delay, state reset, and revision policy. Test abrupt pitch leaps and
two recordings with the same available prefix. Mark gaps and
incomplete frames as unavailable. A supported aperiodic frame is
unvoiced under the selected model.
[Mauch and Dixon (2014), §§2.1–2.2](https://webspace.eecs.qmul.ac.uk/s.e.dixon/pub/2014/MauchDixon-PYIN-ICASSP2014.pdf)

Check voicing recall and false alarms in addition to frequency
errors. Use signed cents $1200\log_2(f_{\mathrm{est}}/f_{\mathrm{ref}})$
for matched positive values. Score octave-sensitive agreement
separately from pitch-class agreement. State time alignment,
tolerance, labeled coverage and input conditions. The mir_eval
melody metrics default to 50 cents. Use a tighter declared tolerance
if the application needs a tuner or calibration measurement.
[mir_eval melody](https://mir-eval.readthedocs.io/stable/api/melody.html)

### Executed checks and portable fixtures

Use 48 kHz, 1,200 samples, $W=960$, and integer lags 48–240 for
the first four rows. Periodic examples may repeat a 120-sample
base array. Select the first interior trough below 0.1 of $d'$.

| Probe | Verified result |
| --- | --- |
| $x[n]=0.3\cos(4\pi n/120)+0.2\cos(6\pi n/120)$. | $d(40)/W=0.135$, $d(60)/W=0.08$, and $d(120)=0$. The first qualified trough is lag 120 (400 Hz), even though the two components are 800 and 1,200 Hz. |
| Keep only the 800 Hz component in that frame. | The first qualified trough is lag 60 (800 Hz). The 400 Hz interpretation requires additional evidence. |
| Use constant 0.125 PCM. Repeat the first probe with $0.5-2x[n]$. | Constant input has a zero denominator throughout. The affine transform leaves the supported $d'$ curve unchanged within `1e-14`. Check the level gate separately. |
| Use $0.4\cos(2\pi 437.5n/48000)$ and fit $d'$ at and around its integer trough. | The trough is 110 samples. The fit gives 437.51494 Hz, about +0.05912 cents. The exact target lag is $768/7$. |

For an independent arithmetic comparison draw uniform `[-1,1)`
samples using NumPy 2.3.5 PCG64 seed 390039. Use $(W,p_{\max})$
of `(96,120)`, `(129,91)`, `(192,128)`, and `(257,199)` in that
order, with $W+p_{\max}$ samples each. Use a transform length at
least the linear correlation length. The FFT/energy identity and
direct paired differences agreed to `1.43e-13` squared-PCM sum
units across 542 lags. Music, voicing calibration and live
commitment need their own evaluation.

## Next action

Implement a bounded candidate extractor with exact sample support,
explicit level and threshold policies, and reported competing lags.
Test silence, DC, a missing fundamental, a two-source mixture,
interpolation at both search edges, and stream reset. Add continuity
only with testable rules for voicing, transients, pitch leaps and
delivery delay.

## Revisit when

The pitch range, window, voicing policy, tracking delay, source mix
or target cents tolerance changes.
