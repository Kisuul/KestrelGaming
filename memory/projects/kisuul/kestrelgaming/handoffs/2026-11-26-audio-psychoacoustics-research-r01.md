---
schema: 1
id: 2026-11-26-audio-psychoacoustics-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch a435c790546b7aefc8ba35ba18be1d7c235f916f; ISO 226:2023; ISO 532-1:2017; Glasberg and Moore (1990); LTFAT auditory bandwidth reference; executed auditory bandwidth and in-band power checks."
---

# Skill 64 research for psychoacoustics

## Summary

**Task outcome:** COMPLETE

Choose a perceptual model for a defined quantity, level,
and presentation. The selected filter and its bandwidth
affect the amount of masking noise accumulated near a
target. The fixtures expose two effects that a single
broadband signal-to-noise ratio (SNR) can hide.
[Glasberg and Moore (1990)](https://www.sciencedirect.com/science/article/pii/037859559090170T)

## Evidence

### Keep the level reference and model explicit

For an absolute perceptual interpretation, record the
sound pressure level at the listening position, the
calibration or playback transfer, and the presentation
conditions. Level in dBFS describes the digital signal.
Keep digital level, calibrated pressure and predicted
perceptual quantity in separate fields.
[SPL metering](2026-11-26-audio-spl-metering-research-r01.md) ·
[Microphone calibration](2026-11-26-audio-microphone-calibration-research-r01.md)

ISO 226:2023 gives equal-loudness contours for pure tones
under specified conditions. Use the declared population,
presentation geometry and contour range. For a predicted
loudness quantity from stationary or time-varying
sound, consult the scope and inputs of ISO 532-1:2017
(Zwicker). Programme loudness in LKFS has its own input
and weighting contract. Name the output unit and method
each time the application mixes these quantities.
[ISO 226:2023](https://www.iso.org/standard/83117.html) ·
[ISO 532-1:2017](https://www.iso.org/standard/63077.html) ·
[Programme loudness](../../../../../skills/audio-program-loudness/SKILL.md)

### Reason about masking in a selected band

The equivalent rectangular bandwidth (ERB) of a filter
is the width of a rectangle with the same area and peak
as its power response. For the fixture, use the LTFAT
approximation $\mathrm{ERB}(f)=24.7+f/9.265$ in Hz,
with $f$ the center frequency in Hz. For a shaped noise
spectrum and a declared filter with power gain $G(f)$,
integrate noise power as $\int S_n(f)G(f)\,df$ over the
chosen one-sided frequency support. A flat $S_n$ times
ERB gives that integral when the peak power gain is unity
and the integration covers the filter.
[LTFAT auditory filter bandwidth](https://ltfat.org/doc/auditory/audfiltbw.html)

Evaluate a masking threshold only under a named masking
model or measured listening condition. Spectral placement,
sound level and masker timing can affect the report.
Keep simple in-band energy, temporal overlap, and a
listener threshold available as distinct observations.
[Glasberg and Moore (1990)](https://www.sciencedirect.com/science/article/pii/037859559090170T) ·
[Noise and SNR](2026-11-26-audio-noise-snr-sinad-research-r01.md)

### Executed checks and portable fixtures

For a flat one-sided power spectral density of
`1e-8` power units per Hz, take the response's peak power
gain as 1 and compute noise power as density times ERB.

| Center frequency | Approximate ERB | Integrated noise power |
| --- | --- | --- |
| 250 Hz | 51.683 Hz | `5.1683e-7` |
| 1,000 Hz | 132.633 Hz | `1.3263e-6` |
| 4,000 Hz | 456.432 Hz | `4.5643e-6` |

The 4 kHz filter admits about 9.4603 dB more noise power
than the 250 Hz filter in this example. This check assumes
flat noise and equal peak gain. For the second check, use
an idealized passband. Target power is `0.001`, all in
the passband. “Remote” means outside that passband. All
power terms have the same units.

| Case | In-band noise | Remote noise | Broadband SNR | In-band SNR |
| --- | --- | --- | --- | --- |
| A | `0.010` | `0.010` | `−13.0103 dB` | `−10 dB` |
| B | `0.0001` | `0.0199` | `−13.0103 dB` | `+10 dB` |

Both broadband readings use noise power of `0.020`.
Moving noise outside the passband changes the in-band
SNR by 20 dB. A real filter can pass some of the remote
energy. Effective bandwidth and SNR are verified here.
An audibility claim requires further evidence.

## Next action

Implement or select the filter model with explicit level
reference, peak gain, bandwidth and PSD convention. Give
Gauge the flat-noise scaling and fixed-total-power
fixtures. Add a measured or published check for any
claimed threshold or loudness prediction.

## Revisit when

The calibration, listener condition, filter or masking
model, sample rate, or interpretation of the score changes.
