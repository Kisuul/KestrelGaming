---
name: audio-rms-crest-factor
description: Implement and audit finite-window RMS, mean-square amplitude, sample peak, crest factor, and level conversions with exact amplitude-versus-power references, window and channel policies, silence semantics, and analytic verification.
---

# RMS and crest factor — amplitude and dynamics with declared references

## Activate when

Use for sample-window RMS measurements, mean-square energy proxies, sample-peak/RMS ratios, crest factors, RMS trend displays, or audits of these computations. This is not a VU meter, standardized broadcast loudness implementation, true-peak instrument, or calibrated dB SPL meter. For an upstream signal-pipeline redesign load [audio-dsp-core](../audio-dsp-core/SKILL.md). For spectral noise density load [audio-power-spectral-density](../audio-power-spectral-density/SKILL.md).

## Procedure

1. **Define the input and measured point.** State normalized PCM or physical sample units, gain/processing tap, channel configuration, sample rate, frame length, and frame timestamps. Distinguish raw float sample excursion beyond ±1 from integer PCM clipping and do not silently clamp valid floating-point values.
2. **Define every quantity.** Sample peak P = max(|x[n]|), mean square Q = sum(x[n]²)/M, RMS = sqrt(Q), crest ratio = P/RMS for nonzero RMS, crest in dB = 20 log10(P/RMS). For exact silence (P=RMS=0), the crest factor is undefined, **not** zero, one, or a fabricated finite value. Specify the intentional display policy separately. For extremely small finite samples, compute RMS with a scaled sum of squares and distinguish mean-square underflow from exact digital silence.
3. **Separate decibel conventions.** An amplitude ratio uses 20 log10(A/A_ref); a mean-square/power ratio uses 10 log10(Q/Q_ref). For sample amplitude normalized to unit *peak*, a full-scale on-bin sine has RMS ~0.7071 (about -3.0103 dB relative to unit amplitude). AES17 full-scale RMS conventions differ; do not label a unit-amplitude reference as an AES17 meter without adapting its reference definition. A zero amplitude maps mathematically to negative infinity in log representation.
4. **Treat channels independently before aggregating.** For stereo, measure L and R separately; never sum raw channels before squaring unless measuring the intentionally mixed-down signal. State whether a combined result is max-channel, mean power, summed power, or a specified downmix. A phase-inverted L/R test must not disappear from energy measurement.
5. **Distinguish windowing from meter ballistics.** An M-sample rectangular RMS window is not the same as a weighted, exponential, or standard-specific level detector. Define averaging topology, overlap, smoothing, attack/release, hold times, and reset policy whenever those are added. Display refresh rate must not alter the underlying measurements.
6. **Handle numerical failures honestly.** Reject empty or nonfinite samples; detect overflow or invalid accumulated energy rather than emitting a deceptive finite reading. Use a scaled sum of squares to stabilize RMS. Even where RMS is representable, the squared mean can underflow to zero; the reference records `mean_square_underflowed=True` instead of identifying it as silence. If an isolated subnormal impulse's RMS itself underflows, `rms_underflowed=True` distinguishes this from exact silence; mean-square overflow fails closed. For nonzero amplitudes, compute logarithmic ratios as `20*(log10(amplitude)-log10(reference))`, not by dividing before logging. Preserve discontinuity metadata; lost samples are not silence.
7. **Verify fixtures.** Use the [level reference](references/LEVEL_FIXTURES.md), [small oracle](scripts/reference_levels.py), and [regression tests](../../tests/test_audio_levels_reference.py). Test silence, DC, impulse, rectangular sine, full-scale sine, stereo anti-phase, and nonfinite inputs. Compare analytical values rather than accepting plausible screen movement.

## Acceptance gate

The sample/temporal window, sample-level reference, channel policy, silence and overflow semantics, and executed fixture results must be recorded. Do not substitute this technique for standardized programme loudness, physical acoustic level, VU ballistics, or true-peak oversampling. Follow [Kestrel verification](../../kestrel/VERIFICATION.md).

## Sources

- [AES17-2020 official preview (scope and level definitions)](https://www.aes.org/publications/standards/preview.cfm?ID=21) — full-scale and dBFS definitions are standard-dependent.
- [ITU-R BS.1770-5](https://www.itu.int/rec/R-REC-BS.1770) — true peak and programme loudness require other defined algorithms.
- [Digital reference-convention comparison](https://support.listeninc.com/hc/en-us/articles/212762166-What-Sensitivity-Should-I-Use-For-My-Digital-Device) — distinguishes peak-normalized unit amplitude from AES17 RMS full-scale.
