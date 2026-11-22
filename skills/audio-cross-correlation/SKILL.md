---
name: audio-cross-correlation
description: Estimate signed sample delay between PCM observations using linear cross-correlation. Use for loopback or channel alignment, lag search, peak ambiguity, polarity, reflections, and comparison with FFT-based correlation.
---

# Audio cross-correlation

1. **Identify the reference and measurement.** Record ordered channel
   IDs, taps, units, clock, epoch, rate, and sample intervals. Set the
   plausible delay range on that clock. Supply guard samples.
   [Clock and lag](references/CROSS_CORRELATION_CONTRACT.md#clock-and-lag)
2. **Choose a score and support.** Use raw products for a controlled
   probe, overlap cosine to compare shape with DC retained, or
   overlap Pearson to compare centered variation. Set minimum paired
   support and levels before searching. Use fixed support when a
   change in overlap would alter the comparison.
   [Score and gates](references/CROSS_CORRELATION_CONTRACT.md#score-and-gates)
3. **Inspect the peak and its competitors.** Use positive peaks for
   known same-polarity paths. Otherwise rank magnitudes and keep the
   sign. Check for ties, search edges, and short or quiet overlaps.
   Report both local lag and clock delay.
   [Offline reference](scripts/reference_cross_correlation.py)
4. **Check the signal path.** Replay a known offset and check how the
   peak moves. Use a distinctive probe for repeated waveforms. Inspect
   the earlier arrivals when a reflection can dominate the score.
   [Frozen fixtures](../../tests/fixtures/AUDIO_CROSS_CORRELATION_GOLDENS.md)
5. **Verify estimator changes.** Compare the entire linear curve
   before adopting an FFT. Use known fractional offsets and band
   delays to assess interpolation or frequency weighting.
   [FFT and refinements](references/CROSS_CORRELATION_CONTRACT.md#verify-fft-and-refinements)

Report the selected criterion, support, peak sign and delay, competing
lags, and the repeat measurement that supports the diagnosis.
