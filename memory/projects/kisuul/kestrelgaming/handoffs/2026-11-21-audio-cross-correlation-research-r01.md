---
schema: 1
id: 2026-11-21-audio-cross-correlation-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-21
updated: 2026-11-21
sources: "Kestrel audio branch 67a09a8657fff5f28cf8509fe49f0060ff6ac5fe, Smith's correlation theorem, SciPy 1.17.0, Knapp and Carter (1976), Grinstein et al. (2024), Salvati et al. (2021), Cespedes et al. (1995), ITU-T P.931, and executed synthetic and differential checks."
---

# Skill 34 research for audio cross-correlation

## Summary

**Task outcome:** COMPLETE

Start `audio-cross-correlation` with a bounded, linear, integer-lag measurement
on two named PCM taps. With a common origin, a positive lag means the
measurement follows the reference. Keep the scored curve, its sample support,
and the selected delay.
The highest score answers the selected criterion. Short overlaps, repeated
waveforms, and a strong reflection can all produce a high score without
identifying the intended delay.

Use a direct sum as the offline reference. Compare an FFT implementation
against the complete lag curve before using it to select a peak. Teach
fractional refinement and frequency weighting after the integer-lag
measurement works. This follows the reference-first channel order of
Skill #33. [Curriculum ledger](2026-11-17-audio-curriculum-status-r01.md) ·
[Phase and coherence](../../../../../skills/audio-phase-coherence/SKILL.md)

## Evidence

### Define lag on the sample clock

Let `x` be the reference of length $N_x>0$ and `y` the measurement of
length $N_y>0$. Use zero-based indices. At integer lag $\ell$, pair $x[n]$
with $y[n+\ell]$. The feasible lags are $1-N_x\le\ell\le N_y-1$.
Use this half-open reference interval and its pair count.

$$
I_\ell=[\max(0,-\ell),\,\min(N_x,N_y-\ell)),\qquad
m_\ell=\min(N_x,N_y-\ell)-\max(0,-\ell).
$$

The paired measurement interval is $I_\ell+\ell$. For real PCM, the raw
linear score is $R_{xy}[\ell]=\sum_{n\in I_\ell}x[n]y[n+\ell]$. Its units
are the product of the input sample units. In the complex form, conjugate
the reference. Swapping the real inputs gives $R_{yx}[-\ell]=R_{xy}[\ell]$.
For an isolated matching event with $y[n]=a\,x[n-d]$ and $d>0$ on a common
origin, the corresponding peak is at $+d$. An inverted response changes
the score sign. [Smith, discrete-time correlation](https://www.dsprelated.com/freebooks/sasp/Fourier_Transforms_Continuous_Discrete_Time_Frequency.html)

If the first samples have indices $s_x$ and $s_y$ on one clock and epoch,
the clock-referenced delay is $d=s_y-s_x+\ell$. In seconds it is $d/f_s$,
with $f_s$ the exact sample rate. Keep the origin arithmetic in integer
samples until conversion. Positive $d$ then always denotes a later
measurement event, even when the local array lag has the opposite sign.
Translate the expected delay range to local lags before intersecting it with
the feasible range. Two devices with the same nominal rate can have different
clocks. Establish a verified time mapping or report the relative array lag
with its limitations. Recheck offsets across time when drift is plausible.
Start a new valid interval at a capture gap or reset.
[Sample clocks](../../../../../skills/audio-timebase-sync/SKILL.md) ·
[Measurement provenance](../../../../../skills/audio-analysis-provenance/SKILL.md)

### Match the direct and FFT measurements

Use the same preprocessing and support for both paths. For the **full
raw linear sum**, zero-pad both records to transform length
$L\ge N_x+N_y-1$. With unnormalized negative-exponent transforms and an
inverse scaled by $1/L$, form $C[k]=\overline{X[k]}Y[k]$. The inverse is the
sum of $x[n]y[(n+\ell)\bmod L]$ for real input. Padding separates every positive
and negative linear lag into its own inverse-DFT index. Read lag $\ell$
at index $\ell\bmod L$. Keep only the feasible lags and count original
samples toward overlap. A real-FFT API can store only the nonnegative
bins and restore the conjugate half in its inverse.
Use the complex products directly, with no one-sided PSD doubling.
[Smith, DFT correlation theorem](https://www.dsprelated.com/freebooks/mdft/Correlation_Theorem.html) ·
[Skill #33 cross-spectrum convention](../../../../../skills/audio-phase-coherence/references/PHASE_COHERENCE_CONTRACT.md#welch-profile)

For a differential check with SciPy 1.17.0, use `correlate(y, x, mode="full")`
and `correlation_lags(N_y, N_x, mode="full")`. The `correlate` definition
conjugates the second input, so this argument order yields the intended
positive-lag convention. Freeze an asymmetric impulse fixture before a
library swap. A direct sum over a narrow search can be cheaper than computing
the whole FFT curve. An FFT can accelerate the raw numerator over many lags.
Norms and means for a normalized estimate must still use the defined
support. [SciPy correlate](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.correlate.html) ·
[SciPy correlation lags](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.correlation_lags.html)

### Choose the score and qualify its peak

| Score | Meaning and support |
| --- | --- |
| Raw sum $R_{xy}[\ell]$ | Useful for a known template or controlled probe. Score magnitude depends on gain and on the amount and energy of overlapping data. |
| Mean product $R_{xy}[\ell]/m_\ell$ | Average product per paired sample. The units remain sample units multiplied together. Short overlaps can give variable estimates. |
| Overlap cosine $R_{xy}[\ell]/\sqrt{E_xE_y}$ | Divide by the product of the two norms from $I_\ell$. Dimensionless and bounded by $[-1,1]$ when both energies are positive. Retains DC. For equal-length captures at zero lag this is Kestrel's stereo correlation. |
| Overlap Pearson | Subtract the mean of each paired vector on $I_\ell$ before taking the cosine. A constant vector has zero centered energy. This answers whether the variations match in the presence of different offsets. |

Here $E_x=\sum_{I_\ell}x[n]^2$ and $E_y=\sum_{I_\ell}y[n+\ell]^2$.
A fixed whole-record normalization or a fixed length divisor gives a
different estimate. State the denominator and any demeaning, taper, or
band selection. Apply the same preprocessing before comparing methods.
Demeaning each overlap changes its vectors at every lag. A measured zero
cross-product with positive energies gives a valid zero coefficient. A
zero denominator makes the coefficient unavailable.
[Stereo correlation](../../../../../skills/audio-stereo-correlation/SKILL.md)

One pair with both samples nonzero gives cosine magnitude one. With two
pairs and both channels varying, Pearson magnitude is one because each
mean-removed vector is proportional to $(1,-1)$. Set the minimum paired
support and level from the capture and stimulus before peak selection.
A capture with guard samples can use the same reference samples for
every candidate. For a local search
$[\ell_{\min},\ell_{\max}]$, any subset of
$[\max(0,-\ell_{\min}),\,\min(N_x,N_y-\ell_{\max}))$ has that property.
A positive raw score can be dominated by DC. Remove DC when the signal
variation is the intended match and check that enough band energy remains.

Compare eligible positive maxima for a known same-polarity path. If polarity
is unknown, compare magnitudes and retain the sign of the winning score.
Return an ambiguous result when separated peaks tie or when the measurement
cannot resolve their difference. Report the search edge when a peak reaches a
bound. Keep peak separation, the support and level checks, and the competing
lags visible. Prominence can serve as an application-specific quality
indicator. Estimating a probability of correctness requires calibration for
the stimulus, window, noise, and search range.

Store energy and centered variance with a stable reduction. For a cosine,
scaling each vector by its own positive maximum magnitude before accumulating
products preserves the coefficient. Exact or exponent-aware arithmetic can
serve as a reference when an input pair spans a large numeric range.
An exact oracle can compare the squared cosine ratios as rational numbers,
then use the original signs for signed ranking. Apply any measurement
tie tolerance to the underlying comparison. Use explicit centering or a
stable variance algorithm for small variations on a large offset.
Separate a finite raw result that is outside the output
type's range from a valid normalized coefficient. Reject nonfinite input
and keep silence, missing samples, and unavailable estimates observable.
[Numerical stability](../../../../../skills/audio-numerical-stability/SKILL.md)

### Refine or change the estimator with evidence

For an isolated integer peak at $\ell_0$ with two eligible neighbors, take
their scores $q_-,q_0,q_+$. If the winning peak is inverted, negate all three
scores together. Fit a parabola through the three equally spaced samples.
Its vertex displacement is

$$
\delta=\frac{q_--q_+}{2(q_--2q_0+q_+)}.
$$

Accept a fractional candidate $\ell_0+\delta$ only for a stable concave
fit at a local maximum inside the search. If the neighbors are unavailable
or the shape is flat or ambiguous, retain the integer result with its
quality state. Model error depends on the peak shape. In the executed
fractional fixture below the parabolic estimate has different biases at
different bandwidths. Calibrate error on the intended signal band and at
known fractional offsets. [Céspedes et al. (1995), abstract and bias result](https://doi.org/10.1177/016173469501700204)

Generalized cross-correlation changes the frequency weights before the
inverse transform. The phase transform, GCC-PHAT, uses $C[k]/\lvert C[k]\rvert$
at accepted nonzero bins and zero at excluded bins. It can sharpen an
isolated broadband-delay peak. The same operation gives a weak retained
bin the same pre-inverse magnitude as a strong bin, so weak noisy or
conflicting bins can change the winning lag. Record the bin mask, any floor
or partial weighting, and the selected peak. Use a conjugate-symmetric
weighting for real signals. Treat an empty mask as insufficient evidence.
If using coherence to qualify bins, obtain it from several supported
segment pairs. Retain the unweighted comparison. The weighted inverse is
periodic in $L$ and is a different estimator from the linear raw sum.
Evaluate plausible lags and check the effects of the chosen FFT grid.
[Knapp and Carter (1976), GCC bibliographic reference](https://doi.org/10.1109/TAU.1976.1162830) ·
[Grinstein et al. (2024), §§2.4 and 4.1](https://doi.org/10.1186/s13636-024-00377-z) ·
[Salvati et al. (2021), §§2–3](https://www.isca-archive.org/interspeech_2021/salvati21_interspeech.pdf)

### Executed checks and portable fixtures

All indices below are zero-based. These are synthetic calculations.
The delayed pair, edge-gate, periodicity, and multipath fixtures use real
records and the direct formula above.

| Fixture | Observed or exact result |
| --- | --- |
| $N_x=7$, $N_y=11$. Place $2$ at $x[2]$ and $3$ at $y[6]$. All other values are zero. Repeat with $y$ inverted and with the roles swapped. | Positive peak $+4$ and raw score $6$ with seven pairs. Inversion gives the same absolute peak at score $-6$. Swapping the inverted pair gives lag $-4$. The inverted single impulse also gives PHAT score $-1$ at $+4$ with $L=17$. With $s_x=2^{60}+1$, $s_y=2^{60}+101$ and 48 kHz, the physical delay for the original order is 104 samples, or $13/6$ ms. |
| $x=[0,0,0,1]$, $y=[1,0,0,0]$. | A length-4 inverse puts the circular maximum at index $1$. Padding to length 7 and extracting signed lags gives $-3$. |
| $x=[3,-1,4,-2,1,5,-4,2]$, $y=[2,-3,3,-1,4,-1,1,5]$. | Overlap cosine is $+1$ at both $\ell=-7$ and $+7$, each with one pair. With six or more pairs eligible in this fixture, the absolute peak is at $+2$, about $0.991201182589$. |
| Let $p=[1,0,-1,0]$ and form two length-32 records $x[n]=p[n\bmod4]$, $y[n]=p[(n-1)\bmod4]$. Use $8\le n<24$ at every lag from $-6$ to $+6$. | Positive peaks of $8$ at $-3,+1,+5$. Negative peaks of $-8$ at $-5,-1,+3$. A single period-compatible winner would hide the ambiguity. |
| Length-32 $x$ has one unit impulse at index 4. Length-32 $y$ has impulses at 7 and 13 with amplitudes $1/4$ and $1$. | First arrival at $+3$, strongest peak at $+9$. The criterion changes the reported delay. |
| Add $2^{40}$ to $[-2,-1,1,2]$ and use the reversed result as the measurement. Separately scale $[1,-2,3]$ by $2^{600}$ or $2^{-600}$ and invert for the measurement. | Explicit centering preserves Pearson $-1$ in the first case. Calculating variance as the difference of two large moments gives zero in binary64. In the scaling cases the raw power sums overflow or underflow, while the scaled overlap cosine remains $-1$. |
| $x=[1,0]$, $y=[1,2^{-30},1,0]$. Compare the two-pair cosine at lags 0, 1 and 2. | The squared scores at 0 and 2 are $2^{60}/(2^{60}+1)$ and $1$. Lag 2 has the largest exact score. Both peaks display as 1 in binary64, so a display-value comparison creates a tie. |

**Differential check.** Use NumPy PCG64 seed 340020 and draw uniform
$[-1,1)$ values for `x` then `y` for each length pair in this order.
Use $(N_x,N_y)=(1,5),(7,11),(12,4),(64,63),(127,129)$. Compare a direct
accurately summed dot product at all 418 feasible lags across those inputs
with two FFT lengths per input, $N_x+N_y-1$ and $N_x+N_y+2$.
The 836 FFT comparisons had maximum absolute error $2.665\times10^{-15}$
in squared normalized sample units. SciPy 1.17.0 direct and FFT modes had
maxima $1.776\times10^{-15}$ and $2.720\times10^{-15}$ over the same 418
lags. These are observations on the specified scale and inputs.

**Fractional fixture.** For $n=0,\ldots,256$, set $x[n]=\operatorname{sinc}(W(n-128))$
and $y[n]=\operatorname{sinc}(W(n-128-2.35))$, with
$\operatorname{sinc}(u)=\sin(\pi u)/(\pi u)$ and value one at the origin.
Search raw lags $-8$ through $+8$. For $W=1,0.5,0.25$, the integer estimate
was $+2$ in all three cases. The three-point fit gave $2.231788$, $2.326345$,
and $2.344364$ samples. The differences from the known 2.35-sample delay
show why interpolation resolution and estimation error need separate labels.

**Weighting fixture.** Use a 64-point diagnostic with positive bins 1–8
at $X[k]=1$ and bins 9–31 at $X[k]=0.01$. Set
$Y[k]=X[k]\exp(-2\pi i k d_k/64)$, with $d_k=3$ on the strong band and
$d_k=11$ on the weak band. Set DC and Nyquist to zero and fill the
negative bins by conjugate symmetry. Search signed lags $-16$ to $+16$.
The unweighted inverse peaks at $+3$. PHAT with both bands peaks at $+11$.
PHAT restricted to bins 1–8 and their conjugates peaks at $+3$. This
controlled frequency-grid test isolates the weighting effect. The data
contain two different band delays by construction.

## Next action

Implement an offline integer-lag reference with explicit clock and channel
order, search bounds, per-lag support, named score, and validity states.
Test its raw sum and lag layout first. Then test level and overlap gates,
polarity, ties, search-edge peaks, silence, constant inputs, and nonfinite
inputs. Use the synthetic fixtures to verify the rule that selects a
peak. Add fractional refinement or PHAT only with a separate stated
selection rule and evidence for its accuracy on the intended signal.

For a loopback or channel-alignment check, send a finite, distinctive
broadband probe and record both named taps with guard time for the expected
delay and decay. Add a known sample offset as a cross-check. Verify that
the reported delay moves by the injected amount and compare repeated
captures on the same settings. For an acoustic path, inspect secondary peaks
and establish how to distinguish direct arrival from a stronger reflection.
For an electrical loopback, report the tap-to-tap or round-trip delay that
the wiring measures. ITU-T P.931 §7 illustrates why a coarse search,
fine-stage consistency checks, and timestamps can all matter in a
communications measurement. [ITU-T P.931](https://www.itu.int/rec/T-REC-P.931-199812-I/en) ·
[Electrical loopback example](https://www.mathworks.com/help/audio/ug/measure-audio-latency.html)

## Revisit when

The sample clock, tap pair, search bounds, stimulus bandwidth, peak rule,
numeric representation, or acoustic path changes. Hardware clock mapping
and field thresholds require measurements on the intended setup.
