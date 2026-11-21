---
name: audio-stereo-correlation
description: Measure or audit signed zero-lag stereo correlation from aligned PCM. Use for correlation meter disagreements, low-level readings, gain and DC effects, or suspected cancellation in a mono fold-down.
---

# Stereo correlation

1. **Trace the input.** Select two channel IDs from the same original PCM
   capture. Record the tap, units, clock, epoch, sample rate, and exact
   sample bounds. Check a known impulse if the planes could be shifted.
   [Aligned capture](../audio-oscilloscope/SKILL.md)
2. **Declare the estimator.** Use the signed, zero-lag normalized dot
   product over all samples in one rectangular window. Keep DC and
   report both channel RMS levels. A zero-energy channel makes the
   coefficient unavailable. Report an exact zero cross-product as zero
   when both channels carry energy.
   [Measurement contract](references/STEREO_CORRELATION_CONTRACT.md#window-moments)
3. **Reconcile meter readings.** Match the tap, estimator, window,
   smoothing, and level gate before comparing meters. For disjoint
   windows, sum the three product totals before normalizing. A rounded
   endpoint or a quiet display needs the measurement status.
   [Comparison and timing](references/STEREO_CORRELATION_CONTRACT.md#compare-meters)
4. **Measure the actual mono output.** Identify the fold-down weights and
   take levels on the same sample support. Inspect the affected band and
   listen to the folded signal. A positive broadband reading can coexist
   with cancellation in one band.
   [Mono fold-down](references/STEREO_CORRELATION_CONTRACT.md#mono-fold-down)
5. **Verify with known signals.** Check matched and inverted channels,
   unequal gain, a silent channel, DC, and a two-tone mix. Replay the same
   tape across different callback boundaries. Compare the values on
   identical sample intervals.
   [Offline reference](scripts/reference_stereo_correlation.py) ·
   [Frozen fixtures](../../tests/fixtures/AUDIO_STEREO_CORRELATION_GOLDENS.md)

Report the channel levels, coefficient and availability, sample support,
and fold-down weights. Use the relevant band or lag measurement when the
question concerns a frequency range or alignment.
