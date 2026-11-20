---
name: audio-spectral-descriptors
description: Measure or audit centroid, RMS spread, rolloff, flatness, crest, entropy, and flux from a calibrated one-sided PSD. Use for spectral shape and frame-to-frame changes, including unexpected effects of gain, band selection, or sample timing.
---

# Audio spectral descriptors

Use this skill to describe where frame power lies or how it changes. For a peak
tone amplitude, use [the FFT amplitude skill](../audio-fft-spectrum/SKILL.md).

1. **Trace the PSD.** Select one channel from one original analysis profile.
   Record the tap, calibration, amplitude unit, window, detrending, sample rate,
   FFT length, and sample interval. Keep the source clock and epoch. For a
   multiresolution view, retrieve the contributing profile before measuring.
   [PSD calibration](../audio-power-spectral-density/SKILL.md) ·
   [Multiresolution spectra](../audio-multiresolution-spectrum/SKILL.md)
2. **Declare the frequency support.** Use a half-open band of bin centers.
   Specify DC and even-length Nyquist inclusion. Assign each selected ordinate
   its full power, $q_k=S_{xx}[k]f_s/N$. Keep the one-sided factors that the
   PSD already contains. To allocate power across a fractional band edge, use
   the [RTA cell model](../audio-fractional-octave-rta/SKILL.md).
3. **Choose the quantity.** Use centroid and RMS spread for the location and
   width of the power distribution. Use rolloff for the first center that
   reaches a specified fraction. Count equality as a crossing. Use flatness,
   crest, or entropy to describe how power is distributed across the bins.
   [Definitions and units](references/SPECTRAL_DESCRIPTORS_CONTRACT.md#frame-descriptors)
4. **Preserve measurement states.** Check every PSD ordinate for validity.
   Distinguish an empty band, zero selected power, and numerical underflow.
   For a positive-power selection with an exact zero ordinate, flatness is
   zero. Evaluate positive ordinates in the log domain.
5. **Compare adjacent frames.** Match the source, channel, clock, epoch, and
   analysis settings. Check the exact next sample index and use identical bin
   selection. Report power flux in squared amplitude units. Report shape flux
   as a dimensionless change between two positive-power distributions. After a
   seek or gap, reset the comparison and prime it with a complete frame.
   [Sample-clock rules](../audio-timebase-sync/SKILL.md)
6. **Diagnose with a controlled signal.** If uniform gain moves a centroid,
   check the tap for clipping or other processing. Check the input units, grid,
   weighting, and floor. Use two bins at 100 and 200 Hz with a 1:3 power ratio.
   The power centroid is 175 Hz. Verify an exact rolloff tie and an epoch break.
   [Analytic and adversarial fixtures](../../tests/fixtures/AUDIO_SPECTRAL_DESCRIPTORS_GOLDENS.md)
7. **Report the limits.** Include channel, sample interval, bin support, units,
   status, and rolloff fraction with the results. A different grid or window can
   change the descriptors. Keep feature values apart from display transforms.
   For onset detection, specify an event and timing model around the flux.

Use the [offline reference](scripts/reference_spectral_descriptors.py) to check
the arithmetic in a target implementation. See the
[measurement contract](references/SPECTRAL_DESCRIPTORS_CONTRACT.md) for input
limits, comparison state, and source conventions.
