---
name: audio-mid-side-analysis
description: Measure Mid and Side from aligned stereo PCM. Use to check polarity, stereo width, band-specific cancellation, and the effects of Side gain, clipping, or channel delay on mono fold-down.
---

# Mid/Side analysis

1. **Identify the tap.** Select the original left and right channel IDs
   from one aligned capture. Record the clock, epoch, rate, units, and
   exact sample bounds. Check the source wiring if it supplies recorded
   Mid and Side channels.
   [Aligned capture](../audio-oscilloscope/SKILL.md) ·
   [Channel mapping](../audio-channel-mapping/SKILL.md)
2. **Apply the stated matrix.** Use half the sum for Mid and half of
   left minus right for Side. Keep DC. Check the signs with left-only,
   right-only, and opposite-polarity pairs.
   [Matrix and levels](references/MID_SIDE_ANALYSIS_CONTRACT.md#matrix-and-levels)
3. **Measure before rounding.** Report Mid and Side RMS and their powers
   on the same samples. Divide Side power by the sum of their powers.
   Mark the fraction unavailable for measured silence. Inspect the
   source balance when interpreting the fraction.
   [Offline reference](scripts/reference_mid_side_analysis.py)
4. **Trace the delivered mix.** Predict the linear output from the Mid
   and Side gains and check the sample headroom. Measure the actual
   mono fold-down after all gains, delays and limiters.
   [Delivered mono](references/MID_SIDE_ANALYSIS_CONTRACT.md#trace-the-delivered-mono-signal)
5. **Check the affected band.** Form both waveforms from the same original
   pairs and use matching spectrum settings. Compare their band powers
   and listen to the mono output. Use a known two-tone case to check
   whether equal L/R magnitudes hide cancellation.
   [Band diagnosis](references/MID_SIDE_ANALYSIS_CONTRACT.md#diagnose-a-frequency-band) ·
   [Frozen fixtures](../../tests/fixtures/AUDIO_MID_SIDE_ANALYSIS_GOLDENS.md)

Report the matrix convention, channel and window provenance, component
levels, and measured mono path. Preserve the distinction between
positive power below the RMS display range and an exact measured zero.
