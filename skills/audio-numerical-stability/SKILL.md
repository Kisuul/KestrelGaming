---
name: audio-numerical-stability
description: Diagnose and prevent finite-arithmetic errors in audio RMS, FFT amplitudes, PSD, Welch averaging, ENBW and filters using explicit signal units, scalable mathematics, independent numeric oracles, fixed-point policies and reproducible error budgets.
---

# Audio numerical stability — compute the intended signal quantity, not merely a plausible number

## Activate when

Use when an audio algorithm's correctness depends on **intermediate arithmetic**, numeric representation, cancellation, quantization, finite-range limits, reduction order, denormals, FFT/PSD scaling, dB or filter sensitivity. This is a mathematics-led engineering procedure, **not** a Python lesson or general numerical-analysis replacement. Load [math-numerical-analysis](../math-numerical-analysis/SKILL.md) only for needed numerical techniques, [math-verification](../math-verification/SKILL.md) for error claims, and the relevant audio skill for its *specific* measurement definition: [RMS/crest](../audio-rms-crest-factor/SKILL.md), [FFT](../audio-fft-spectrum/SKILL.md), [PSD/Welch](../audio-power-spectral-density/SKILL.md), [windows](../audio-window-functions/SKILL.md), [STFT](../audio-spectrogram-waterfall/SKILL.md), [filter design](../audio-filter-design/SKILL.md), or [PCM](../audio-sample-formats/SKILL.md). Do **not** load every math module or assume every audio unit is dBFS.

## Engineering method (language-neutral, before code)

1. **State the exact target.** Record sample/channel units and reference (linear amplitude, power, power/Hz, relative to full scale, SPL), sample rate and clock domain, sample window, FFT length/bin order, periodic/symmetric window, one-/two-sided factor and detrending. Write the *real-number equation* and identify what must be representable in the chosen output type. No implementation change may silently change the physical quantity or calibration.
2. **Describe the arithmetic environment.** Document input and accumulator representation, signed/fixed-point limits, rounding, saturation versus wrapping, float32/float64 width, intermediate precision, FMA or non-FMA semantics, subnormals/flush-to-zero, reproducibility across threads and the latency/memory budget. For a filter, identify coefficient format and feedback-state precision separately. Treat these as assumptions to test on actual target hardware—not implied by source-language types.
3. **Separate four failure categories.** (a) *Problem conditioning:* close inputs can imply vastly different outputs; e.g. near-zero coherent window sum. (b) *Algorithmic instability:* a numerically sensitive computation of an otherwise well-conditioned quantity. (c) *Representability:* the exact final result cannot fit the chosen type. (d) *Measurement uncertainty:* unknown calibration/input information that additional arithmetic precision cannot restore. Prefer explicit error/indeterminate status over silently manufacturing a plausible measurement.
4. **Audit every intermediate expression.** Identify products and powers before divisors, destructive cancellation, running sums, log of zero, FFT reduction order and block-state transitions. Two equivalent formulas over exact numbers may differ drastically under finite arithmetic; evaluate both range and rounding, not only final symbolic equivalence. For example, `2*|X|/N` can overflow when `|X|/N*2` is finite; `|X|²/(fs*Σw²)` can overflow *before* normalization, and `Σw²` may underflow to zero for tiny windows.
5. **Derive the replacement and proof obligation.** For RMS, set `s=max|x|`, then `RMS=s*sqrt(Σ(x/s)²/N)` for `s>0`; for true silence return zero. For ENBW use `v_i=w_i/s`, `ENBW_bins=N Σv_i²/(Σv_i)²`, and explicitly reject a vanishing coherent sum. For PSD and FFT amplitude, use exponent/mantissa-aware scaling, normalized factors or sufficient exact/extended precision where justified; never square huge intermediate magnitudes before considering the denominator. For Welch means, average *scaled* nonnegative ordinates rather than summing to infinity. For signed reductions use pairwise/compensated methods with a derived error budget; neither `fsum` nor higher precision alone solves all conditioning and range problems.
6. **Preserve domains and failure policy.** Exact zero, tiny nonzero, invalid/unknown, nonfinite input, undefined denominator, unrepresentable finite output, and negative power estimates are distinct states. A valid nonzero result that underflows to output zero is **not observed silence**; document a smaller unit, log-domain result, explicit underflow status or a narrower supported domain. Do not silently clamp a spectral ordinate to a reference threshold. Quantization requires declared scale, bit width, rounding (including ties) and overflow policy; fixed-point *wrap* is not interchangeable with saturation.
7. **Check stateful and control behavior.** FFT/PSD windowing and Welch segments must preserve original sample epochs and units. Ring partitioning, parallel reductions and filter-state updates should not change intended results outside declared tolerance. Validate the entire new block before advancing accumulators. For IIR, assess poles of the *quantized implemented denominator*, not solely the unquantized design; coefficient errors close to the unit circle may remove strict BIBO stability. State any filter retuning/denormal-state policy separately.
8. **Build an independent evidence ladder.** Start with exact rational/analytic vectors, then use a mathematically distinct implementation where possible, intentional negative tests, scaling and chunk invariants, numeric extremes, and dtype/backend differential runs. Bind tolerance to the observable's unit and magnitude; an absolute `1e-12` tolerance cannot adequately qualify an answer of `1e-300` or `1e300`. Require failures to fail for the intended reason. Preserve the seed and input bit patterns for reproducibility.
9. **Review maturity before claiming acceptance.** Passing the [bounded reference suite](../../tests/test_audio_numerical_stability_reference.py) means the tiny Python oracle meets its tested contract. It does **not** repair existing production PSD/STFT/FFT code or demonstrate audio agent quality, device accuracy, portability, realtime safety, true-peak conformance, or floating-point determinism across all hardware. The [technical contract](references/NUMERICAL_CONTRACT.md) states the acceptable domain and the [frozen analytic fixtures](../../tests/fixtures/AUDIO_NUMERICAL_STABILITY_VECTORS.md) supply independently justified expected behavior.

## Minimal verification

```sh
python3 -m unittest discover -s tests -p 'test_audio_numerical_stability_reference.py' -v
python3 tools/validate_seed.py
python3 -m unittest discover -s tests -v
git diff --check
```

The first command runs against the repository layout; subsequent checks are required for integrated changes where available. Report what was **actually executed** and distinguish its reference environment from any host audio application.

## Acceptance criteria

A satisfactory engineering answer declares: quantity/units and input uncertainty; numeric types/intermediate order; conditioned vs unstable vs unrepresentable case; justified reformulation; overflow/underflow/zero policy; sample-rate/window/channel/tap conventions; independent expected values and *dimensioned* error budgets; rejection behavior; and the unverified platform/perceptual limits. Merely recommending “use float64,” “clip to zero,” or “increase precision” fails this skill.

## Sources and relationship to the math core

- [LAPACK DLASSQ scaled sum-of-squares](https://www.netlib.org/lapack/explore-html/d8/d76/group__lassq_gae8f40b0a34771b4f2d9c863de3af7be5.html) and [LASSQ family](https://www.netlib.org/lapack/explore-html/d8/d76/group__lassq.html) — inspiration for stable norm accumulation; our simple reference does **not** implement modern LAPACK's more elaborate threshold branches.
- [SciPy periodogram definitions](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.periodogram.html) — density vs spectrum units and one-sided real-spectrum conventions; no claim of bit-identical SciPy results.
- [Python floating-point limitations](https://docs.python.org/3/tutorial/floatingpoint.html) — implementation-language context, **not** a substitute for representation-independent mathematics.
- [Audio numerical research handoff](../../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-04-audio-numerical-stability-lane-a-research-r01.md) — project-specific proposed cases, not verified repairs.
