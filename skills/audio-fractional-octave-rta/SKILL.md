---
name: audio-fractional-octave-rta
description: Design or audit octave and fractional-octave real-time analyzers (RTA), including IEC base-10 band geometry, Welch PSD integration, filter-bank measurement, per-channel band power, and resolution and Nyquist limits.
---

# Fractional-octave real-time analysis

Use this skill when an analyzer reports power, RMS, or level in logarithmically
spaced frequency bands. Load [audio-power-spectral-density](../audio-power-spectral-density/SKILL.md)
for density and Welch calibration, [audio-window-functions](../audio-window-functions/SKILL.md)
for leakage and resolution, and [audio-filter-design](../audio-filter-design/SKILL.md)
when the measurement uses a filter bank.

## Procedure

1. **Identify the measurement.** Record the input tap, sample rate, channel labels,
   sample units, reference level, band family and frequency range. Use Welch PSD
   integration for a digital band-power estimate. Use a band-pass filter bank
   when the measurement specifies a filter response or continuous filtered output.
2. **Calculate the bands.** Use the [base-10 geometry](references/FRACTIONAL_OCTAVE_RTA_CONTRACT.md#frequency-geometry)
   with $G=10^{3/10}$ and a 1 kHz reference. For odd denominators, 1 kHz is
   a band center. For even denominators, it is a shared band edge. Use exact
   centers and edges for analysis. Apply nominal frequencies only as labels.
   State the geometry if an existing analyzer uses a base-2 grid.
3. **Set frequency and time resolution.** Specify segment length, FFT size, window,
   hop, detrending and number of Welch segments. Check the narrowest band
   against the window's main-lobe width at the actual segment duration. Zero
   padding gives a finer integration grid. A longer input record gives finer
   resolution. Decide which bands have usable resolution for the task.
4. **Integrate linear power.** Use a correctly normalized one-sided PSD. Convert
   density to power with the bin spacing and allocate power by each cell's
   overlap with the band. Keep DC out of the logarithmic bands. Retain the
   unique Nyquist bin's power over its half-width cell. Flag incomplete
   coverage and use complete bands for ordinary readings. Average linear
   powers over complete segments, then calculate RMS and decibels.
5. **State the reference and clock.** Measure channels independently. For
   normalized PCM use $10\log_{10}(Q_b)$ dBFS with full-scale amplitude 1.
   Use a calibrated pressure chain before reporting dB SPL. Keep a display
   floor separate from the zero-power result. Preserve the exact contributing
   sample range and the source epoch. After a gap, seek or rate change, start
   a fresh epoch and refill the analysis history.
6. **Check the filter bank if one is specified.** Document the gain, actual
   response, sample rates, averaging and settling time. Check center tones,
   both edges, off-band attenuation and the response toward Nyquist. For a
   class claim, obtain the applicable IEC 61260 limits and test evidence.
7. **Verify the result.** Use a rectangular, bin-centered tone whose cell fits
   inside the band and check its power against $A^2/2$. Check adjacent bands
   against a common covered interval and total PSD power against Parseval.
   Test boundary neighbors, silence, DC, Nyquist, anti-phase
   channels, callback partitions and epoch resets. White noise has more
   power in wider bands. Ideal pink noise has equal power per equal frequency
   ratio. Check finite noise records statistically.

The [Python reference](scripts/reference_fractional_octave_rta.py) uses IEC 61260-1
frequency geometry and sample-clocked Welch estimates for normalized PCM. Its
evidence covers an offline educational estimator. A filter-class claim requires
the applicable response and other IEC performance checks. See the [contract](references/FRACTIONAL_OCTAVE_RTA_CONTRACT.md)
and [independent fixtures](../../tests/fixtures/AUDIO_FRACTIONAL_OCTAVE_RTA_GOLDENS.md)
for bounds, verification commands and a runnable example.
