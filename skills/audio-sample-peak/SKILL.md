---
name: audio-sample-peak
description: Build, review, or validate sample-peak audio meters, per-channel maximum excursions, sample-index timestamps, threshold counters, program peaks, and sample-clock-based peak holds without confusing sample peaks with true peak or proven clipping.
---

# Audio sample peak — measure samples, not reconstructed waveform

## Activate when

Load this skill for PCM sample-peak metering, per-channel peak locations, peak hold, maximum-since-reset, reference-threshold counters, or peak-meter label audits. Do **not** load it for RMS/crest-factor mathematics, intersample true-peak estimation, or loudness metering alone. Use [audio-rms-crest-factor](../audio-rms-crest-factor/SKILL.md) for peak/RMS ratios and [audio-dsp-core](../audio-dsp-core/SKILL.md) for upstream timestamps, discontinuities and ingestion architecture.

Consult [sample-peak contract and fixtures](references/SAMPLE_PEAK_CONTRACT.md) before implementing a meter.

## Procedure

1. **Establish the exact measured stream.** Record the measurement tap (decoded PCM, pre/post gain, effects, limiter or output), sample representation (integer or float), normalization, full-scale/reference amplitude, per-channel identity and sample rate. Do not silently clip valid floating-point samples outside [-1, 1].
2. **Define the observable.** A finite PCM block's sample-peak magnitude is P = max(abs(x[n])). Track its absolute sample index and optionally the signed value at that index; choose a deterministic tie rule (the reference keeps the earliest occurrence). A sample peak is not the continuous-time maximum and is not ITU true peak.
3. **Specify reference and units.** Convert a nonnegative peak to 20*log10(P/P_ref) dB **relative to the declared sample-amplitude reference**. Exact silence has mathematical level -infinity. A display floor or latch is presentation, not a new measured value. Avoid unqualified AES17, dB TP or calibrated SPL labels.
4. **Separate over-reference indicators from clipping evidence.** Define comparisons precisely: abs(sample) >= P_ref means a reference **hit**, while abs(sample) > P_ref means a **strict exceedance**. Float streams may legitimately exceed unit amplitude before downstream limiting; neither comparison alone proves a recording clipped. Detecting repeated rail values or hardware overload is a distinct diagnosis requiring codec/sample-format and processing-context evidence.
5. **Keep channel signals independent.** Compute each channel's peak and sample position before aggregation. Anti-phase stereo channels can both have large peaks even though their algebraic sum cancels. If offering an overall max, identify the channel and do not silently downmix.
6. **Define each time-dependent state.** Distinguish the *current block peak*, the *program peak since explicit reset*, and a *rolling sample-count peak window*. A rolling window of H valid samples keeps the maximum over exactly the latest H sample positions, with no arbitrary UI-frame-rate decay; it is not the same as an indefinitely latched overload indicator or a meter with timed hold then ballistic fall. Convert a requested hold duration to sample count using a documented rounding policy and effective sample rate.
7. **Treat gaps, resets and invalid data as real events.** Track contiguous sample positions across callbacks. Reject negative or out-of-sequence sample origins; require a deliberate reset/new epoch on seeks, dropped samples, stream restart, channel-layout or sample-rate changes. Validate a whole input block before mutating state so nonfinite data or a malformed channel cannot partially corrupt later readings. Missing input is not silence.
8. **Protect the audio callback.** Avoid UI rendering, allocations and unbounded operations inside a hard-realtime capture path. Use efficient bounded state and snapshot transport. The [reference](scripts/reference_peak.py) prioritizes clarity over realtime performance.
9. **Verify and report.** Run [deterministic fixtures](references/SAMPLE_PEAK_CONTRACT.md) and [regression tests](../../tests/test_audio_sample_peak_reference.py): positive/negative impulses, ties, exact silence, phase-inverted stereo, threshold equality/exceedance, rolling-hold expiration, differently sized contiguous blocks, reset, and invalid input. Inspect the downstream meter label and hold behavior in the target app separately.

## Acceptance gate

The measured tap, per-channel and tie semantics, amplitude/reference convention, three peak scopes (block, program, rolling), sample-time and reset policies, threshold behavior and tested fixtures must be explicit. Do not claim true-peak accuracy, recorded clipping or standardized instrument compliance based only on peak sample values. Follow [Kestrel verification](../../kestrel/VERIFICATION.md).

## Authoritative context

- [ITU-R BS.1770-5](https://www.itu.int/rec/R-REC-BS.1770-5-202311-I) — Annex 2 explicitly distinguishes sample maxima from oversampled true-peak estimates.
- [FADGI glossary: decibels relative to full scale](https://www.digitizationguidelines.gov/term.php?term=decibelsrelativetofullscale) — explains reference levels and intersample overs.
- [EBU R 128](https://tech.ebu.ch/publications/r128) — broadcaster true peak and loudness are specialized measurements, not arbitrary sample meters.
