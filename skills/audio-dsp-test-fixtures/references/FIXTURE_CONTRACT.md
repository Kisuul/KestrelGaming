# Reproducible audio fixture and verification contract

Companion to [audio-dsp-test-fixtures](../SKILL.md).

When designing or auditing an oracle/comparator, use [math-verification](../../math-verification/SKILL.md) and its [fixture policy](../../math-verification/references/FIXTURE_POLICY.md) for generic independence, shape, finite-value and error-budget decisions. Consult [numerical analysis](../../math-numerical-analysis/SKILL.md) only for a finite-arithmetic issue. The DSP schema, clocks, channel contracts, analytic signals and calibration conventions below remain audio-owned.

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
4. **Optional live differential:** [seeded SciPy comparison](../scripts/check_scipy_differential.py) tests multiple frame lengths (including odd FFTs), windows, zero-padding, signal families and Welch/STFT modes. Explicitly pass `detrend=False`, periodogram `scaling="density"`, correct one-sided real scaling and frame geometries. Its comparator and heuristic margins are specified below. Frozen SciPy goldens and live SciPy comparisons share backend conventions; keep analytic and metamorphic checks as complementary evidence. The live FFT comparison checks real amplitudes, not complex phase/sign.
5. **Production and normative evidence:** real application integration, hardware timing, signal calibration, latency/CPU under supported load, external true-peak instruments and standard-specific fixtures remain separate and unverified.

### Live differential comparison contract

The harness converts both quantities to NumPy `float64`, requires identical array shapes **before** comparison (no broadcasting), and rejects nonfinite values in either array. The compared outputs are bounded, nonempty real measurement arrays generated from the declared finite fixtures. Ragged/non-convertible arrays also fail rather than being partially compared. No complex phase comparison is implied by this real-valued gate.

For each finite element, `np.allclose(got, want, rtol=2e-9, atol=3e-12)` uses the asymmetric additive rule:

`abs(got-want) <= 3e-12 + 2e-9*abs(want)`.

`want` is the external NumPy/SciPy result. The relative term is dimensionless; the absolute term has the units of the compared quantity:

| Compared quantity | Absolute margin | Relative margin |
| --- | --- | --- |
| Periodogram / Welch frequency coordinates | `3e-12 Hz` | `2e-9` times the external frequency magnitude |
| One-sided FFT peak amplitude | `3e-12` in normalized sample-amplitude units | `2e-9` times the external amplitude magnitude |
| Periodogram / STFT / Welch PSD | `3e-12` in normalized sample-amplitude squared per Hz | `2e-9` times the external PSD magnitude |
| RMS | `3e-12` in normalized sample-amplitude units | `2e-9` times the external RMS magnitude |

These are **fixture-specific heuristic comparison margins**, not derived universal error bounds or calibrated measurement uncertainties. They apply to the harness's bounded amplitudes, sizes, windows and declared normalization; do not reuse them for arbitrary signals, units or precision without a new budget. Near zero, the absolute term controls. This NumPy rule differs from the symmetric **max** rule of `math.isclose`; specifying both budgets does not make the APIs interchangeable. Frame counts and sample start/center coordinates are checked separately against the declared frame geometry, not admitted through these floating margins; an even-length frame's center may lie at a half-sample coordinate.

The mismatch message reports the largest absolute discrepancy, which need not be the first element that violates its relative/absolute gate. Preserve the fixture label/seed and actual array when investigating a failure rather than interpreting that diagnostic alone as an error bound. For checks built outside this harness, follow the shared [comparison policy](../../math-verification/references/FIXTURE_POLICY.md) and document any different rule explicitly.

### Optional command

```sh
python3 -m unittest discover -s tests -v
python3 skills/audio-dsp-test-fixtures/scripts/check_scipy_differential.py --seed 20261103 --cases 12
```

Normal GitHub CI needs only Python stdlib. The optional comparator needs independently installed SciPy and NumPy; its availability and execution status must be reported honestly. Do not treat matching SciPy numbers as proof of compliance with ITU, EBU, IEC or AES instruments.

## Negative fixtures

Test too-few/many samples, undefined signal kind, nonfinite amplitude/rate/phase, invalid bin/event sample/seed, malformed channel arrays, nonfinite sample data, empty or nonpositive chunk-size pattern, gap and out-of-sequence sample positions. A valid digital silence fixture is conceptually different from missing input.
