---
name: audio-multiresolution-spectrum
description: Engineer or audit parallel STFT spectrum analyzers with independent observation durations, calibrated one-sided PSD, exact common-end timing, deterministic frequency ownership, and atomic sample-clocked streaming.
---

# Multiresolution spectrum

Use when different frequency regions need different observation durations, or when
reviewing a spectrum assembled from several analysis windows. Load
[PSD](../audio-power-spectral-density/SKILL.md),
[windows](../audio-window-functions/SKILL.md), and
[timebase](../audio-timebase-sync/SKILL.md) for their established contracts.

1. **Declare the measurements.** Record source tap, normalized PCM units, sample
   rate, ordered channel labels, epoch and exact integer origin. Specify each
   profile's window length M, hop H, FFT length N and window variant.
2. **Choose physical durations first.** Longer windows discriminate closer tones
   but observe more history. Distinguish M/fs, H/fs, fs/N, window main-lobe width
   and ENBW. Zero padding changes the grid; it adds no observed information.
3. **Prove alignment.** Use complete left-aligned frames. Under the reference's
   [common-end equations](references/MULTIRESOLUTION_SPECTRUM_CONTRACT.md), reject
   profiles that cannot meet every selected endpoint. Preserve each contributor's
   start, end-exclusive and doubled sample-coordinate center. A shared endpoint
   does not imply a shared center or duration.
4. **Calibrate each profile independently.** Compute one-sided PSD with
   `d[k]*abs(X[k])**2/(fs*sum(w*w))`. Double paired interior power bins only.
   Verify each profile's integrated density against its own window-weighted
   time-domain energy. Retain all original spectra, including DC and Nyquist.
5. **Select frequencies explicitly.** Assign bin centers to nonoverlapping
   ranges; crossovers belong to the higher profile. Exclude DC from logarithmic
   views. Return unavailable when no measured bin supports a request. Ownership
   does not prevent leakage across crossovers. Never sum selected bins into a
   claimed composite energy or `composite_total_power`.
6. **Make streaming transactional.** Validate the entire callback and compute all
   profiles before committing state. Reject gaps, overlaps, bad samples and
   numerical failures atomically. Reset history and schedules on a new epoch.
   Bound input, output, retained history and transform work explicitly.
7. **Verify independently.** Freeze [analytical fixtures](../../tests/fixtures/AUDIO_MULTIRESOLUTION_SPECTRUM_GOLDENS.md),
   run the existing direct DFT on small vectors, test callback partitions and
   adversarial failures, then run repository validation. Submit exact revision
   and G1–G8 evidence for independent review; green tests do not confer acceptance.
8. **Label presentation honestly.** Density needs an explicit density reference
   for `10*log10(PSD/reference)`. Preserve measured zero beneath any render floor.
   Smoothing adds no measurements; normalized PCM is not calibrated SPL.

The standard-library [reference](scripts/reference_multiresolution_spectrum.py)
implements an offline educational three-profile analyzer. See its
[contract and example](references/MULTIRESOLUTION_SPECTRUM_CONTRACT.md) for limits.
CQT/VQT, wavelets, multirate filter banks, reassignment and synchrosqueezing offer
different time-frequency representations with additional scaling, kernel, phase,
edge or delay contracts. Compare them when choosing an architecture; this skill
does not implement them. Descriptors (Skill #25), pitch, harmonic/source tracking,
true peak, loudness, IEC class verification, production GPU processing and callback
deadline guarantees are outside this reference.
