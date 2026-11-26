---
schema: 1
id: 2026-11-26-audio-intermodulation-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; Audio Precision automotive amplifier test note, Analog Devices MT-012, Kestrel spectrum calibration; executed polynomial and alias fixtures below."
---

# Skill 46 research for intermodulation distortion

## Summary

**Task outcome:** COMPLETE

Start with a coherent two-tone measurement. Predict the
product frequencies, record their levels individually, and
declare what the ratio uses as reference. Distinguish actual
frequency separation from a collision on the sampled frequency
grid. Two-tone products and single-tone harmonics test different
behavior of a nonlinear path.
[Analog Devices MT-012](https://www.analog.com/media/en/training-seminars/tutorials/mt-012.pdf) ·
[THD research](2026-11-26-audio-thd-thdn-research-r01.md)

## Evidence

### Choose a two-tone question

Specify both stimulus frequencies, phases, peak levels, sample
rate and support. Identify the source and measurement taps.
Check the realized stimulus with the measurement path or a
loopback at a comparable level. Products already present there
limit conclusions about a downstream device. Test at several
drive levels while retaining source and response amplitudes.
For a coherent first reference, use an unpadded rectangular
window and distinct interior FFT bins.
[Test-signal research](2026-11-26-audio-test-signals-research-r01.md) ·
[Coherent FFT calibration](../../../../../skills/audio-fft-spectrum/SKILL.md)

Select the test by the behavior it probes. In the SMPTE-style
example described by Audio Precision, a large 60 Hz tone and a
smaller 7 kHz tone have an amplitude ratio of 4:1. Measure
specified sidebands around the higher tone to inspect modulation.
A high-frequency two-tone difference-frequency test places
products near the tone spacing or around the carriers. Fix the
included sidebands, band, filters, and carrier reference before
comparing a published ratio. Keep the raw line measurements
with any aggregate.
[Audio Precision amplifier testing, DFD and SMPTE IMD](https://www.audioprecision.com/fileadmin-ap/technical-library/Audio-Precision-AppNote-Automotive-Audio-Amplifier-Testing.pdf?force=)

### Predict components and support

For a controlled memoryless example, let
$x=A\cos(2\pi f_1t)+B\cos(2\pi f_2t)$ and
$y=x+a_2x^2+a_3x^3$, with $0<f_1<f_2$. Expanding the cross
terms gives these peak amplitudes when the lines are isolated.

| Product | Peak amplitude in this model |
| --- | --- |
| $f_2-f_1$, $f_1+f_2$ | $\lvert a_2 A B\rvert$ each |
| $2f_1-f_2$ | $3\lvert a_3 A^2 B\rvert/4$ |
| $2f_2-f_1$ | $3\lvert a_3 A B^2\rvert/4$ |

The cubic expressions assume the specified near-carrier
frequencies are positive. A negative frequency of a real
cosine maps to its absolute value. These predictions follow
from the product-to-sum identities in this model. The
polynomial also changes carriers and produces single-tone
harmonics. Measure the actual output carrier if it is the
ratio denominator. If grouping isolated lines, sum their
powers and take the square root for an amplitude ratio.
Report the reference, for example one carrier in peak units
or the root-sum-square of both carriers.

Include expected harmonics and other products in the collision
check. An above-Nyquist component may be rejected by the
measurement filter, or appear folded in a digital nonlinearity
or inadequately filtered capture. Apply the expected sample-rate
mapping before interpreting a bin. If two components occupy
one observed bin, its complex sum cannot establish their
separate amplitudes. Change carrier frequencies, support or sample
rate for a discriminating check.
[Harmonic peaks and gates](../../../../../skills/audio-harmonic-analysis/SKILL.md) ·
[Analog Devices MT-012](https://www.analog.com/media/en/training-seminars/tutorials/mt-012.pdf)

### Executed checks and portable fixtures

| Probe | Verified result |
| --- | --- |
| At 48 kHz for 4,800 samples use cosine-phase tones at 7 and 8 kHz with $A=0.2$, $B=0.1$, and $a_2=0.05$, $a_3=0.1$. | Peak amplitudes at 1, 15, 6 and 9 kHz are 0.001, 0.001, 0.0003 and 0.00015 respectively. |
| Double both input peak amplitudes with the same polynomial. | The specified second-order amplitudes scale by 4 and the third-order amplitudes by 8, within `1e-11` of those factors. |
| Use 19 and 20 kHz at peaks 0.2 and 0.1 and apply only $y=x^2$ in two 0.1 s captures, at 96 and 48 kHz. | The sum product has peak amplitude 0.02 at 39 kHz in the 96 kHz calculation, and folds to 9 kHz in the 48 kHz calculation. |

The results compare the algebra with one-sided FFT amplitudes
of synthetic input. Audio path nonlinearities, input-source
distortion, metering filters, and formal standard conformance
require their own checks.

## Next action

Implement a profile-driven product list and bounded coherent
measurement. Report carrier and product amplitudes, declared
ratio, and collision or alias limits. Compare a linear loopback,
separate square/cubic examples, and a level sweep before
interpreting a new pair of tones.

## Revisit when

The two-tone profile, measurement chain, input level, band,
product definitions, or ratio denominator changes.
