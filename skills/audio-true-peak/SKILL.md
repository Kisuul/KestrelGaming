---
name: audio-true-peak
description: Design and audit true-peak intersample estimation, oversampling filters, sample-time and boundary policy, dBTP labeling, and ITU-R BS.1770-5 evidence, with an explicitly experimental finite-buffer reference.
---

# Audio true-peak estimation — see between PCM samples

## When to activate

For intersample peaks, true-peak meters, reconstructed overshoots, limiter-headroom diagnosis, or `dBTP` labeling audits. Use [audio-sample-peak](../audio-sample-peak/SKILL.md) for sampled maxima and [audio-dsp-core](../audio-dsp-core/SKILL.md) for tap, clock, and discontinuity questions. Consult [the interpolation and verification contract](references/TRUE_PEAK_CONTRACT.md).

**Maturity:** experimental reference guidance and fixtures. The provided code is **not** a BS.1770-conformant or calibrated instrument.

## Procedure

1. **Name the measured stream.** Specify PCM origin, channel identity, processing tap, effective sample rate, full-scale amplitude reference, and sample-clock epochs. Measure each channel independently before any aggregation; phase-inverted stereo channels still have nonzero peaks.
2. **Separate two quantities.** Sample peak is max(abs(x[n])) on the input grid. True peak refers to the reconstructed waveform's maximum and can occur between samples. An oversampled-grid maximum is an *estimate*, not a guaranteed exact continuous-time peak or upper bound.
3. **Consult the actual standard.** [ITU-R BS.1770-5 Annex 2](https://www.itu.int/rec/R-REC-BS.1770-5-202311-I) describes a fourfold oversampling example at 48 kHz (192 kHz), interpolation filtering, magnitude and dB TP conversion. It supplies an example four-phase FIR of order 48. The optional 12.04 dB initial attenuation protects fixed-point processing; floating-point may avoid that step with adequate headroom. A generic sinc interpolator is **not** that filter.
4. **Specify a reproducible estimator.** Declare oversampling ratio, filter coefficients or kernel, window and cutoff, phase/group delay, frequency response, passband ripple, stopband rejection, time-grid alignment, DC treatment, and error tolerance. A larger factor reduces *grid-sampling* error but cannot cure a bad filter or unknown boundary samples.
5. **Define boundaries and streaming lifecycle.** State exactly how missing pre/post samples are treated and how much lookahead or delayed output is needed. Prevent frame boundaries, seeks, gaps, channel changes and sample-rate changes from creating invented contiguous peaks. Never hide an edge artifact as a valid interior measurement.
6. **Report honestly.** Include sampled maximum, interpolated magnitude and separately located timestamps, full-scale reference, sample rate, and uncertainty/edge flags. A ratio in dB relative to a declared digital reference is not automatically a verified `dBTP` meter reading. An intersample over does not independently prove clipping in a specific DAC, codec or limiter.
7. **Verify with independent evidence.** Use [analytic/negative fixtures](references/TRUE_PEAK_CONTRACT.md), [experimental offline oracle](scripts/reference_true_peak.py) and [unit tests](../../tests/test_audio_true_peak_reference.py). Verify silence, midpoint overshoot, centered impulse, shifted sinusoid, channel polarity, grid nesting, sub-sample timing, short edges, overload, nonfinite inputs, and an independent filter/vector set before claiming accuracy.
8. **Earn standards claims separately.** For production `dBTP`, check the target BS.1770 revision's filter/tolerances and measurement rate, conformance material such as [ITU-R BS.2217](https://www.itu.int/rec/R-REP-BS.2217), independently calibrated instruments, actual host streaming/latency, and maximum error across expected frequencies and sample levels. Log which tests were *actually run* under [Kestrel verification](../../kestrel/VERIFICATION.md).

## Acceptance gate

The experimental skill requires explicit interpolation and extension choices, per-channel sample-vs-interpolated results, exact clock coordinates and reproducible analytic tests. **Do not promote it to a standards-compliant meter** without independent filter and instrument evidence.

## Sources

- [ITU-R BS.1770-5 (2023), Annex 2](https://www.itu.int/rec/R-REC-BS.1770-5-202311-I)
- [ITU-R BS.2217 meter test material](https://www.itu.int/rec/R-REP-BS.2217)
- [EBU R 128](https://tech.ebu.ch/publications/r128)
