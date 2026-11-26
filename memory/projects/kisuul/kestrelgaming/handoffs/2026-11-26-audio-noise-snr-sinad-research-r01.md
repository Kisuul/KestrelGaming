---
schema: 1
id: 2026-11-26-audio-noise-snr-sinad-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; Analog Devices MT-001 and MT-003, SciPy 1.17.0 Welch, Kestrel PSD contract; executed noise accounting, PSD integration, and quantization fixtures below."
---

# Skill 47 research for noise, SNR and SINAD

## Summary

**Task outcome:** COMPLETE

Define what counts as signal, noise and distortion. Measure
their powers over a declared band and operating state. A
quiet-input noise result and a driven residual answer different
questions. Record which harmonics and other spurs the calculation
excluded, and combine powers before conversion to decibels.
[THD and residual research](2026-11-26-audio-thd-thdn-research-r01.md)

## Evidence

### Fix the reference and the operating state

Record the tap, channel, device gain, source termination or
stimulus, bandwidth, weighting filter, time range and amplitude
reference. Separate digital full-scale units from calibrated
voltage or pressure. Noise measured with a quiet input describes
that input condition. To compare it to a driven measurement,
retain gain, band and configuration. Signal-dependent errors,
gating and processing state can change the driven result.

Use $P_S$ for the reference signal power, $P_N$ for the declared
noise power, and $P_D$ for separately admitted distortion
power. For disjoint contributions use

$$
\mathrm{SNR}=10\log_{10}(P_S/P_N),\qquad
\mathrm{SINAD}=10\log_{10}[P_S/(P_N+P_D)] .
$$

For the coherent example below, $P_S$ is the fundamental and
$P_N$ includes the nonharmonic residual. For dynamic ADC
measurements, state whether DC, harmonics and other lines are
excluded from the reported noise. A nonharmonic line can be
counted in a residual without asserting a stochastic cause.
With matched definitions and bandwidth this SINAD is the
negative dB value of fundamental-relative THD+N. If the THD+N
denominator is total power, the comparison uses a different
reference. Return unsupported when $P_S$ is unavailable.
[Analog Devices MT-003, SNR and SINAD](https://www.analog.com/media/en/training-seminars/tutorials/MT-003.pdf)

### Integrate in linear power

Use a time-domain mean square with the band/weight filter
documented, or an appropriately calibrated PSD. A bin density
in squared units per Hz needs a bandwidth factor. For aligned
whole bins use the bin width once, and retain the one-sided
endpoint convention from the chosen PSD. For fractional-band
integration, state the bin model and how overlap is computed.
Pool powers on comparable support before taking logarithms.
FFT bin height, density, and integrated noise level answer
different questions.
[PSD calibration](../../../../../skills/audio-power-spectral-density/references/PSD_CALIBRATION.md#normalization) ·
[SciPy 1.17.0 Welch](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.welch.html)

For a median, trimmed mean, or other robust estimate, state
what distribution and correction are assumed. Keep nonstationary
intervals visible with their sample ranges. Repeated or
overlapping windows share data, so estimate uncertainty from
an appropriate measurement model or independent captures.
Report a floor or upper bound when the measurement chain
limits the noise result. A zero measured digital residual can
be a valid observed value on that tap.

### Bound the quantizer model

The ideal full-scale sine relation $6.02N+1.76$ dB assumes
$N$ bits, an approximately uniform quantization error of
one-step peak-to-peak, and noise integrated over the Nyquist
band. Low-level or coherent inputs can make the error
structured. State stimulus amplitude, bandwidth and the
formula before calculating an equivalent number of bits from
SINAD. Treat it as a performance result under those conditions.
[Analog Devices MT-001](https://www.analog.com/media/en/training-seminars/tutorials/MT-001.pdf)

### Executed checks and portable fixtures

| Probe | Verified result |
| --- | --- |
| Use the coherent Skill #45 mixture. Exclude DC and assign the known 3 kHz harmonic to distortion and the 1.37 kHz spur to the noise term for this accounting exercise. | $P_S=0.125$, $P_D=0.0000125$, $P_N=0.000002$. SNR is 47.95880 dB and SINAD is 39.35542 dB. |
| Integrate an ideal flat density of $10^{-9}$ squared units/Hz from 100 to 1,100 Hz, then from 100 to 2,100 Hz. | The noise powers are $10^{-6}$ and $2\cdot10^{-6}$. The wider band adds 3.01030 dB. |
| Average two equal-duration power observations at $10^{-6}$ and $10^{-4}$ relative to unit power. | The linear mean followed by the log gives −42.96709 dB. Averaging the two dB readings gives −50 dB. |
| At 48 kHz render a coherent 1 kHz sine with a peak of 0.2 quantizer steps and round to the nearest step. | Every output is zero. The error is entirely signal-correlated and its mean square is 0.02 steps squared. |

For the PSD check draw 4,096 samples uniformly in
`[-0.05,0.05)` with NumPy 2.3.5 PCG64 seed 470047. Use seven
complete 1,024-sample periodic Hann windows with hop 512 and no
detrending. The mean of their window-energy-normalized mean
squares is 0.000840767548041 in squared PCM units. Integrating
SciPy 1.17.0 Welch density on FFT grids of 1,024 and 2,048
points agrees with that time-domain value within `1.41e-18`.
This checks noise-power calibration and accounting. Hardware
floor and long-term noise statistics need measurement.

## Next action

Implement the bounded power and ratio procedure with explicit
reference, band and spur membership. Give Gauge a nonharmonic
spur, noisy silence, a bandwidth change, and a small quantized
signal. Require evidence of comparable gain and support when
using a quiet-input noise acquisition to explain a driven test.

## Revisit when

The signal reference, operating state, integration band, weighting,
spur exclusions, or uncertainty model changes.
