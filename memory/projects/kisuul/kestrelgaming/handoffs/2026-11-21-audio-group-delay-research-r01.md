---
schema: 1
id: 2026-11-21-audio-group-delay-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-21
updated: 2026-11-21
sources: "Kestrel audio branch 67a09a8657fff5f28cf8509fe49f0060ff6ac5fe, Smith's Introduction to Digital Filters, MIT 6.011 notes, Audio Precision TN138, Keysight group-delay guidance, REW group-delay help, SciPy 1.17.0, and executed synthetic and Kestrel reference checks."
---

# Skill 35 research for audio group delay

## Summary

**Task outcome:** COMPLETE

For `audio-group-delay`, start with the phase slope of a known filter. Verify
the sign and units against a pure delay. Then estimate the slope of a sampled
complex transfer only where the phase and frequency support justify it.
Keep the timing reference, usable frequency intervals, and slope aperture
with the curve. A coarse grid can report a consistent delay with the wrong
sign. A stencil that crosses a response null can report a spike where each
valid side has constant group delay.

Use [Skill #33 phase and coherence](../../../../../skills/audio-phase-coherence/SKILL.md)
for the phase of matched PCM segments, and use
[Skill #34 cross-correlation research](https://github.com/Kisuul/KestrelGaming/blob/9f49cc12ea21a25405986b1f5ca70e61e5c28d84/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-21-audio-cross-correlation-research-r01.md)
for a bounded delay check between named taps.
[Curriculum ledger](2026-11-17-audio-curriculum-status-r01.md)

## Evidence

### Define the slope and its timing reference

Let $H(e^{j\omega})$ be the complex measurement-over-reference transfer under
the negative-exponent DFT convention. Let $\phi$ be its phase in radians on
a continuous branch where $H$ is finite and nonzero. For frequency $f$ in
Hz and sample rate $f_s$, $\omega=2\pi f/f_s$ is in radians per sample.
The group delay $g$ in samples and $\tau$ in seconds are

$$
g(\omega)=-\frac{d\phi}{d\omega},\qquad
\tau(f)=\frac{g(\omega)}{f_s}=-\frac{1}{2\pi}\frac{d\phi}{df}.
$$

For a pure delay of $d$ samples, $H=e^{-j\omega d}$ and $g=d$. Multiplying
$H$ by a nonzero constant adds its phase as a constant offset.
Phase delay on a declared branch is $-\phi/\omega$ at
$\omega\ne0$. A narrowband waveform's envelope follows group delay
approximately when magnitude is nearly constant and the phase is nearly
linear across the occupied band. The carrier phase follows the phase at its
own frequency. If a waveform occupies bands with different delays or sharp
magnitude changes, inspect its actual impulse or time-domain response.
[Smith, Phase and Group Delay](https://www.dsprelated.com/freebooks/filters/Phase_Group_Delay.html) ·
[Oppenheim and Verghese, §3.2](https://ocw.mit.edu/courses/6-011-introduction-to-communication-control-and-signal-processing-spring-2010/a6bddaee5966f6e73450e6fe79ab0566_MIT6_011S10_notes.pdf)

Record which tap is the reference, which is measured, the clock and epoch,
and the original sample intervals. Shifting the measured record earlier by
$a$ samples applies $e^{+j\omega a}$ to its transfer if the same response
support is retained. The resulting slope gives $g_{\rm residual}=g-a$.
Add $a$ back when reporting the original tap-to-tap delay. Keep known capture
buffer offsets and applied alignment explicit. A clock-rate mismatch changes
the meaning of a single delay estimate, so establish the time mapping before
combining captures. Use a known inserted delay or a broadband time-domain
match to check the common timing origin.
[Audio timebase](../../../../../skills/audio-timebase-sync/SKILL.md) ·
[Analysis provenance](../../../../../skills/audio-analysis-provenance/SKILL.md)

### Use the available complex transfer

**Known coefficients.** Use a derivative that can be evaluated independently
of phase unwrapping. For a finite impulse response with sample index $n$ and
the declared time origin, define

$$
H(\omega)=\sum_n h[n]e^{-j\omega n},\qquad
M_h(\omega)=\sum_n n h[n]e^{-j\omega n}.
$$

Since $H'=-jM_h$ and $d\phi/d\omega=\operatorname{Im}(H'/H)$, group delay is
$\operatorname{Re}(M_h/H)$ where $H$ is nonzero. For a rational transfer
$H=B/A$, calculate each index-weighted polynomial in the same way and use
$\operatorname{Re}(M_B/B-M_A/A)$ where both ratios are valid. For a cascade,
the valid section delays add. Evaluating the actual sections avoids forming
one large polynomial. A symmetric $M$-tap FIR with index origin zero has
delay $(M-1)/2$ where its real centered response is nonzero.
[Smith, Numerical Computation of Group Delay](https://www.dsprelated.com/freebooks/filters/Numerical_Computation_Group_Delay.html)

The Kestrel filter-design reference already measures a centered phase
increment on specified FIR or SOS models. Use it as a comparison within its
interior-frequency and magnitude limits. Those limits describe its stencil.
An analytic response can have valid group delay at DC or Nyquist when the
transfer is nonzero and differentiable there. A sampled profile that requires
a centered aperture can mark its endpoints unavailable.
[Kestrel filter response contract](../../../../../skills/audio-filter-design/references/FILTER_DESIGN_CONTRACT.md#4-frequency-response-group-delay-and-sampled-acceptance)

**Measured transfer.** For a matched capture, use an impulse-response
estimate with declared time origin and window, or derive $H_1=C_{xy}/S_{xx}$
from the paired cross-spectrum and reference auto-spectrum. The $H_1$ model
assumes a reliable reference and any additive output noise to be uncorrelated
with it. With $S_{xx}>0$, the phase of $H_1$ is the phase of $C_{xy}$.
Use the same segment pairing, window, and cross-product order as Skill #33.
Record excitation, response level, and the basis for a coherence or other
quality gate. Repeated segments and coherence can help qualify a phase bin.
A delay slope also needs nearby supported phase. Choose the stimulus and
capture duration so the target band has that support.
[Skill #33 cross-spectrum contract](../../../../../skills/audio-phase-coherence/references/PHASE_COHERENCE_CONTRACT.md#welch-profile) ·
[Audio Precision, TN138, H1](https://www.admess.de/tl_files/admess-2013/pdf/Audio%20Precision/TN138%20-%20Transfer%20Function%20Measurements%20with%20APx500%20Audio%20Analyzers.pdf)

### Estimate a slope on a supported interval

1. **Establish valid intervals.** Require a strictly increasing frequency
   grid, valid timing, and finite complex values. A true transfer zero or
   pole has undefined phase slope at that frequency. For measurements,
   identify the usable band with the level, excitation, repeatability, and
   coherence evidence. Restart the phase run across a rejected bin or known
   spectral gap. Qualify the full stencil and mark unavailable values with
   their reason. SciPy 1.17.0 documents a warning and zero placeholder when
   it detects a singularity. The DC-zero fixture below exercises that case.
   [SciPy 1.17.0 group_delay](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.group_delay.html)
2. **Check the phase branch.** For adjacent valid samples, form the principal
   angle of $H_{k+1}\overline{H_k}$, or take the wrapped difference of their
   phases. Use an independent delay bound or a finer supported grid to
   establish that each true phase change stays inside $(-\pi,\pi)$ with
   margin for noise. On a uniform DFT grid of length $N$, a pure delay of
   magnitude less than $N/2$ samples has successive changes below $\pi$
   in magnitude.
   Delays $d$ and $d+N$ have identical sampled transfers on that grid.
   Remove a known coarse offset when the residual meets the same bound.
   Unwrap the residual and restore the offset afterward.
   Zero padding a complete finite impulse samples its transfer at more
   frequencies with the same time window and measured bandwidth.
   [Keysight, group-delay accuracy and aperture](https://helpfiles.keysight.com/csg/m9485a/tutorials/group_delay6_5.htm)
3. **Use the actual aperture.** For phase points at $f_-<f_+$ on one valid
   run, use the branch-consistent estimate
   $\widehat\tau=-(\phi_+-\phi_-)/(2\pi(f_+-f_-))$. Report it at the
   midpoint with aperture $f_+-f_-$ in Hz. For a wider aperture, unwrap
   adjacent increments along the interval before combining them. A principal
   angle of the endpoint ratio wraps the full increment. For irregular grids,
   fit a local line to phase versus actual Hz. Use nonnegative weights
   and at least two distinct frequencies with positive weight. The
   weighted slope is
   $\sum_i w_i(f_i-\bar f)(\phi_i-\bar\phi)/\sum_i w_i(f_i-\bar f)^2$,
   where the bars are weighted means. Report the weighted center frequency
   and the used interval. Qualify the whole interval, particularly when
   a narrow notch could lie between sampled frequencies. The
   between-bin null fixture below shows two nonzero endpoints giving an
   erroneous slope. Inspect a sufficiently fine response or a known model.
   [Keysight, aperture on a frequency grid](https://helpfiles.keysight.com/csg/89600B/Webhelp/Subsystems/gui/content/trace_format_groupdelayaperture.htm)
4. **Check variation with aperture.** A two-point secant is the average of
   group delay over the interval when the phase is smooth there. A narrower
   interval follows sharper features and takes a smaller phase difference
   between points. With independent endpoint errors of standard deviation
   $\sigma_\phi$ radians, the estimated delay standard deviation in seconds
   is $\sqrt{2}\sigma_\phi/(2\pi\Delta f)$. Correlated endpoint errors need
   the covariance in the variance of their difference. Test two plausible
   apertures and rerun the measurement to see which features are repeatable.
   Report the grid, actual aperture, and support alongside the estimate.
   [Keysight, aperture tradeoffs](https://helpfiles.keysight.com/csg/m9485a/tutorials/group_delay6_5.htm)

Use range-safe complex ratios or phase increments. Near a response zero a
small complex error can cause a large phase error. Keep numerical
representability separate from measurement validity and retain the evidence
for any magnitude floor. Phase-only slope can be finite and negative in a
causal filter. The echo fixture shows this on a path whose first response
sample is at zero. Inspect the original impulse response when the question
is about first arrival. [Audio numerical stability](../../../../../skills/audio-numerical-stability/SKILL.md)

For acoustic measurements that include an **excess group delay** trace,
state the minimum-phase reference used to form $g_{\rm meas}-g_{\rm min}$.
Record how the magnitude was windowed and the supported bandwidth. Also
state which time offset has been applied to $g_{\rm meas}$. Altering the
time origin shifts the measured baseline. Removing a known bulk delay
changes the origin and still leaves any minimum-phase filter delay in the
residual. [REW, Group Delay Graph](https://www.roomeqwizard.com/help/help_en-GB/html/graph_groupdelay.html)

### Executed checks and portable fixtures

Frequencies in this section use 48 kHz. The model checks used NumPy 2.3.5
and SciPy 1.17.0.

| Fixture | Observed or analytic result |
| --- | --- |
| $h[n]=-2\delta[n-12]$ and $h[n]=-2\delta[n]$. | A polarity inversion shifts the phase by $\pi$. The delayed transfer gives $+12$ samples, or $0.25$ ms. The constant inverted transfer gives zero slope. |
| Symmetric FIR $h=[1/2,1/2]$. | $0.5$ sample at every valid frequency. The exact Nyquist zero has an unavailable slope there. |
| $h=[1,0,1]$. Use $H=2\cos(\omega)e^{-j\omega}$. | The slope is $+1$ sample on both sides of the 12 kHz zero. A 128-point FFT puts the zero at bin 32. Bridging bins 31 and 33 gives a false $-31$ samples. A 126-point FFT hides the zero between bins 31 and 32. Both magnitudes are about 0.049861 and the naive adjacent slope is $-62$ samples. |
| All-pass $H_c=(z^{-1}-c)/(1-cz^{-1})$ with $c=3/4$. Then prepend a 12-sample delay. | The magnitude is one. The analytic delay is $(1-c^2)/(1+c^2-2c\cos\omega)$, from 7 samples at DC to $1/7$ at Nyquist. The cascade adds exactly 12 samples at valid frequencies. |
| $h[n]=\delta[n]+(3/4)\delta[n-24]$. | First and strongest impulse at index 0. Group delay is $72/7$ samples at DC and $-72$ at 1 kHz. The 1 kHz magnitude is $1/4$. This delay comes from the interference of two causal arrivals. |
| $h[n]=\delta[n-40]$. Evaluate a 64-point FFT and a 128-point FFT of the same complete impulse record. | Nearest-branch slope gives $-24$ samples at 64 and $+40$ at 128. With a known 38-sample offset, the 64-point residual is $+2$ and restoring the offset gives $+40$. |
| SciPy 1.17.0 group delay of $h=[1,-1]$ at DC. | An exact DC zero gives a singularity warning and a returned placeholder of zero. The constant-transfer zero delay above is a different state. |

**Known coefficients.** Evaluate 513 evenly spaced frequencies from DC to
Nyquist inclusive. Use the inverted 12-sample delay, both symmetric FIRs,
the all-pass and its delayed cascade, and the 24-sample echo. Exclude the
two known null points. The six moment calculations agreed with their
closed forms at 3,076 eligible model-frequency pairs to a maximum absolute
difference of $1.137\times10^{-12}$ samples. The maximum difference against
SciPy was $2.132\times10^{-14}$ samples on those same pairs.

The existing Kestrel centered probe also agreed on four interior frequencies
(125, 500, 1500 and 3000 Hz) for a 31-tap Hamming low-pass with 5 kHz design
cutoff and an SOS representation of the $c=3/4$ all-pass. The largest absolute
errors against the analytic delays were about $2.405\times10^{-12}$ and
$2.746\times10^{-7}$ samples respectively. The probe rejected DC and Nyquist.
This comparison is scoped to those inputs and the current reference.

**Paired capture.** Use six length-128 rectangular segments with hop and
FFT length 128 and no detrending. In segment $j=0,\ldots,5$ put one impulse
of amplitude $1+j/8$ at $x[21+7j]$. Put its inverted, doubled copy twelve
samples later in $y$. Use the pooled $H_1$ and adjacent phase increments.
All 64 adjacent estimates were within $7\times10^{-14}$ samples of $+12$.
Swapping reference and measurement gave $-12$ to the same tolerance.
As a failure case, set each reference segment to the repeating period
$[1,0,-1,0]$ at gain $1+j/8$, and the measurement to the same periodic
signal delayed by one sample. Coherence is one at the sole excited bin
(12 kHz). There is no eligible adjacent slope.

**Irregular grid.** Sample the inverted 12-sample delay at
$[100,145,300,310,425,659]$ Hz. Fit a phase line with weights
$[1,2,3,2,1,3]$ after unwrapping. The estimate is $+12$ samples with
absolute error below $10^{-12}$ samples.

**Aperture.** Use $H_c$ with $c=0.98$ and a center frequency of 200 Hz,
where the point delay is 36.952603 samples. For each aperture, add
independent Gaussian errors of 1 degree standard deviation to the two
endpoint phases. Use 20,000 trials per aperture, in the listed order
with NumPy PCG64 seed 350050. The phase increments stay inside the
principal branch in this fixture.

| Aperture | Noiseless secant | Secant bias | Measured standard deviation | Predicted standard deviation |
| --- | --- | --- | --- | --- |
| 20 Hz | 36.981683 samples | +0.029080 samples | 9.523162 samples | 9.428090 samples |
| 360 Hz | 44.826944 samples | +7.874341 samples | 0.521227 samples | 0.523783 samples |

The wider aperture lowers variance here and moves the result farther from
the point delay. The bias table uses the analytic response and independent
endpoint noise. An actual capture can have correlated bins, time variation,
and errors in the timing reference.

## Next action

Implement a bounded offline reference with a known-filter derivative and
a sampled complex-transfer slope. Use the known-filter path as an oracle.
Store delay units, the applied offset, the frequency and sample support,
and validity with each result. Test the complete pure-delay curve first.
Then give the reviewer the ambiguous grid, both versions of the notch,
the single excited bin, the signed echo, and the aperture study. A passing
implementation identifies why each disputed reading changes and
preserves the timing reference needed to reproduce it.

For a field check, capture a known broadband path with repeatable timing,
then add a known sample delay and check that the valid band shifts by
that amount. Inspect the impulse and rerun with a finer supported grid
or a different aperture wherever a feature changes. Establish thresholds
from repeated measurements on the intended setup.

## Revisit when

The transfer estimator, impulse window, time reference, expected delay
range, frequency grid, aperture, usable band, or numeric representation
changes.
