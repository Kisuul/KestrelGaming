# THD and THD+N measurement contract

## Capture and bin power

Record the stimulus, drive level and units, settled interval,
tap, channel, epoch, rate, and measurement weighting. Check
for clipping and capture gaps. When comparing measurements,
use the same band, DC policy, weighting, and ratio reference.

The offline reference accepts a complete
[scope capture](../../audio-oscilloscope/SKILL.md) with one
selected channel and 3 to 1,024 frames. Keep the half-open
capture interval and its exact sample rate $F_s$. Use a
rectangular window, DFT length equal to frame count $N$, and
known bin $0<k_1<N/2$. This profile assumes that the
stimulus is coherent and that the fundamental bin resolves
the line. Settle and verify the stimulus before measuring.
[Timebase contract](../../audio-timebase-sync/references/TIMEBASE_CONTRACT.md) ·
[FFT calibration](../../audio-fft-spectrum/references/FFT_CALIBRATION.md#frequency-layout-and-amplitude-convention)

Let $X[k]$ be the unnormalized DFT. The integrated one-sided
bin power is

$$
p[k] = S_{xx}[k]\frac{F_s}{N}
     = c_k\frac{|X[k]|^2}{N^2},
\qquad f[k]=k\frac{F_s}{N}.
$$

Use $c_k=1$ for DC and the even-length Nyquist bin. Use
$c_k=2$ for the remaining bins, including the highest bin of
an odd-length DFT. A real interior sine with peak amplitude
$A$ contributes $A^2/2$. A Nyquist sequence $A(-1)^n$
contributes $A^2$. The sum over all bins gives the record
mean square in squared PCM units.
[PSD normalization](../../audio-power-spectral-density/references/PSD_CALIBRATION.md#normalization)

The reference calls the PSD oracle with computational bin
width one, then labels the bins with the exact physical
frequencies. It scales PCM by a common power of two for the
DFT and restores power units after the calculation. In a
rectangular, unpadded DFT, removing the mean affects only
DC in exact arithmetic. The reference computes DC power
from the PCM mean and uses the mean-removed samples for
the AC bins. It accumulates the represented bin powers as
fractions. The DFT uses binary64 arithmetic and sets the
precision of the AC powers.

Use inclusive band endpoints in Hz from zero through
$F_s/2$. This profile uses exact integer or rational
endpoints and admits bins by center frequency. The default
band includes all positive-frequency bins through Nyquist.
Enable DC separately to admit it when the band includes
zero. The reference uses unity weighting. Pass the capture
and a `ThdProfile` to `measure_thd_thdn`. Name the channel
for a capture with more than one channel. The report keeps
all one-sided bins and each admission decision.

## Harmonics and residual

Give the reference up to 64 distinct harmonic orders of
two or greater. The default is 2 through 24. For each
order $h$, compute the nominal bin $h k_1$ and record its
disposition.

| Disposition | Accounting |
| --- | --- |
| Admitted | The nominal bin is at or below Nyquist and lies in the band. Add its power once. |
| Out of band | The nominal bin exists outside the band. Exclude its power from both distortion and residual. |
| Above Nyquist | The nominal frequency is above $F_s/2$. Record the possible folded bin for diagnosis. |

A possible fold can coincide with another harmonic, the
fundamental, DC, or a nonharmonic bin. The reference
counts each observed bin by its own assignment. Use a
different rate or controlled band limit to investigate a
suspected alias. A component that shares a bin with a
line is unresolved within this profile.
[Harmonic assignment](../../audio-harmonic-analysis/SKILL.md)

| Power | How to obtain it |
| --- | --- |
| $P_1$ | Power at $k_1$. Retain the measured power and the qualification status even when its bin is excluded. |
| $P_D$ | Sum of the admitted harmonic-bin powers. |
| $P_R$ | Sum of all admitted bin powers except $k_1$. It includes admitted harmonics, hum, nonharmonic spurs, noise, and enabled DC. |
| $P_B$ | Sum of all admitted bin powers. |

Form $P_R$ directly. Subtracting rounded $P_1$ from
rounded $P_B$ can lose a weak residual. An admitted
fundamental and this bin partition give $P_B=P_1+P_R$
and $0\le P_D\le P_R$. A harmonic order omitted from
the profile can still contribute to $P_R$.

## Ratio references

| Quantity | Numerator power | Reference power |
| --- | --- | --- |
| THD | $P_D$ | $P_1$ |
| Fundamental-relative THD+N | $P_R$ | $P_1$ |
| Total-relative THD+N | $P_R$ | $P_B$ |

For powers $P_a$ and $P_b$, return amplitude ratio
$\sqrt{P_a/P_b}$, percent $100\sqrt{P_a/P_b}$, and
level $10\log_{10}(P_a/P_b)$ in dB. Keep the four
powers with the named ratios. A ratio with zero numerator
and a qualified reference gives zero and $-\infty$ dB.
Return unavailable ratios when the fundamental is out of
band, has zero power, or falls below the declared power
floor. Equality at a positive floor qualifies. Choose
the floor in squared PCM units from the measurement's
usable reference level.
[Audio Precision ratio conventions](https://www.audioprecision.com/news/more-about-thdn-and-thd)

## Off-bin checks

An off-bin tone occupies several rectangular FFT bins.
Removing its nearest bin can leave substantial fundamental
energy in the residual. Padding samples the windowed
spectrum on a finer grid with the same record duration.
For a tapered spectrum, declare the power normalization,
line-integration region, and the separation needed for a
nearby line.

For a known off-bin frequency, fit sine and cosine on
the actual capture samples. Use integer sample offsets
from a local origin to form the phase. Declare any DC
column. Check fit rank and conditioning with the chosen
span and columns. Evaluate the fitted fundamental and
residual on the same support. Measure finite-span powers
there. The identity $A^2/2$ assumes a span with the
corresponding phase average.

An unweighted least-squares projection onto the
fundamental alone gives an orthogonal residual on its
fit interval. A joint fit followed by removal of just
the fundamental, or a different weighting or band in the
power calculation, can leave cross terms. Measure the
powers separately unless the decomposition is orthogonal
under the reported weighting and band. For a notch,
measure its rejection, settle time, and response at
nearby frequencies. Check sensitivity to stimulus
frequency error, drift, noise, and a nearby spur.

The reference implements the coherent profile. The
off-bin comparisons are fixture checks for choosing
a rejection method. Instrument or standards claims
require a specified test method, bandwidth, calibration,
and uncertainty.
[Fixture values](../../../tests/fixtures/AUDIO_THD_THDN_GOLDENS.md)
