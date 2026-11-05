---
name: audio-dsp-test-fixtures
description: Build reproducible, metadata-rich audio test signals, preserve sample-clock and channel semantics, verify DSP invariants, and run independent FFT/PSD/STFT/Welch comparisons without mistaking passing synthetic tests for instrument conformance.
---

# Audio DSP test fixtures — verification that can disagree

## Activate when

Use when designing, testing, reviewing or reproducing DSP measurements and their fixtures, especially FFT, PSD, STFT, meters, detector state, callback boundaries, or channel aggregation. This is a **shared audio-specific verification skill**, not another mathematical theory course. Consult [audio-dsp-core](../audio-dsp-core/SKILL.md) for the analysis tap and stream lifecycle; [audio-true-peak](../audio-true-peak/SKILL.md) for intersample reconstruction (its oracle remains experimental).

Consult mathematics only for the question at hand: [math-verification](../math-verification/SKILL.md) and its [fixture policy](../math-verification/references/FIXTURE_POLICY.md) for oracle independence, comparison contracts, shape/finite policies and evidence; [math-numerical-analysis](../math-numerical-analysis/SKILL.md) for floating-point range, cancellation or error-budget diagnosis. Audio retains fixture generation, sample-clock/channel provenance, transform calibration and measurement semantics. These links do not load every mathematics skill or replace DSP fixtures.

Read [the fixture contract](references/FIXTURE_CONTRACT.md), then apply the following procedure.

## Procedure

1. **Identify the actual assertion.** Define measured quantity, units/reference, channel layout, input tap, sampling rate, window/hop/FFT parameters, sample origin, boundary and reset policy, numeric representation, and acceptable accuracy. Record expected output or expected failure *before* changing the implementation under test.
2. **Choose fixtures with different failure modes.** Use exact silence/DC, constant and alternating signals, time-localized impulses, coherent-bin and off-bin sinusoids, adjacent positive samples with known intersample overshoot, anti-phase stereo, and deterministic broadband input. Do not interpret random noise as having an exact per-bin PSD; use distributional bounds or a separately computed result.
3. **Preserve metadata and reproducibility.** Call [the small standard-library generator](scripts/fixture_bank.py) with explicit parameters and sample origin. It emits planar PCM and a versioned generator descriptor. Noise uses a defined uint32 LCG so a seed maps to a portable sequence; no unseeded process RNG or audio hardware is needed. Validated chunk partitioning preserves every sample and its absolute index.
4. **Use complementary evidence layers.** Keep analytic results for constant/impulse/sine and exact arithmetic alongside previously frozen [SciPy/NumPy golden vectors](../../tests/fixtures/AUDIO_EXTERNAL_GOLDENS.md). Apply the shared [oracle policy](../math-verification/references/FIXTURE_POLICY.md): compare distinct codepaths, record shared dependencies, and do not count frozen and live SciPy outputs as two unrelated algorithms. [The optional seeded differential tool](scripts/check_scipy_differential.py) uses installed SciPy and NumPy to check live FFT amplitude/PSD/STFT/Welch and RMS results; its real magnitude/power comparisons do not establish a complex FFT phase/sign convention. It is **not** part of stdlib-only GitHub CI unless explicitly added and its dependencies pinned.
5. **Exercise metamorphic and chunk invariants.** Vary callback partitions without changing the audio samples and require invariant final STFT frames/sample timestamps and meter program/hold state. Test sign inversion, amplitude scaling, channel permutation, no unintended anti-phase cancellation, and sample-time positions beyond binary64's exact integer range.
6. **Deliberately test rejection and partial context.** Nonfinite inputs, invalid units/sample rate, sample count outside oracle bounds, mismatched channel lengths, nonpositive chunk sizes, gaps/seeks, and invalid configuration must produce an explicit failure/epoch state—not fabricated silence. Distinguish empty data from valid zero-valued measurements.
7. **Write comparisons and evidence honestly.** Use exact equality for integer sample coordinates and exact expected values. For floating results specify the comparator API and both tolerance terms, their units and rationale, following the [fixture contract](references/FIXTURE_CONTRACT.md). NumPy `allclose` uses an additive, expected-value-scaled rule; it differs from Python `math.isclose`. Log the reported discrepancy, fixture parameters, seed, backend/package versions, revision and test command. Do not silently replace a golden with the implementation's new output.
8. **Check the measurement environment.** Run [fixture-bank regression tests](../../tests/test_audio_dsp_fixture_bank.py), the existing repository tests, and optional live differential comparisons where available. Test any actual audio integration separately. CI green is **not** a substitute for calibrated instruments, real-time latency measurement, hardware/codec behavior, or standards conformity.

## Acceptance gate

A test suite using this skill declares signal generation, oracle dependence/independence, input/channel/time provenance, comparator semantics and tolerance, expected failure cases, and the verification layer actually executed. Novel test vectors must be reviewable without trusting the code under test. The fixture generator and comparator are intentionally offline and bounded; they do not run in audio callbacks.

## References

- [SciPy periodogram](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.periodogram.html) and [Welch](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html) — normalization, overlap, window/detrend settings.
- [SciPy spectrogram](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.spectrogram.html) — output and scaling conventions; legacy API used only for differential evidence.
- [Python unittest](https://docs.python.org/3/library/unittest.html), [Python math.isclose](https://docs.python.org/3/library/math.html#math.isclose), [NumPy allclose](https://numpy.org/doc/stable/reference/generated/numpy.allclose.html) — executable assertions and distinct comparator semantics with explicit numeric tolerances.
