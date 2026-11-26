---
schema: 1
id: 2026-11-26-audio-microphone-calibration-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; IEC 60942:2017, IEC 61094-3 and IEC 61094-5, NIST microphone field sensitivity guidance; executed calibration-scale, gain-drift and uncertainty examples below."
---

# Skill 53 research for microphone calibration

## Summary

**Task outcome:** COMPLETE

Calibrate the microphone and recording path at a named tap.
Use the level and frequency that apply to the actual calibrator,
microphone, and coupler. Preserve that calibration with the gain
settings and measurement epoch. A scalar sensitivity at the
calibration frequency is the first result. Frequency, field, and
phase correction require their own data.
[IEC 60942:2017 scope](https://webstore.iec.ch/en/publication/30045) ·
[SPL metering research](2026-11-26-audio-spl-metering-research-r01.md)

## Evidence

### Measure the chain at the chosen tap

Identify microphone, input, instrument or interface, calibrator,
adapter, and serial or certificate reference. Record the applied
pressure level and calibration frequency, applicable environmental
corrections, tap, rate, gain, orientation and field condition.
Use a settled acquisition at fixed gain. Check for clipping,
gain control, a poor seal or unwanted signal. Inspect the
fundamental and residual energy before trusting the reading.
Repeat the acquisition after reseating the calibrator when
repeatability matters.
[IEC 61094-5 pressure sensitivity scope](https://webstore.iec.ch/en/publication/24988) ·
[Measurement provenance](../../../../../skills/audio-analysis-provenance/SKILL.md)

If the calibration pressure level is $L_{\mathrm{cal}}$ dB re
$20\,\mu\mathrm{Pa}$, the RMS pressure is
$p_{\mathrm{cal}}=20\,\mu\mathrm{Pa}\cdot10^{L_{\mathrm{cal}}/20}$.
With a measured calibrator tone RMS $x_{\mathrm{cal}}$ at the
declared tap, use $K=p_{\mathrm{cal}}/x_{\mathrm{cal}}$ in
pascals per tap unit. Use the same amplitude convention on both
sides. Document whether the reference observation is a sine fit
or band-limited RMS and how DC and background enter it. For a
linear chain with microphone sensitivity $S$ V/Pa and downstream
conversion $G$ tap units/V, $K=1/(GS)$ at the stated frequency.
An unknown $G$ prevents applying a microphone-only certificate
directly to PCM. Reject zero, clipped, or otherwise unusable
references.
[PCM scaling](../../../../../skills/audio-sample-formats/SKILL.md) ·
[RMS convention](../../../../../skills/audio-rms-crest-factor/SKILL.md)

### Respect the calibration domain

Keep the full traceable record with each calibrated result.
A gain or front-end processing change invalidates direct
reuse unless its effect was measured. If a pre/post check
changes on the same calibrator, record the shift and its sign.
Use the applicable uncertainty or drift limit to judge affected
spans. A correction needs evidence about when the change occurred.

A coupler pressure calibration and a free-field or diffuse-field
calibration describe different conditions. Microphone response
can vary with frequency and angle. For a correction curve record
source, field, incidence, gain units, correction sign, supported
frequencies and interpolation. If sensitivity is in V/Pa, divide
the measured voltage by sensitivity. If a file already gives
an inverse correction, apply that convention once. A magnitude
curve alone omits phase information. Validate frequency response
separately when the task needs broadband accuracy.
[NIST on microphone fields](https://www.nist.gov/publications/importance-free-field-calibration-microphones) ·
[IEC 61094-3 free-field sensitivity scope](https://webstore.iec.ch/en/publication/25105)

Track uncertainty from the reference level, coupler fit,
repeatability, front-end gain, and relevant response correction.
For independent standard uncertainties expressed in the same dB
domain, use the root-sum-square. Retain covariance when terms
share a reference. Keep an expanded uncertainty with its stated
coverage factor. Record frequency and orientation limitations
separately from scalar gain uncertainty.

### Executed checks and portable fixtures

| Probe | Verified result |
| --- | --- |
| Use a synthetic 1 kHz calibrator level of 94.10 dB re 20 µPa, measured at 0.05000 tap units RMS. Measure another observation at 0.01250 RMS on that gain. | The implied reference is 1.0139814165 Pa RMS. $K=20.27962833$ Pa per tap unit. The second observation gives 82.058800 dB. |
| Double the gain for the second observation and reuse the old $K$. Then test a post-check of 0.04900 RMS on the original calibrator. | The stale-scale result reads 6.020600 dB higher. The calibrator reading has moved by −0.175478 dB. The updated $K$ would be $50/49$ times the old value. |
| Measure 20 mV RMS at a frequency whose qualified sensitivity is 0.100 V/Pa. Compare the result given by an unqualified constant 0.050 V/Pa. | The two pressures are 0.200 and 0.400 Pa RMS. |
| Use independent standard uncertainties of 0.20, 0.10 and 0.15 dB. | The combined standard uncertainty is about 0.269258 dB. |

The fixture values exercise scale, sign and applicability.
An actual calibration needs an identified instrument and a
traceable reference with its conditions and uncertainties.

## Next action

Implement a bounded calibration record and application path.
Keep raw readings and calibration IDs, and test wrong gain,
unsupported frequency, zero reference, and double application
of a correction. Verify an instrument and coupler before
using the result for a field measurement.

## Revisit when

The microphone, coupler, field, gain, device, sample rate,
frequency correction, or traceable reference changes.
