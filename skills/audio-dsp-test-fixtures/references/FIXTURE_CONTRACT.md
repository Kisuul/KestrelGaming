# Reproducible audio fixture and verification contract

Companion to [audio-dsp-test-fixtures](../SKILL.md).

## Fixture schema v1

The [reference generator](../scripts/fixture_bank.py) emits:

- `schema_version=1`, `kind`, `sample_count`, `sample_rate_hz`, `origin_sample`, `channel_mode`, and `provenance`.
- `planar_samples[channel][relative_sample_index]`, in signed normalized floating amplitude units, with amplitude parameter between zero and one.
- `parameters`: amplitude, sinusoid bin index, phase in radians, impulse event sample, and `seed_uint32`. A parameter's presence does not imply relevance to every waveform.
- `channel_mode`: mono, stereo-inphase, or stereo-antiphase. Multi-channel mean-square cannot be inferred by algebraically summing anti-phase samples before squaring.

The bounded fixture bank supports 8–256 sample frames, finite positive sample rates, nonnegative absolute sample origins and explicitly finite coefficients. The uint32 noise generator uses `state=(1664525*state+1013904223) mod 2^32` and `sample=amplitude*(2*(state/2^32)-1)`. This is deterministic **test noise**, not cryptographic noise, statistical truth or an analog measurement model.

Waveform kinds:

| Kind | Mathematical property / test intention |
| --- | --- |
| silence | Digital zeros; zero linear levels, separate log-level policy |
| dc | Constant amplitude; no spectral energy away from DC under rectangular window |
| alternating | Even-length Nyquist tone; same magnitude/RMS as DC, different spectrum |
| impulse | Peak at the requested integer sample; RMS amplitude / sqrt(N) |
| coherent_sine | Integer FFT-bin sine at k/N; peak-amplitude bin calibration with declared window |
| offbin_sine | Frequency (k+0.25)/N; spectral leakage, no promised exact single-bin peak |
| seeded_noise | Same seed and shape => same samples; test broad spectrum and deterministic backend comparisons |
| adjacent_pair | Two consecutive +amplitude samples; intersample overshoot under declared interpolation (not instrument compliance) |

## Chunking, time and failure rules

`partition_contiguous(planar_samples, origin_sample, chunk_sizes)` cycles the positive size pattern, preserves every input sample, never inserts silence, and emits each chunk's **absolute** first sample index. A sample rate, stream epoch, or channel change must be represented externally. Chunk partition invariance is only expected for processing with identical valid continuous samples and the same measurement configuration.

A fixture generator is not a clock-recovery mechanism or an audio file decoder. Files, resampling and device gap semantics need separate fixtures when those specialist skills are developed.

## Verification ladder and tolerances

1. **Analytic cases:** independent expression for RMS, coherent tones, Parseval on declared windows, or impulse placement. Exact sample indices and channel data use exact comparison.
2. **Metamorphic cases:** scale factors, sign inversion, anti-phase preservation, and callback chunk partitions yield expected relationships without requiring copied DSP formulas.
3. **Frozen independent external goldens:** [existing SciPy-generated vectors](../../../tests/fixtures/AUDIO_EXTERNAL_GOLDENS.md). Do not regenerate expected arrays merely because a test fails.
4. **Optional live differential:** [seeded SciPy comparison](../scripts/check_scipy_differential.py) tests multiple frame lengths (including odd FFTs), windows, zero-padding, signal families and Welch/STFT modes. Explicitly pass `detrend=False`, periodogram `scaling="density"`, correct one-sided real scaling and frame geometries. Use `2e-9` relative and `3e-12` absolute tolerance for the **bounded test amplitudes**; this is a practical comparison threshold, not a universal DSP error budget.
5. **Production and normative evidence:** real application integration, hardware timing, signal calibration, latency/CPU under supported load, external true-peak instruments and standard-specific fixtures remain separate and unverified.

### Optional command

```sh
python3 -m unittest discover -s tests -v
python3 skills/audio-dsp-test-fixtures/scripts/check_scipy_differential.py --seed 20261103 --cases 12
```

Normal GitHub CI needs only Python stdlib. The optional comparator needs independently installed SciPy and NumPy; its availability and execution status must be reported honestly. Do not treat matching SciPy numbers as proof of compliance with ITU, EBU, IEC or AES instruments.

## Negative fixtures

Test too-few/many samples, undefined signal kind, nonfinite amplitude/rate/phase, invalid bin/event sample/seed, malformed channel arrays, nonfinite sample data, empty or nonpositive chunk-size pattern, gap and out-of-sequence sample positions. A valid digital silence fixture is conceptually different from missing input.
