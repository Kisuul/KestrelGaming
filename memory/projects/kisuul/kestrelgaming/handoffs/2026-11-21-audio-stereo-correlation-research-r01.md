---
schema: 1
id: 2026-11-21-audio-stereo-correlation-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-21
updated: 2026-11-21
sources: "Kestrel audio branch a2323f1c8f8bba04c3ae7d6bea2be72a9d024230. FFmpeg 7.1 aphasemeter source and 7.1.5 runtime, x42 DSP at f22b08a04d81dd646238cc8736e1aefb584e26ac, Apple Logic Pro, NIST Dataplot, BBC AS-11 section 2.4.2, Breebaart et al. (2005), and executed analytical, rational and binary64 signal checks."
---

# Skill 31 research for stereo correlation

## Summary

**Task outcome:** COMPLETE

For `audio-stereo-correlation`, use a signed, zero-lag normalized inner product
of the original left and right samples over one complete window. Preserve DC.
Report the two channel levels alongside the coefficient. When investigating mono
compatibility, measure the actual fold-down. A controlled fixture in this record
has correlation +0.8 even though a tone present in both channels vanishes in mono.

The [curriculum ledger](2026-11-17-audio-curriculum-status-r01.md) names this skill
after [the vectorscope](../../../../../skills/audio-vectorscope/SKILL.md).
Use its aligned PCM input. The plotted points may have a different sampling cadence,
scale, or persistence from the meter.

## Evidence

### Published conventions

| Source | What the source establishes |
| --- | --- |
| Apple Logic Pro, Correlation Meter | The guide describes a signed −1 to +1 display for checking stereo relationships. It documents a return to center after two seconds without signal. That display position does not specify a measured coefficient or the estimator that produced it. [Logic Pro Effects, Correlation Meter](https://help.apple.com/pdf/logicpromac-effects/en_US/logic-pro-mac-effects-user-guide.pdf) |
| FFmpeg 7.1, `aphasemeter` | The filter takes the arithmetic mean of the per-pair values $2L_nR_n/(L_n^2+R_n^2)$. A NaN pair value takes the filter's +1 fallback. This gives equal weight to each pair's ratio. The local 7.1.5 check below distinguishes this policy from normalization over the entire window. [FFmpeg 7.1 source, lines 284–299](https://www.ffmpeg.org/doxygen/7.1/avf__aphasemeter_8c_source.html#l00284) |
| x42 Stereo Phase-Correlation Meter | The source filters each channel before it smooths the three products. It normalizes the smoothed cross-product with denominator regularization. The plugin initializes a 2 kHz filter parameter and a 0.3 s correlation time parameter. Match filtering, settling, timing and low-level policy before comparing readings. [DSP at f22b08a](https://github.com/x42/meters.lv2/blob/f22b08a04d81dd646238cc8736e1aefb584e26ac/jmeters/stcorrdsp.cc#L47-L93) · [Plugin initialization](https://github.com/x42/meters.lv2/blob/f22b08a04d81dd646238cc8736e1aefb584e26ac/src/meters.cc#L205) |
| Pearson product-moment correlation | Subtract each channel's own mean before normalizing the cross-product. A constant input has zero centered variance. Use this definition for correlation of fluctuations around local means. [NIST correlation reference](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/correlat.htm) · [SciPy formula and constant-input behavior](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) |

A meter labelled phase or correlation can compute a different quantity. Use these
sources to reconcile a disagreement after matching the tap, input preparation, timing,
estimator and display behavior.

### First measurement contract

1. **Pair measured samples.** Use distinct channel identities, one tap, one rate,
   common amplitude units, one epoch and equal half-open support $[s,s+N)$.
   Match by original sample index. Reject absent or mismatched channel data. Acquire
   both planes before presentation. Reuse the capture metadata and clock rules.
   The existing offline vectorscope's capture supports up to 1,024 samples per channel.
   If a longer correlation window is required, size the capture path for it explicitly.
   [Vectorscope input contract](../../../../../skills/audio-vectorscope/references/VECTORSCOPE_CONTRACT.md#aligned-pairs)
   · [Sample clocks and epochs](../../../../../skills/audio-timebase-sync/SKILL.md)
2. **Compute on the complete window.** For $N$ simultaneous pairs, define channel
   mean-square powers $P_L=\frac1N\sum L_n^2$, $P_R=\frac1N\sum R_n^2$ and
   $C=\frac1N\sum L_nR_n$. The raw coefficient is

   $$
   \rho_0=\frac{C}{\sqrt{P_LP_R}}\quad\text{for }P_L>0,\ P_R>0.
   $$

   It is dimensionless and lies in $[-1,1]$ by Cauchy–Schwarz. The common $1/N$
   factors cancel. A value of +1 or −1 means proportional
   samples with positive or negative gain, respectively. Zero means the cross-product
   sum is zero on this support. Independence and lead/lag direction require other
   evidence. If the scope uses per-sample weights $w_n$, apply the same nonnegative
   weights to all three products. Multiplying both PCM channels by a taper $w_n$
   before forming the products instead gives weights $w_n^2$. Use a rectangular
   window for the first reference.
3. **Keep level and availability.** Obtain the signal level and exact-zero state
   from each original channel. One or both all-zero channels make $\rho_0$
   unavailable. Two nonzero constant channels are valid for the raw calculation.
   A low-level display gate, if needed, is a declared threshold in the input units
   with an explicit unavailable state. Keep the gate separate from the arithmetic.
   An epsilon in the denominator changes the result when level changes. With one
   pair and both values nonzero, the result is always +1 or −1. Choose the window duration so it represents
   the variation the meter is intended to show.
4. **Scale the arithmetic where needed.** For the inner product, divide each
   channel independently by its own maximum absolute sample. Then normalize the
   dot product of these two scaled sequences by their norms. The two positive
   scale factors cancel. Use accurate accumulation and an error budget for the
   supported sample range and window length. Treat a bound violation outside that
   budget as an arithmetic error. A rounding correction at an endpoint must stay
   within the budget. Use the original levels for the fold-down. Verify distinct
   handling of an exact zero and a positive value outside the output representation.
   [Numerical stability](../../../../../skills/audio-numerical-stability/SKILL.md)

### Keep correlation and mono level distinct

For Kestrel's equal-weight fold-down $M=(L+R)/2$, with $S=(L-R)/2$,

$$
P_M=(P_L+P_R+2C)/4,\qquad P_S=(P_L+P_R-2C)/4.
$$

The normalized axis-energy difference for Kestrel's vectorscope is
$(P_M-P_S)/(P_M+P_S)=2C/(P_L+P_R)$. It equals $\rho_0$ for equal,
nonzero channel powers. If both channels carry energy and their powers differ,
the multiplier is $2\sqrt{P_LP_R}/(P_L+P_R)$. One silent channel with a nonzero
partner gives axis-energy difference zero and unavailable correlation.
[Channel mapping and Mid/Side convention](../../../../../skills/audio-channel-mapping/references/CHANNEL_MAPPING_CONTRACT.md)

Measure mono retention on the same support as $G=P_M/((P_L+P_R)/2)$ if the
denominator is positive. For an equal-weight fold-down, $0\le G\le1$ and identical
nonzero channels give $G=1$. Name the reference when reporting $10\log_{10}G$.
Equal-level opposite copies give $G=0$. For $R=-L/2$, $\rho_0=-1$ and $G=0.1$,
or −10 dB against average input channel power. If one channel is silent, $G=0.5$
under this fold-down and reference. For a different mono matrix, use its actual
weights. For example, $aL+bR$ has mean square $a^2P_L+b^2P_R+2abC$.
Measure fold-down RMS from the summed samples with suitable precision. Near
cancellation, subtracting the large power terms can erase a real residual.

Use a correlation reading to decide where to listen or inspect the actual mono
output. A broadband value can hide cancellation in a quiet band. A delayed copy
can also have low zero-lag correlation despite a strong match at another lag.
Inspect frequency or lag when the question depends on either. The BBC AS-11
delivery document describes audible mono cancellation as a condition to check,
and Breebaart et al. show why phase alignment and band support matter for
related stereo measurements. [BBC AS-11, §2.4.2](https://downloads.bbc.co.uk/scotland/commissioning/TechnicalDeliveryStandardsBBCFile.pdf)
· [Breebaart et al., §1 and §5.3](https://pure.tue.nl/ws/files/1790814/Metis194783.pdf)

### Sample timing and aggregation

Use complete windows with length $N$ and hop $H$. With epoch origin $s_0$ the
start of window $j$ is $s_j=s_0+jH$. Its support is $[s_j,s_j+N)$ and its doubled
sample-coordinate center is $2s_j+N-1$. Report the rate, channel IDs, estimator,
exact support and availability. If streaming, validate a full incoming block before
advancing the cursor. Compare output under different callback partitions. Reject
a gap or overlap, or explicitly start a new epoch. Show warm-up as unavailable
until both channels contain a full window. A paused renderer creates no new samples.

Begin with a direct reduction over the requested frame. If a rolling implementation
subtracts outgoing moments, compare it against a fresh reduction after a large impulse
leaves a quiet window. A meter that pools disjoint blocks must sum their three product
totals before normalizing. Means require weighting by their sample counts. If an
exponential measurement is required, apply the same sample-clocked decay to all
three moments before division and document its initialization, release and gate.
Averaging reported coefficients is a different display statistic. Window overlap
also changes which samples contribute when combining results.

### Executed checks and portable fixtures

For the short fixtures below, $G$ uses the equal-weight mono average. The exact
ratios come from rational samples and direct fold-down power. The FFmpeg 7.1.5
readings came from separate four-pair stereo float blocks at 48 kHz with no padding,
using audio metadata from `aphasemeter` with video disabled.

| Four-pair input | Raw $\rho_0$ | $G$ | FFmpeg |
| --- | --- | --- | --- |
| $L=[1,-1,1,-1]$, $R=L/2$ | 1 | 9/10 | 0.8 |
| $L=[1,-1,1/8,-1/8]$, $R=[1,-1,-1/8,1/8]$ | 63/65 | 64/65 | 0 |
| Both channels zero | Unavailable | Unavailable | 1 |
| $L=[1,-1,1,-1]$, $R=0$ | Unavailable | 1/2 | 0 |
| $L=[1,-1,1,-1]$, $R=-L/2$ | −1 | 1/10 | −0.8 |
| Repeat the alternating pairs $(1/4,-3/4)$ and $(3/4,-1/4)$ twice | −3/5 | 1/5 | −0.6 |

In the second row the loud positive pair of frames gives +1 and the quiet
negative pair of frames gives −1 when measured separately. Their average is zero.
Pooling the moments gives 63/65. In the last row Pearson's centered coefficient
is +1. These fixtures expose incorrect averaging and inadvertent DC removal.

| Controlled check | Independent expectation and observation |
| --- | --- |
| Use 480 samples at 48 kHz. Let $L[n]=\cos(2\pi fn/f_s)$ and $R[n]=L[n-D]$ with periodic extension. Use $D=\pm12$ and $f=500,1000,2000$ Hz. | For integer-cycle support the coefficient is $\cos(2\pi fD/f_s)$. The probes gave approximately 0.7071, 0 and −1 at those frequencies for both delay signs. |
| Use the same clock and support. Let $L=a+b$ and $R=a-b$ with zero-phase cosines $a$ at 1 kHz, peak 0.75, and $b$ at 2 kHz, peak 0.25. | Orthogonal tones give $\rho_0=0.8$ and $G=0.9$. The direct mono waveform equals $a$. A sine/cosine projection measured the 2 kHz amplitude in mono below $3\times10^{-17}$ in this binary64 check. |
| Use $L=[1,-1]$ and $R=-(1-2^{-40})L$. Evaluate both forms of $P_M$ in binary64. | The power identity rounded to zero in this evaluation. The direct mono power was $2^{-82}$, about $2.07\times10^{-25}$. |
| Use $L=[2^{-600},-2^{-600}]$ and $R=[2^{600},-2^{600}]$ in a numerical stress probe. | The unscaled sums of squares underflowed to zero and overflowed to infinity. Scaling the two channels separately gave coefficient 1. These exponents test arithmetic far outside nominal PCM. |
| Start at $2^{53}+1$ with $N=4$, $H=2$. Take $L=[1,-1,1,-1,1/8,-1/8,1/8,-1/8]$ and invert only the last four samples for $R$. | Direct calculation gave +1, 63/65, −1. The doubled centers are 18014398509481989, 18014398509481993, 18014398509481997. Replay as one block and in lengths 1, 2, 1, 3, 1 for a streaming acceptance test. |

Use a small direct dot product or exact arithmetic as the initial oracle.
Check polarity, independent positive gain, raw constant signals, measured silence,
and late invalid samples. For a rendered meter, also change the paint rate with
identical input and require the same measured values on the same sample support.
The executed checks cover the stated signals and formula behavior. Streaming
and presentation remain acceptance cases for the implementation.

## Next action

Build the stateless aligned-frame calculation first and verify the fixtures above.
Keep filtering, averaging and any display gate explicit. Ask the agent to diagnose
a mix with a positive reading whose quiet tone disappears in mono. Require it to
identify the tap, predict the mono waveform and verify the missing band directly.
Use the actual target host to verify response time if it becomes a requirement.

## Revisit when

The channel tap, preprocessing, window length, gate, fold-down matrix, or meter
ballistics change, or a target claims a broader numerical range.
