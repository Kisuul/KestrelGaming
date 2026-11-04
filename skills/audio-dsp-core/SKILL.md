---
name: audio-dsp-core
description: Design, harden, refactor, or audit real-time audio analysis, energy detection, FFT preparation, sample timing, and shared DSP measurement contracts. Use before building meters, oscilloscopes, spectrum analyzers, waterfalls, or temporal signal analysis.
---

# Audio DSP core — measurements before visuals

## Activate when

Use this skill for audio sample ingestion, analysis scheduling, shared numerical primitives, FFT/window inputs, energy/activity detectors, and the contract between DSP and display. It is intentionally independent of programming language, backend, UI framework, and audio project. Load only this skill at first; consult other specialized skills when their subject becomes relevant.

Before changing a target project, follow its own instructions and Kestrel's [verification](../../kestrel/VERIFICATION.md) and [permissions](../../kestrel/PERMISSIONS.md) guidance. A skill supplies method and context, **not** additional authority.

## Procedure

1. **Trace the actual signal path.** Locate capture/decode, resampling, gain, channel mapping, ring buffers, FFT or filter-bank input, smoothing, event emission, and render consumers. Determine the measurement tap: pre/post gain, limiter, effects, or output. Record existing behavior and tests before replacing it.
2. **Specify observations before algorithms.** Every value must have an unambiguous quantity, unit, reference, channel scope, sample-rate basis, window size, hop, timestamp convention, and validity state. Distinguish peak, RMS, mean-square energy/power proxy, FFT amplitude, spectral density, and user-interface activity indicators. See [measurement definitions](references/MEASUREMENT_CONTRACT.md).
3. **Protect the realtime boundary.** Keep hard realtime callbacks bounded. Avoid unbounded allocations, blocking I/O, locks with uncontrolled waits, logging, and heavyweight transforms in such callbacks. Use explicit producer/consumer buffering, overrun policy, and discontinuity reporting. Do not silently replace missing data with valid silence.
4. **Define sample time, not render time.** Base analysis timestamps on sample positions and sample rate; document whether they identify frame start, center, or end. Cover seeks, pauses, dropped blocks, underruns, live-source resets, resampling, stream changes, and mismatched sample rates. Distinguish algorithmic latency from UI refresh delay.
5. **Separate measurement, detector, and presentation.** Shared DSP emits numerical observations with provenance. A detector converts observations into events using documented thresholds, hysteresis, attack/release/hold and reset behavior. A UI applies smoothing, clipping, scales, colors, and labels without changing the underlying measurement. Do not let display frame rate change the numerical answer.
6. **Get FFT conventions right.** State transform normalization, window definition, coherent gain, equivalent noise bandwidth where applicable, one-sided spectrum handling including DC and Nyquist, frequency-bin centers, leakage, and the difference between per-bin amplitude and density. Never apply a dB conversion to an unspecified quantity.
7. **Handle edge cases explicitly.** Test silence, DC offsets, sparse impulses, clipping, small signals, non-finite input, channel cancellation, unequal channel energies, short blocks, fractional analysis hops if supported, buffer wraps, and rapid configuration changes. For stereo energy, do not sum waveform channels before squaring unless phase cancellation is the intended measurement.
8. **Use deterministic evidence.** Implement [baseline fixtures](references/VALIDATION_FIXTURES.md), compare analytical expectations or a separately implemented reference, record tolerances and precision, and test frame boundaries and dropped-buffer recovery. Add performance measurements with the real buffer sizes and supported hardware targets.
9. **Review lifecycle and compatibility.** Check start/stop, suspend/resume, teardown, configuration migrations, API consumers, recordings, and historical-data users. Preserve backward behavior unless the change intentionally corrects a documented semantic error; label migration or new data versions.
10. **Report evidence and limits.** List implemented definitions, exercised fixtures, commands and actual results, measured CPU/latency if assessed, and what remains unverified. Do not claim IEC, AES, EBU, ITU, or instrument conformance solely from plausible output or a few synthetic tests.

## Design invariants

- No unlabeled or misleading numerical units; no unexplained calibration constants.
- No conflation of UI activity thresholds with physical energy or standardized loudness.
- No unbounded work on a truly realtime callback; no fabricated zeros when samples were lost.
- No dependence on animation/render frame rate for DSP timing or output.
- No claim of measurement conformance without traceable methodology and suitable references.

## Completion gate

A change is reviewable when its measurement contract exists, timing/reset semantics are explicit, representative deterministic fixtures pass, and the consumer-facing labels match the algorithms. If independent validation or device calibration is not available, report this as a gap rather than a pass.

## Related authoritative reading

- [ITU-R BS.1770 family](https://www.itu.int/rec/R-REC-BS.1770) — algorithms for loudness and true peak; do not apply its labels to arbitrary RMS meters.
- [EBU R 128](https://tech.ebu.ch/publications/r128) — broadcast loudness requirements and context.
- [SciPy ShortTimeFFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.html) — practical STFT conventions and scaling documentation.
- [Spectral Audio Signal Processing](https://www.dsprelated.com/freebooks/sasp/) — windowing, leakage, spectral estimation, and STFT background.

Keep standards editions and normative requirements pinned when claiming compliance; some full standards are not freely available.
