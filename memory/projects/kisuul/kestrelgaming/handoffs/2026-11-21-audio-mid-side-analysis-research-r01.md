---
schema: 1
id: 2026-11-21-audio-mid-side-analysis-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-21
updated: 2026-11-21
sources: "Kestrel audio branch a2323f1c8f8bba04c3ae7d6bea2be72a9d024230 and Skill 31 handoff at e8cb75637f5e85d6fcedcbe61e1b5c256b2088f0. DPA Mid/Side microphone guide, FFmpeg 7.1.5 source and runtime, RFC 9639 section 4.2, C++ midpoint specification, and executed rational, binary64 and spectral checks on 2026-11-21."
---

# Skill 32 research for Mid/Side analysis

## Summary

**Task outcome:** COMPLETE

For `audio-mid-side-analysis`, use Kestrel's half-sum and half-difference on
aligned original PCM. Report Mid and Side levels over the same support. Treat the
Side power fraction as a defined signal statistic. Check the actual mono fold-down
after gain, delay, clipping or other changes downstream of the matrix.

The [curriculum ledger](2026-11-17-audio-curriculum-status-r01.md) places this
skill after [stereo correlation](https://github.com/Kisuul/KestrelGaming/blob/e8cb75637f5e85d6fcedcbe61e1b5c256b2088f0/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-21-audio-stereo-correlation-research-r01.md).
Two inputs can have identical magnitudes in both L/R spectra and put an entire
band in Mid in one case and Side in the other. The fixtures below verify this
difference from measured samples and spectral phase.

## Evidence

### Choose the matrix and gain convention

Start with two distinct channel IDs from one tap, clock, rate and epoch. Use
the same sample index for both values. Record exact half-open support $[s,s+N)$
and the amplitude reference. Retain DC and valid digital headroom. Keep measured
zero, missing data and unsupported input distinct. Read timing from the
capture's sample clock.
[Aligned capture](../../../../../skills/audio-vectorscope/references/VECTORSCOPE_CONTRACT.md#aligned-pairs)
· [Sample clocks](../../../../../skills/audio-timebase-sync/SKILL.md)

For real $L,R$, let $M=k(L+R)$ and $S=k(L-R)$ for the stated nonzero gain $k$.
With this polarity, $L=(M+S)/(2k)$ and $R=(M-S)/(2k)$. A channel swap keeps $M$
and negates $S$. If an external source uses right minus left, reverse its
Side sign before applying this inverse. Verify signs with basis pairs.

| Convention | $k$ | For $L=R=1$, output $M$ | For $L=1,R=0$, output $(M,S)$ |
| --- | --- | --- | --- |
| Kestrel amplitude-normalized | $1/2$ | 1 | $(1/2,1/2)$ |
| Orthonormal | $1/\sqrt2$ | $\sqrt2$ | $(1/\sqrt2,1/\sqrt2)$ |
| Unscaled sum and difference | 1 | 2 | $(1,1)$ |

The orthonormal matrix preserves $M^2+S^2=L^2+R^2$. The Kestrel matrix
preserves $(L^2+R^2)/2$ as $M^2+S^2$. A nonzero orthonormal coordinate is
about 3.01 dB above its amplitude-normalized value for the same reference.
In Kestrel's vectorscope, mathematical coordinates are
$x=-\sqrt2 S$ and $y=\sqrt2 M$ for the half-sum and half-difference. Compare
these measured coordinates before viewport gain, clipping and history.
[Channel matrix](../../../../../skills/audio-channel-mapping/references/CHANNEL_MAPPING_CONTRACT.md)
· [Vectorscope axes](../../../../../skills/audio-vectorscope/references/VECTORSCOPE_CONTRACT.md#measured-coordinates)

| Source | Implication for the skill |
| --- | --- |
| FFmpeg 7.1.5 `stereotools` | At its default gains and pans, the encoder uses the half-sum and half-difference, and the decoder adds or subtracts the pair. The source also has balance, polarity, delay and clipping options. Record those settings for a differential test. [Pinned filter source](https://github.com/FFmpeg/FFmpeg/blob/n7.1.5/libavfilter/af_stereotools.c#L221-L245) |
| DPA Mid/Side microphone setup | The described arrangement uses a forward-facing Mid mic and a transverse figure-eight mic with its positive lobe to the left. The captured signals carry the capsule patterns, gains and orientation. Verify these before decoding a mic pair. A digital transform of arbitrary L/R produces sum and difference coordinates on the existing samples. [DPA Mid/Side setup and decode](https://www.dpamicrophones.com/mic-university/audio-production/stereo-recording-techniques-and-setups/) |
| FLAC channel decorrelation | FLAC stores an integer half-sum rounded by a right shift and the full integer difference. The decoder uses the difference's low bit to recover the lost parity of the sum. The difference needs an extra bit. Use this only for codec comparisons. A signed 16-bit pair $(1,0)$ gives FLAC $(0,1)$ and analysis $(1/2,1/2)$. [RFC 9639, §4.2](https://www.rfc-editor.org/rfc/rfc9639.html#section-4.2) |

### Define the measurements over one window

For the Kestrel convention, write $P_X=\operatorname{mean}(X^2)$ and
$C=\operatorname{mean}(LR)$ on the same support. The channel and component
powers are in squared input units. Compute component samples first, then
report their RMS or powers. Define $F_S=P_S/(P_M+P_S)$ when total power is
positive. An all-zero measured window has zero component RMS and unavailable
$F_S$. Keep this availability when mapping to the display.

$$
P_M+P_S=(P_L+P_R)/2,\qquad
\operatorname{mean}(MS)=(P_L-P_R)/4,\qquad
F_S=\tfrac12-\frac{C}{P_L+P_R}.
$$

Equal nonzero L/R powers give $F_S=(1-\rho_0)/2$ for the raw zero-lag
coefficient. Otherwise the relationship depends on the channel powers.
A left-only input $\bigl(L,R\bigr)=(x,0)$ gives $M=S=x/2$ and $F_S=1/2$ for
any nonzero $x$. Two nonzero orthogonal channels give the same fraction.
Use the original channel levels, temporal structure and phase to understand
what contributes to the difference signal. A single hard-panned source
contributes to both components. If reporting Side/Mid
in decibels, declare $10\log_{10}(P_S/P_M)$ and the zero cases. A zero Side
with positive Mid gives $-\infty$. A positive Side with zero Mid gives
$+\infty$. Two zeros leave the ratio undefined.

Avoid using the power identities to obtain a small residual. For
$L=[1,-1]$ and $R=(1-2^{-40})L$, the direct Side power is $2^{-82}$.
In the binary64 check, $(P_L+P_R-2C)/4$ rounded to zero.
Use scaled RMS where the supported input range requires it. For $F_S$,
scale both components by the same nonzero peak before reducing the powers.
[Numerical stability](../../../../../skills/audio-numerical-stability/SKILL.md)

### Verify widening and the downstream mono result

With gains $g_M,g_S$, reconstruct $L'=g_M M+g_S S$ and
$R'=g_M M-g_S S$. The average $(L'+R')/2$ returns $g_M M$ for aligned linear
outputs. Setting $g_S=0$ removes the difference and loses its information.
With $g_M=1$ and $g_S=-1$, the channels swap. A signed gain should have a
defined polarity interpretation.

The equivalent L/R matrix has diagonal entries $(g_M+g_S)/2$ and off-diagonal
entries $(g_M-g_S)/2$. The absolute row sum is $\max(\lvert g_M\rvert,\lvert g_S\rvert)$.
With both input magnitudes bounded by $A$, this gives a sharp worst-case
sample magnitude bound for the linear matrix. Identical inputs at magnitude
$A$ attain the Mid bound. Inputs at $A$ and $-A$ attain the Side bound. For
example, $g_M=1$, $g_S=2$ and $(L,R)=(1,0)$ give $(L',R')=(1.5,-0.5)$.
The average remains 0.5. Clipping each channel at magnitude 1 changes
that average to 0.25. Keep the unclipped samples and the stage that
applies any limit identifiable.

If the final mono matrix is $(a,b)$, its result is
$(a+b)g_M M+(a-b)g_S S$. An unequal-weight fold can retain Side.
A shared filter or delay on Side before splitting its signs still cancels
in an aligned equal-weight fold. A delay on one reconstructed output
changes the pairing. The pure-Side impulse fixture below distinguishes
those two paths. Test the actual delivery tap and matrix.

### If the measurement needs a frequency diagnosis

Form Mid and Side from aligned samples before measuring their spectra.
With the same linear windowed transform on both channels, their complex
bins also follow the same matrix. For density estimates $D_L,D_R$ and
$D_{LR}$, let $D_{LR}$ use the product $\overline X_L X_R$ and the
same one-sided scaling as $D_L$ and $D_R$. Then

$$
D_M=(D_L+D_R+2\operatorname{Re}D_{LR})/4,\qquad
D_S=(D_L+D_R-2\operatorname{Re}D_{LR})/4.
$$

Use these identities as checks on direct component spectra. Match the
window, time support, detrending, FFT length and endpoint scaling first.
Integrate both densities over the same declared band and divide the Side
power by the total band power. Combine linear powers before ratios or
decibels. A zero-power band leaves the fraction unavailable. Reuse the
project's PSD and band integration convention.
[PSD calibration](../../../../../skills/audio-power-spectral-density/SKILL.md)
· [Fractional band integration](../../../../../skills/audio-fractional-octave-rta/references/FRACTIONAL_OCTAVE_RTA_CONTRACT.md#psd-integration-and-coverage)
· [Cross-spectrum convention](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.csd.html)

### Check representation and finite precision

Use the existing routing signs, gain and channel labels. The channel matrix
reference accepts up to 256 samples per channel in one call and applies
each coefficient before summing. If the supported range includes subnormals,
verify the mixer against an oracle that evaluates the exact sum and divides
by two before rounding. For maximum finite binary64 $B$, $(B+B)/2$ with an
intermediate binary64 sum overflows although the exact midpoint is $B$.
For minimum positive binary64 $\eta=2^{-1074}$, separately halving both
inputs rounds both to zero. With $(L,R)=(\eta,\eta)$ the exact Mid is
$\eta$. With $(\eta,-\eta)$ the exact Side is $\eta$. The current mapper
returned zero in both cases at a2323f1. Match the helper to the
declared range and rounding policy. An overflow-safe floating-point midpoint
is one option for $M$ and for $S$ as the midpoint of $L$ and $-R$.
[Existing matrix application](../../../../../skills/audio-channel-mapping/scripts/reference_channel_mapping.py)
· [Floating-point midpoint contract](https://eel.is/c%2B%2Bdraft/numeric.ops.midpoint)

A reversible real-valued transform can lose information when each output is
rounded. With $L=1,R=2^{-60}$ in binary64, both half-scaled coordinates round
to 0.5 and the reconstructed right value is zero. Check reconstruction within
an error budget that includes an absolute tolerance. Handle a component or
power outside the supported representation explicitly. Inverse decoding of
arbitrary M/S inputs can produce a sum outside the finite input range.

### Reproducible checks

| Fixture | Expected result and observed evidence |
| --- | --- |
| Exact grid with $L,R$ independently selected from $\{n/4:-5\le n\le5\}$. Select each gain independently from $\{-2,-1,-1/2,0,1/2,1,2\}$. | 121 exact pairs verified the inverse, swap sign, power identity and Mid–Side product. All 5,929 gain cases satisfied the L/R matrix, mono identity and headroom bound. Equal and opposite full-scale cases attained the bound. |
| Ordered pairs $(1,1),(1,-1),(1,0),(0,1),(0,0),(1,-1/2),(5/4,-1/4)$. | FFmpeg 7.1.5 matched the analytic values for all seven pairs. Use `stereotools` on stereo binary64 PCM at 48 kHz. Encode the input with `mode=lr>ms`. Decode the encoded pairs with `mode=ms>lr`, once at default gain and once with `slev=2`. |
| Pure Side impulse $S=[1,0,0]$ and $M=0$. Delay Side by one sample before decoding. In a second pass delay only the reconstructed right output. | The first mono waveform is $[0,0,0]$. The second is $[1/2,-1/2,0]$. Verified with exact sample arithmetic. |
| Use 480 samples at 48 kHz of zero-phase cosines $a$ at 1 kHz with peak $3/4$ and $b$ at 2 kHz with peak $1/4$. Set $L=a+b$. Compare $R=a+b$ with $R=a-b$. | Direct projections found the same L/R peak magnitudes 0.75 at bin 10 and 0.25 at bin 20 in both cases. Whole-frame $F_S$ was 0 and 0.1, respectively. At bin 20, $F_S$ was 0 and 1. The measured Mid residual at 2 kHz in the second case was about $4.1\times10^{-17}$ in peak units. Both cases passed the cross-term power check. |
| 16-bit FLAC reference pairs $(1,0),(0,1),(-32768,32767),(32767,-32768)$. | The integer parity reconstruction recovered all four pairs exactly. The greatest difference magnitude was 65,535, outside the signed 16-bit range. |

## Next action

Implement the stateless analysis of an aligned frame with the agreed matrix.
Verify exact basis pairs, common and differential DC, one silent channel, missing
channels, polarity, near cancellation and supported numeric limits. For a streamed
version, replay the same samples across uneven callback partitions above sample
index $2^{53}$ and verify the exact unchanged timestamps. Exercise gap, epoch change,
and rejected input handling.

Give the reviewer the two-tone fixture and ask them to explain why the L/R
magnitudes agree while their mono outputs differ. Have them confirm Mid and Side
waveforms and independently calculate band powers. Then introduce the one-sided
delay or the clip fixture and trace the first stage where the fold-down changes.

## Revisit when

The polarity or normalization convention, capture range, measurement window,
band estimator, or mono delivery matrix changes.
