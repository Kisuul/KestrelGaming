# Noise power, SNR, and SINAD

[Capture](#capture-and-reference) · [Band power](#band-power) ·
[Driven ratios](#driven-ratios) · [Quantization](#quantization)

## Capture and reference

A quiet-input measurement gives the in-band power at
the declared termination and processing state. A
driven measurement gives the output signal and residual
while applying a stimulus. Record the tap, channel, units,
clock, capture interval, gain, termination or stimulus,
weighting, band, and DC policy. Retain the measured floor
or a bound when the chain limits a noise measurement.

Compare quiet and driven powers after checking gain,
calibration, band, weighting, and analysis support.
The operating state can change with signal level or
processing. Subtract powers from different captures
only if a verified model supports that operation.

Use power in squared PCM units. Convert to a physical
unit with the calibration at the selected tap. To give
a noise level in dB, declare a positive reference power
in the same units. For example, with a normalized
full-scale sine of peak one at 0 dBFS, the reference
power is 0.5. The report's \`noise_level_db\` method
uses the supplied reference and returns $-\infty$ dB
for zero measured noise.

Pass one complete \`CaptureWindow\` to the reference.
A mono capture can use its only channel by default.
Name the channel for a multichannel capture. The
report retains the epoch, selected channel, half-open
interval, exact band, and bin width. The bounded reference
uses a rectangular record, no padding, unity weighting,
and up to 1,024 frames. The driven capture needs a
known coherent interior bin. The quiet capture accepts
a record of at least two frames.
[Capture](../../audio-oscilloscope/SKILL.md) ·
[Coherent capture](../../audio-thd-thdn/references/THD_THDN_CONTRACT.md#capture-and-bin-power)

## Band power

The PSD grid has spacing $\Delta f=F_s/N_{\mathrm{FFT}}$.
For one-sided density $S_{xx}[k]$ in squared PCM
units per Hz, the integrated bin power is
$p[k]=S_{xx}[k]\Delta f$. Use the one-sided endpoint
weights in the PSD. DC and even Nyquist are unpaired.
The highest odd-length bin is paired.

Give exact integer or rational band endpoints in Hz
from zero through $F_s/2$. The reference admits a bin
when its center frequency lies between the inclusive
endpoints. It excludes DC by default and keeps the
raw DC power in the ledger. The bin role \`excluded\`
records a rejected band or DC decision. Fractional
edges in other methods need an integration model.
A rectangular band of bin centers is the profile
for the reference below.

\`measure_quiet_noise\` sums every admitted bin into
noise power. Signal power and driven ratios are
unavailable. The status is \`no_stimulus\` because
the caller declared a quiet-input capture. For signal
ratios, use the driven method with a declared bin.

Use the accepted coherent power calculation in both
capture modes. It removes the mean for the AC DFT,
retains the squared original mean at DC, and scales
PCM before the DFT. Sum the represented bin powers
as fractions. The DFT sets the AC measurement
precision.

For a weighted noise measurement, document the time
filter or the frequency-domain power weight and apply
calibration before integrating. For Welch, use complete
frames, a declared window energy, detrending, and hop.
Pool linear density on the same grid or integrate on
a common declared band before pooling powers. Check
time-domain window-energy-normalized mean square over
the same support. Preserve records of nonstationary
intervals. Overlapping frames share samples. Use an
uncertainty model or independent captures for
statistical claims.
[PSD normalization](../../audio-power-spectral-density/references/PSD_CALIBRATION.md#normalization) ·
[SciPy Welch](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.welch.html)

## Driven ratios

Pass a \`ThdProfile\` to \`measure_driven_noise\` to
declare the known bin, harmonic orders, band, DC
policy, and minimum fundamental power. Name any
nonharmonic lines to exclude from SNR with a tuple
of distinct positive bin indices. Resolve this list
from measured or declared spur evidence. Keep the
raw bin powers and label each admitted bin once.

| Power | Membership |
| --- | --- |
| $P_S$ | The measured fundamental bin, with its qualification status |
| $P_D$ | Admitted bins for the declared harmonics |
| $P_X$ | Admitted declared spurs excluded from the SNR noise term |
| $P_N$ | Other admitted nonfundamental bins |
| $P_R$ | Every admitted nonfundamental bin |
| $P_B$ | Every admitted bin |

Reject a spur exclusion that names the fundamental,
DC, or a declared harmonic bin. A declared spur
outside the band keeps its bin power with role
\`excluded\` and contributes zero to $P_X$. The
harmonic list reports out-of-band and above-Nyquist
orders. Report a possible fold as evidence and keep
the observed bin's declared membership. Noise and spur
membership describe the accounting. To establish a
physical cause, use a discriminating signal or capture.

Sum numerator and denominator powers directly over
their memberships. Then $P_R=P_N+P_D+P_X$. When the
fundamental is admitted, $P_B=P_S+P_R$. A weak
residual can disappear from the difference of
rounded total and signal powers.

$$
\mathrm{SNR}_{\mathrm{dB}}=10\log_{10}(P_S/P_N),
\qquad
\mathrm{SINAD}_{\mathrm{dB}}=10\log_{10}(P_S/P_R).
$$

A spur removed from $P_N$ remains part of the
full-residual SINAD denominator. With no spur mask,
$P_R=P_N+P_D$. For matching membership and signal
power, SINAD is the negative dB value of Kestrel's
fundamental-relative THD+N. Kestrel's total-relative
THD+N uses $P_B$ as reference. Read the actual
equation and bandwidth when comparing instruments.
[THD+N ratios](../../audio-thd-thdn/references/THD_THDN_CONTRACT.md#ratio-references) ·
[Analog Devices MT-003](https://www.analog.com/media/en/training-seminars/tutorials/MT-003.pdf)

A driven signal qualifies when its bin is admitted,
its power is positive, and it meets the declared
floor. Equality at a positive floor qualifies. Choose
a floor from the measurement's usable signal level.
An out-of-band, absent, or below-floor signal leaves
its reported powers available and both ratios
unavailable. A qualified signal and an exact zero
denominator give $+\infty$ dB for that ratio.

## Quantization

The ideal $6.02b+1.76$ dB result for $b$ bits uses
a full-scale sine and an approximately uniform error
spanning one quantizer step. It integrates noise over
the Nyquist band. A coherent low-level input can
produce signal-correlated error. For example,
a sine with peak 0.2 steps quantizes to zero under
nearest-step rounding. Its error power is
0.02 steps squared. The uniform-error model gives
$1/12$ step squared.

For the full-scale sine convention, equivalent bits
are $(\mathrm{SINAD}_{\mathrm{dB}}-1.76)/6.02$.
Report the stimulus amplitude, band, and reference
with that performance result.
[Analog Devices MT-001](https://www.analog.com/media/en/training-seminars/tutorials/MT-001.pdf) ·
[Verified fixtures](../../../tests/fixtures/AUDIO_NOISE_SNR_SINAD_GOLDENS.md)
