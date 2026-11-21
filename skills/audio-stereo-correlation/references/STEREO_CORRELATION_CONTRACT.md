# Stereo correlation measurement contract

[Input](#aligned-capture) · [Moments](#window-moments) ·
[Mono fold-down](#mono-fold-down) · [Comparison](#compare-meters) ·
[Reference](#offline-reference)

## Aligned capture

Use one complete `CaptureWindow` and two distinct channel IDs. Pair the
original PCM values at the same integer sample index. Keep the tap,
clock, epoch, sample rate, units, and exact half-open support $[s,s+N)$.
The doubled sample center is $2s+N-1$. Check relative impulse timing
when payload alignment is in doubt.
[Capture contract](../../audio-oscilloscope/references/OSCILLOSCOPE_CONTRACT.md) ·
[Timebase](../../audio-timebase-sync/SKILL.md)

## Window moments

Keep DC and give each of the $N$ pairs equal weight. Use
$Q_L=\sum L_n^2$, $Q_R=\sum R_n^2$, and $X=\sum L_nR_n$. The channel
mean squares $P_L=Q_L/N$ and $P_R=Q_R/N$ use squared input units. Their
square roots give RMS in the input units. The mean cross-product is $X/N$.

When both squared sums are positive, the dimensionless coefficient is

$$
\rho_0=\frac{X}{\sqrt{Q_LQ_R}}.
$$

Use the sign of $X$ and the root of the exact ratio $X^2/(Q_LQ_R)$.
Cauchy–Schwarz gives an absolute bound of one. Equality of the squared
terms establishes proportionality when both channels carry energy.
A zero energy channel makes the coefficient unavailable. Nonzero
constant channels are valid. A zero $X$ gives zero correlation on this
support. Inspect a frequency or lag measurement when the direction or
cause of a time shift matters.
[RMS conventions](../../audio-rms-crest-factor/SKILL.md) ·
[Numerical stability](../../audio-numerical-stability/SKILL.md)

The reference computes the moments exactly from the represented PCM.
It rounds roots to binary64 using exact squared midpoint comparisons
and ties-to-even. With $\eta=2^{-1074}$, a positive root at or below
$\eta/2$ rounds to zero. Determine energy and cross-product states
before conversion. At a rounded zero, preserve the coefficient's sign.
An independently scaled binary64 dot product can lose a small residual
during product rounding or cancellation.

## Mono fold-down

For the equal-weight fold-down, form each $m_n=(L_n+R_n)/2$ before
accumulating $Q_M=\sum m_n^2$. Report $P_M=Q_M/N$ and its RMS. When
$Q_L+Q_R>0$, define retention relative to average input channel power as

$$
G=\frac{2Q_M}{Q_L+Q_R}.
$$

The ratio is between zero and one. A single silent input gives $G=1/2$
when the other carries energy. Equal-level opposite copies give $G=0$.
Report the power reference when using decibels. Computing the mono
samples first protects a small residual against cancellation between
large power terms in binary64. For other weights, measure the actual
$w_LL+w_RR$ and trace the delivery stage. Measure an affected band
directly when broadband averages can hide its loss.
[Channel mapping](../../audio-channel-mapping/SKILL.md)

## Compare meters

Pearson correlation removes each channel's mean. A constant channel
then has zero centered variance. Kestrel's normalized vectorscope
axis-energy difference is $2X/(Q_L+Q_R)$. Equal nonzero channel energies
make it equal to the raw coefficient. FFmpeg 7.1 `aphasemeter` averages
the per-pair ratios $2LR/(L^2+R^2)$ within each audio frame, with a +1
fallback for NaN. Match signal preparation and measurement support
before comparing readings.
[Pearson definition](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) ·
[Vectorscope coordinates](../../audio-vectorscope/references/VECTORSCOPE_CONTRACT.md#measured-coordinates) ·
[FFmpeg 7.1 source](https://www.ffmpeg.org/doxygen/7.1/avf__aphasemeter_8c_source.html#l00284)

Define window length and hop on the sample clock. Use the capture's
gap, overlap, and epoch rules. Sum disjoint window totals before
normalizing a pooled result. To pool means, weight by each window's
frame count. Account for reused samples when windows overlap. For a
weighted meter, apply the same nonnegative weight to all three
products. Multiplying both PCM planes by a taper applies squared
weights. Declare the timebase, initialization, and threshold of any
smoothing or low-level display gate.

## Offline reference

Put `audio-oscilloscope/scripts` and `audio-stereo-correlation/scripts`
on the Python module search path. Call `measure_stereo_correlation` with
a shared capture and explicit `left_channel` and `right_channel` IDs.
The bounded reference takes one to 1,024 sample frames. Input limits
and channel metadata follow the capture contract.

The result carries the epoch, support, channel IDs, and
`raw_zero_lag` estimator. `left`, `right`, and `mono` report exact
`mean_square`, binary64 `rms`, and a level `status`.
`mean_cross_product` and `mono_retention` are exact where defined.
Retention is `None` when both channel energies are zero.

`coefficient_status` distinguishes a zero-energy left, right, or
both channels from `exact_zero`, `rounded_to_zero`, `exact_endpoint`,
`rounded_to_endpoint`, and other `finite` readings. A zero-energy
input channel leaves `coefficient` as `None`. The exact cross-product
also retains its sign when the coefficient rounds to zero.
[Fixtures and tolerances](../../../tests/fixtures/AUDIO_STEREO_CORRELATION_GOLDENS.md)
