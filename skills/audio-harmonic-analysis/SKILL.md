---
name: audio-harmonic-analysis
description: Measure or audit harmonic partials from a calibrated one-sided FFT frame and a supplied fundamental. Use to diagnose unresolved tones, peak frequency errors, and harmonic matches with explicit frequency tolerances.
---

# Audio harmonic analysis

Use this skill when a known or separately estimated fundamental is available
and the task is to measure its partials. For an amplitude calibration problem,
start with the [FFT amplitude skill](../audio-fft-spectrum/SKILL.md).

1. **Trace the frame.** Select one original analysis frame and one channel.
   Record the clock, epoch, tap, amplitude reference, window, detrending, rate,
   observation length, hop, and FFT length. Name the supplied fundamental and
   its source. Preserve the exact sample interval.
   [Sample-clock rules](../audio-timebase-sync/SKILL.md)
2. **Choose the observation length.** Start with the required separation and
   the allowed latency. Select a window for main-lobe width and leakage.
   Increase FFT length to sample the same spectrum more densely. Collect more
   signal when the observation cannot separate the required tones.
   [Window selection](../audio-window-functions/SKILL.md)
3. **Locate candidates.** State a floor in linear peak-amplitude units. Find
   local maxima and flag equal-height plateaus. Fit a log parabola only when
   both flanks are positive and all three bins use the paired-bin scale.
   Keep the bin center, the fitted frequency if available, and the measured
   bin amplitude. Mark coarse results with their reason.
   [Peak contract](references/HARMONIC_ANALYSIS_CONTRACT.md#peak-search)
4. **Match the requested orders.** Compare each candidate with $h f_0$.
   Use the declared inclusive tolerance and half-open search band. Prefer the
   smallest absolute residual, then the larger measured amplitude. Keep
   unassigned peaks available for diagnosis. Track missing orders and clipped
   gates with separate statuses.
   [Assignment contract](references/HARMONIC_ANALYSIS_CONTRACT.md#harmonic-assignment)
5. **Interpret the evidence.** Report how many target orders were eligible and
   how many were matched. State which gates were fully covered. A missing
   first harmonic can still be consistent with the supplied fundamental.
   Peaks can support more than one series. To infer pitch or identify
   distortion, use the measurement contract for that task.
6. **Verify against the stimulus.** Use an off-bin tone to check frequency
   error. Use known close and unequal tones to check separation and leakage.
   Compare the estimated frequencies with the source frequencies. Include a
   gate-boundary check and an endpoint scaling check.
   [Analytic and adversarial fixtures](../../tests/fixtures/AUDIO_HARMONIC_ANALYSIS_GOLDENS.md)

Use the [offline reference](scripts/reference_harmonic_analysis.py) to check
the calculations in a target analyzer. Keep peak count, frequency accuracy,
and harmonic coverage visible in the engineering report.
