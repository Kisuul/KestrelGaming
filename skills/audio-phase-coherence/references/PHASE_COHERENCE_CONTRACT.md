# Phase and coherence measurement contract

[Capture](#capture-the-pair) · [Welch profile](#welch-profile) ·
[Validity](#read-the-measurement) · [Interpretation](#interpret-the-estimate) ·
[Offline reference](#offline-reference)

## Capture the pair

Use two distinct channel IDs from one complete PCM capture. Preserve
the capture tap, clock, epoch, units, and exact sample rate $f_s$.
Keep the reference $x$ and measurement $y$ in the declared order.
When applying an offset, record the original interval of each channel,
the offset, and the resulting pairings. Start a new observation when
a gap or a clock discontinuity changes the support.
[Sample clock](../../audio-timebase-sync/SKILL.md) ·
[Capture contract](../../audio-oscilloscope/references/OSCILLOSCOPE_CONTRACT.md)

## Welch profile

Use the same real window $w$ of length $M\ge 2$, hop $1\le H\le M$,
and transform length $N\ge M$ for both channels. Subtract each segment's
mean before tapering only when mean subtraction is selected. Retain DC by
default. At capture start $s$, use complete paired segments at $s+jH$.
For $K>0$ the used interval is $[s,s+M+(K-1)H)$. Zero padding changes the
bin step to $f_s/N$ and leaves the measured interval intact.

Let $X_j[k]$ and $Y_j[k]$ be unnormalized negative-exponent DFT bins.
At a fixed bin sum

$$
Q_x=\sum_j \lvert X_j\rvert^2,\qquad
Q_y=\sum_j \lvert Y_j\rvert^2,\qquad
C=\sum_j \overline{X_j}Y_j .
$$

Multiply all three sums by $d_k/(K f_s U)$ to obtain densities, with
$U=\sum_{n=0}^{M-1}w[n]^2$. Use $d_k=1$ at DC and at Nyquist for
even $N$. Use $d_k=2$ at the remaining positive-frequency bins,
including the highest bin for odd $N$. Multiply the complex product
by this factor to retain its imaginary part. Auto density is in squared
input units per Hz. Cross density is in the product of input units per Hz.
[PSD calibration](../../audio-power-spectral-density/references/PSD_CALIBRATION.md#normalization) ·
[SciPy 1.17.0 CSD](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.csd.html)

## Read the measurement

For positive $Q_x$ and $Q_y$, magnitude-squared coherence is
$\gamma^2=\lvert C\rvert^2/(Q_x Q_y)$ and lies in $[0,1]$.
Phase is $\arg C$ in radians on $(-\pi,\pi]$ when $C$ is nonzero.
DC and even Nyquist have real cross-products and phase $0$ or $\pi$
when defined. Compare phases by their wrapped difference.

| State | Result |
| --- | --- |
| Fewer than two complete segments | Return warm-up and the segment metadata. The bin tuple is empty. |
| Either auto power is zero | Return the measured densities. Coherence and phase are unavailable. |
| Both auto powers are positive and $C=0$ | Coherence is zero. Phase is unavailable. |
| Both auto powers are positive and $C\ne0$ | Return coherence and phase. Keep any display mask separate. |

A single-segment estimate with both coefficients nonzero gives unity
coherence by algebra. Report the number of segments and the number
where both coefficients are nonzero at the bin. Inspect the levels
when a single event accounts for the reading.
For pooled weighted estimates, use the same nonnegative weights and
same segment selection on all three products. Treat a value outside
the estimator's numerical error bound as a defect.
[SciPy 1.17.0 coherence](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.coherence.html)

## Interpret the estimate

Coherence one with positive powers means one complex gain relates the
two segment vectors at that bin. An inverted copy can have coherence
one at phase $\pi$ and cancel in an equal-weight mono fold. For a
matched delayed copy $y[n]=x[n-d]$, the expected phase is
$-2\pi k d/N$ modulo a turn. Swapping the channels conjugates the cross
density. Inverting the measurement adds $\pi$ modulo a turn. Both leave
coherence unchanged. Truncation at segment boundaries can change the
measured relationship, so confirm that the same part of the signal falls
inside each pair.
[Stereo correlation](../../audio-stereo-correlation/SKILL.md) ·
[Mid/Side and delivered mono](../../audio-mid-side-analysis/SKILL.md)

Check phase, both channel levels, and the original taps when coherence
changes. A controlled offset or polarity change can test your diagnosis.
When the model is $Y=AX+E$ with $E$ uncorrelated with $X$ at the bin,
population coherence is the fraction of response power due to $AX$.
Gain variation across segments can also lower coherence. Verify the
assumptions before interpreting the result as a noise fraction.

Overlap reuses samples. Base any uncertainty statement on a model of
the actual window and overlap. Under the independent, identically
distributed circular complex Gaussian null at one interior bin, with
$K$ equally weighted observations and independent channels, the
exceedance probability at $c$ is $(1-c)^{K-1}$. For $K=8$, the
5% threshold is about 0.3482. Assess overlap, unequal segment
variances, real-only endpoints, and multiple-bin inference separately.
Use display thresholds in the units of the displayed quantity.
[Research and null-model checks](https://github.com/Kisuul/KestrelGaming/blob/beda56539e68bc7fcf8e3a62b3f81d1c107db1d1/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-21-audio-phase-coherence-research-r01.md#respect-numerical-limits-and-estimator-uncertainty)

## Offline reference

Put `audio-oscilloscope/scripts` and `audio-phase-coherence/scripts` on
the module search path. Call `analyze_phase_coherence` with a shared
`CaptureWindow`, a `WelchProfile(window, hop, fft_length, detrend)`,
and explicit `reference_channel` and `measurement_channel` IDs.
Use finite binary64 window coefficients with positive energy. The
detrending choices are `none` and `mean`. The result retains the full
capture bounds, all complete segment starts, and the used exclusive end.

The transform length is at most 1,024. For a ready measurement the
sample-bin term limit per channel is
$K M (\lfloor N/2\rfloor+1)\le262\,144$. Use this bounded direct
calculation as an offline comparison for a faster implementation.

PCM, window coefficients, and represented DFT weights enter exact
arithmetic before tapering and transformation. The roots have exact
axis values and quadrant symmetries. Other coefficients use binary64
sine and cosine. The reference returns rational frequencies, densities,
and coherence for this kernel. It scales the exact cross components
before conversion for binary64 phase. A positive power or coherence
can round to zero in a display. At spectral nulls, verify the absolute
numerical error and inspect the levels before interpreting a residual.
[Numerical stability](../../audio-numerical-stability/SKILL.md) ·
[Frozen fixtures](../../../tests/fixtures/AUDIO_PHASE_COHERENCE_GOLDENS.md)
