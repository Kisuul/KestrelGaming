---
schema: 1
id: 2026-11-26-audio-spl-metering-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; IEC 61672-1:2013 catalogue and preview, HBK microphone handbook, NTi time and frequency weighting guidance; executed pressure and time-weighting fixtures below."
---

# Skill 52 research for sound pressure level metering

## Summary

**Task outcome:** COMPLETE

Start with calibrated pressure samples and a declared frequency
weighting. Give equivalent continuous level and exponential-time
levels independent state. A pressure reference, a time window,
and a frequency weighting each affect what the reading means.
The checks cover the pressure reference, energy averaging,
and the Fast and Slow step responses.
[IEC 61672-1:2013 scope](https://webstore.iec.ch/en/publication/5708)

## Evidence

### Establish the pressure and integration interval

Record the microphone and calibrated tap, field condition, channel,
sample rate, epoch, full capture interval, and overload status.
Obtain pressure in pascals from the input conversion. If the
measurement chain has only a digital full-scale reference, report
its result in digital units. For sound in air use the reference
$p_0=20\,\mu\mathrm{Pa}$. This also fixes the reference when
expressing a pressure amplitude, peak, or mean square in dB.
[HBK Microphone Handbook, vol. 1](https://www.bksv.com/-/media/literature/Primers/be1447.ashx?hash=5D04E95B7392F12988B969B9AD14B1FA7F3C845C&la=es) ·
[Digital RMS and level references](../../../../../skills/audio-rms-crest-factor/SKILL.md)

Choose the frequency weighting and apply its filter to pressure
before squaring. Preserve the coefficient revision, sample rate,
and filter state or startup policy. A, C, and Z designate different
response profiles. Check the response against the chosen tolerances
at multiple frequencies, including the edges of the supported
band. A reference tone near 1 kHz checks scale at that frequency.
Use a separate test for the rest of the weighting curve.
[Frequency and time weighting](https://www.nti-audio.com/en/support/know-how/what-are-laeq-and-lafmax) ·
[Filter design and verification](../../../../../skills/audio-filter-design/SKILL.md)

For $N>0$ equally spaced weighted samples $p_W[n]$ on a complete
observed interval, use

$$
P_W=\frac{1}{N}\sum_{n=0}^{N-1}p_W[n]^2,\qquad
L_{W,\mathrm{eq},T}=10\log_{10}\frac{P_W}{p_0^2},\qquad
T=N/f_s .
$$

Pool compatible subintervals in linear squared-pressure units
weighted by duration. Report the observed duration and requested
duration when coverage is partial. Missing input has no squared
pressure value. An acquired zero signal can give zero measured
power. Preserve that state and apply any display floor only to
the displayed value.
[Sample-clock support](../../../../../skills/audio-timebase-sync/references/TIMEBASE_CONTRACT.md)

### Keep time weighting on the squared-pressure state

For a held squared-pressure input per sample, the exact
first-order state update is
$q[n]=\alpha q[n-1]+(1-\alpha)p_W[n]^2$ with
$\alpha=\exp[-1/(f_s\tau)]$. Fast uses $\tau=0.125$ s and
Slow uses $\tau=1$ s. Use $10\log_{10}(q[n]/p_0^2)$ for
the time-weighted level. Define initialization and retain state
across contiguous callbacks. The maximum of the A-weighted Fast
trace over the declared interval is an LAFmax estimate.
Retain the filter and detector warm-up support. Time weighting
belongs to this detector branch. The equivalent continuous level
uses the energy of its own stated interval.
[NTi time weighting and level quantities](https://www.nti-audio.com/en/support/know-how/what-are-laeq-and-lafmax) ·
[Smoothing-domain checks](../../../../../skills/audio-envelope-dynamics/SKILL.md)

### Executed checks and portable fixtures

| Probe | Verified result |
| --- | --- |
| Take a complete pressure observation with RMS 1 Pa. | The level is 93.979400 dB re 20 µPa. |
| Use two equal-duration compatible observations at 0.020 Pa RMS and 0.200 Pa RMS. | The levels are 60 and 80 dB. The combined level is 77.032914 dB. The arithmetic mean of the two level readings is 70 dB. |
| At 48 kHz start the detector state at zero. Hold the squared-pressure input at 1 Pa² for 6,000 samples, then 0 Pa² for another 6,000. Repeat for 48,000 samples per span with the Slow constant. | At one time constant both runs reach 0.632120559 Pa². After one more time constant at zero they reach 0.232544158 Pa². Splitting a constant span across callbacks preserves the result within the fixture tolerance. |

These checks verify the scalar calculation and squared-pressure
time law. A device and acoustic measurement also require
frequency response, level linearity, noise floor, overload,
and time-weighting evidence across the applicable range.

## Next action

Implement the bounded pressure-input baseline with complete-span
energy and explicit Fast/Slow state. Add a separately verified
weighting stage. Test nonfinite values, silence, changing
coverage, filter reset, and one mid-block transition. Use
calibrated hardware checks and the full cited standard before
claiming an instrument class.

## Revisit when

The pressure calibration, weighting implementation, time constant,
measurement duration, or intended instrument class changes.
