# Mid/Side analysis measurement contract

[Input](#aligned-capture) · [Matrix](#matrix-and-levels) ·
[Delivered mono](#trace-the-delivered-mono-signal) ·
[Bands](#diagnose-a-frequency-band) · [Reference](#offline-reference)

## Aligned capture

Select two distinct channel IDs from the same original PCM capture.
Carry its tap, clock, epoch, rate, units, and half-open support $[s,s+N)$.
Pair values at each original integer sample index. The doubled sample
center is $2s+N-1$. Report an incomplete capture as unavailable. For a
Mid/Side microphone pair, verify the capsule patterns, orientation, and
gains before decoding.
[Capture contract](../../audio-oscilloscope/references/OSCILLOSCOPE_CONTRACT.md) ·
[DPA microphone setup](https://www.dpamicrophones.com/mic-university/audio-production/stereo-recording-techniques-and-setups/)

## Matrix and levels

Use $M=(L+R)/2$ and $S=(L-R)/2$. Reconstruct the original samples as
$L=M+S$ and $R=M-S$. A channel swap preserves Mid and negates Side.
An orthonormal convention multiplies both of these components by
$\sqrt2$. An unscaled sum and difference doubles them. When an input
uses right minus left for Side, reverse its sign for this inverse.
Kestrel's vectorscope uses $x=-\sqrt2 S$ and $y=\sqrt2 M$.
[Channel matrix](../../audio-channel-mapping/references/CHANNEL_MAPPING_CONTRACT.md) ·
[Vectorscope axes](../../audio-vectorscope/references/VECTORSCOPE_CONTRACT.md#measured-coordinates)

Keep DC and use the same $N$ samples for every power $P_X=\sum X_n^2/N$.
The power unit is the square of the input amplitude unit. RMS is
$\sqrt{P_X}$ in the input unit. The frame obeys

$$
P_M+P_S=\frac{P_L+P_R}{2},\qquad
\operatorname{mean}(MS)=\frac{P_L-P_R}{4}.
$$

Report $F_S=P_S/(P_M+P_S)$ when the total power is positive. A measured
all-zero frame has zero component levels and an unavailable fraction.
A single hard-panned source and two nonzero orthogonal channels both
yield $F_S=1/2$. Inspect the input levels and waveform as evidence of
the cause.

If reporting a Side-to-Mid ratio in dB, use $10\log_{10}(P_S/P_M)$.
A zero numerator gives $-\infty$ for positive Mid power. A zero
denominator gives $+\infty$ for positive Side power. Two zeros leave
the ratio unavailable.

Let $C=\sum L_nR_n/N$. Then $F_S=1/2-C/(P_L+P_R)$ when the total is
positive. With equal positive channel powers, $F_S=(1-\rho_0)/2$ for
raw zero-lag correlation. For unequal powers, use the measured $C$ and
powers. For the equal-weight mono fold-down, $F_S+G=1$ using Skill #31's
retention $G$ relative to average input channel power.
[Stereo correlation contract](https://github.com/Kisuul/KestrelGaming/blob/8794831ad1805a536ddd9e68e868750327e5e37b/skills/audio-stereo-correlation/references/STEREO_CORRELATION_CONTRACT.md#mono-fold-down)

## Trace the delivered mono signal

For signed gains $g_M,g_S$, reconstruct $L'=g_MM+g_SS$ and $R'=g_MM-g_SS$.
The equivalent L/R matrix has diagonal entries $(g_M+g_S)/2$ and
off-diagonal entries $(g_M-g_S)/2$. Each row's absolute weight sum is
$\max(\lvert g_M\rvert,\lvert g_S\rvert)$. If the input magnitudes are
bounded by $A$, the resulting sample magnitudes are bounded by
$A\max(\lvert g_M\rvert,\lvert g_S\rvert)$. Equal and opposite inputs
attain the Mid and Side limits, respectively.

An aligned linear fold-down with weights $a,b$ gives
$(a+b)g_MM+(a-b)g_SS$. Equal weights of $1/2$ give $g_MM$. A shared
change to Side before the signs split still cancels in that fold-down.
A delay, gain difference, or nonlinear stage after reconstruction can
change the delivered mono result. Capture the stage where the result
changes and measure its actual output.

FFmpeg `stereotools` uses this digital matrix with matching mode,
gain, balance, and other settings. FLAC Mid/Side uses the shifted
integer sum and the full difference. Its decoder uses the difference
parity to restore the original integers.
[FFmpeg 7.1.5 source](https://github.com/FFmpeg/FFmpeg/blob/n7.1.5/libavfilter/af_stereotools.c#L221-L245) ·
[FLAC channel decorrelation](https://www.rfc-editor.org/rfc/rfc9639.html#section-4.2)

## Diagnose a frequency band

Form Mid and Side before the spectral measurement. Use the same window,
detrending, transform length, frequency support, and one-sided scaling
for both inputs. With L/R densities $D_L,D_R$ and cross density
$D_{LR}$ from $\overline X_L X_R$ on the same scale, verify

$$
D_M=\frac{D_L+D_R+2\operatorname{Re}D_{LR}}{4},\qquad
D_S=\frac{D_L+D_R-2\operatorname{Re}D_{LR}}{4}.
$$

Use the direct component spectra for small residuals. Combine linear
power over the chosen band before computing the fraction. A zero-power
band gives an unavailable fraction. Inspect the actual mono channel to
confirm the loss.
[PSD calibration](../../audio-power-spectral-density/SKILL.md) ·
[Band integration](../../audio-fractional-octave-rta/references/FRACTIONAL_OCTAVE_RTA_CONTRACT.md#psd-integration-and-coverage)

## Offline reference

Put `audio-oscilloscope/scripts` and `audio-mid-side-analysis/scripts` on
the Python module search path. Call `analyze_mid_side` with a shared
`CaptureWindow` and explicit `left_channel` and `right_channel` IDs.
The reference accepts one to 1,024 sample frames within the shared
capture's PCM limits. The result carries the exact sample support
and the original epoch and channel IDs.

Each component returns exact `samples` and `mean_square` values. The
`side_power_fraction` is exact when available. Each `rms` is binary64.
The reference compares exact squared rounding midpoints and uses
ties-to-even. The `rms_status` values are `exact_zero`, `rounded_to_zero`
for positive RMS rounded to zero, and `finite` for a nonzero rounded RMS.

Form the sum and difference before conversion. The exact midpoint of
the largest finite sample paired with itself fits. For the smallest
positive sample $\eta=2^{-1074}$, separately rounded halves can lose
a measured $\eta$. If exporting component PCM, account for
reconstruction error after rounding. Set an absolute tolerance for
quiet residuals. Measure small component powers from their samples.
Use the L/R power identities to check the analysis.
[Fixtures and tolerances](../../../tests/fixtures/AUDIO_MID_SIDE_ANALYSIS_GOLDENS.md)

Run the focused checks from the repository root.

```sh
python3 -m unittest discover -s tests -p test_audio_mid_side_analysis_reference.py
```
