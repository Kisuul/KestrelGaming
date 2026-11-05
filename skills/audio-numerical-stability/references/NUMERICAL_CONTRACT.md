# Audio numerical stability — mathematical contract v1

This is a **language-neutral analytical contract** with a bounded standard-library [oracle](../scripts/reference_numerical_stability.py), not a DAW backend or a replacement for shared numerical mathematics. It is specific to audio signal/measurement quantities; the [analytic fixture table](../../../tests/fixtures/AUDIO_NUMERICAL_STABILITY_VECTORS.md) records expected values independently from Python code.

## 1. Dimensions, signal model and FFT conventions

| Symbol | Meaning | Units |
| --- | --- | --- |
| `x[n]`, `w[n]` | input sample and dimensionless analysis window | sample unit, dimensionless |
| `N`, `M` | FFT length and segment/window length, `M<=N` | samples |
| `fs` | exact positive nominal sample rate | Hz (`samples/s`) |
| `X[k]` | DFT of `w[n]x[n]`, with any zero-padding defined separately | sample unit |
| `U=Σ w[n]²` | window energy | dimensionless |
| `C=Σ w[n]` | coherent window sum | dimensionless |
| `c[k]` | one-sided real-spectrum factor: 1 at DC and even-N Nyquist, otherwise 2 | dimensionless |

Assume the DFT is **unnormalized on forward transform**, the input is *real*, no unstated detrend is applied, and `X[k]` was already computed from windowed samples. Then:

- **RMS:** `sqrt((1/M) Σ_n x[n]²)` in linear sample units. It is not automatically dBFS or RMS power.
- **Bin amplitude:** `c[k] |X[k]| / |C|` in linear sample units, defined only when `C != 0`.
- **One-sided PSD density:** `c[k] |X[k]|² / (fs U)` in squared sample units/Hz, defined only when `fs>0`, `U>0`. For one-sided power, do not double DC or even-N Nyquist.
- **Equivalent noise bandwidth:** `ENBW_bins = M U / C²`, dimensionless FFT-bin count, defined only when `C != 0`; ENBW Hz for an unzero-padded M-point analysis is `fs U/C²`. Distinguish window length M from FFT zero-padding N when reporting Hz/bin.
- **Welch average:** arithmetic mean of comparable PSD ordinates from segments with compatible rate, window and normalization; mere arithmetic correctness cannot establish physical comparability.

A result in final binary64 range may nonetheless be lost if an intermediate square, sum or product exceeds that range. Conversely a final exact result outside binary64 requires an honest overflow/underflow policy, not an algebraic sleight of hand. DFT accuracy and potential input-space overflow must be evaluated separately from *post-FFT* PSD normalization.

## 2. Portable reformulations

**Scaled RMS:** let `s=max_n |x[n]|`; if `s=0`, RMS=0; else `s sqrt((Σ (x[n]/s)²)/M)`. For general streaming norms, carry a scale and normalized sum of squares, updating both when a larger magnitude arrives. In a true parallel implementation, define merge rules and reduction order; a stateful checksum or chunk-invariant error budget is more meaningful than demanding bitwise identity after reassociation.

**Scaled window:** choose `t=max_n |w[n]| > 0`; then `U=t² Σ (w/t)²` and `C=t Σ(w/t)`. ENBW cancels `t²` before multiplying, avoiding representational underflow for a tiny uniform window. Near cancellation of `Σ(w/t)` is a *conditioning* problem: returning an enormous finite ENBW when the coherent sum's uncertainty dominates is not evidence of a reliable measurement. Declare tolerance/uncertainty or mark undefined; do not blindly replace zero with an epsilon.

**Power ratios:** perform exponent-aware multiplication and division, mantissa/exponent scaling, a log representation, or sufficiently precise exact arithmetic **before** rounding the final PSD. The tiny reference calculates exact rational powers of finite binary64 inputs and rounds at output. This is a *test oracle*, **not** a recommended realtime big-integer architecture. An implementation using float32/64 must separately justify its exponent handling, error and performance.

**Welch mean:** if all ordinates are nonnegative, with `s=max p_i>0`, evaluate `s * [Σ(p_i/s)/K]` without forming an enormous raw `Σp_i`; ensure no overflow in aggregation. Do **not** apply this nonnegative-only strategy to signed or complex quantities without deriving an appropriate alternative. If ordinates represent already-clipped/invalid PSD, stable averaging does not heal them.

**Signed reductions:** `2^54 + 1 - 2^54 = 1` is an *exact* identity for representable binary64 operands; naive left-to-right evaluation may return zero. Compensated or pairwise summation may help, but a guaranteed correct result for arbitrary finite inputs may require precision/range beyond the accumulation type. The reference uses exact rational arithmetic as a check and reports unrepresentable final values.

**Fixed point:** quantization accepts *rational counts of LSBs*, bit width, signedness, nearest ties-to-even and **explicit** `saturate` or `error` policy. Range for signed b-bit: `[-2^(b-1),2^(b-1)-1]`; unsigned: `[0,2^b-1]`. Scaling from physical samples into LSB counts must be specified externally, and wraparound requires a *separate authorized contract*.

**Feedback filters:** for normalized biquad denominator `1+a1 z^-1+a2 z^-2`, pole roots solve `z²+a1 z+a2=0`. A causal linear time-invariant biquad with exact coefficients is strictly BIBO stable only if both poles lie *strictly* inside the unit circle. Quantized poles, state width, limit cycles and denormal policy require a separate implementation audit. Pole radii close to one are sensitive; a tested design in double precision is not automatically safe in fixed point.

## 3. Bounded oracle behavior

[Reference implementation](../scripts/reference_numerical_stability.py) supports finite binary64 scalar input vectors of 1–256 values, explicit rational sample rate `0 < fs <=384kHz`, one-sided unnormalized real FFT bins `0<=k<=floor(N/2)`, `2<=N<=256`, window length `1<=M<=N`, finite window coefficients and an exact positive window energy. Its exact PSD and amplitude arithmetic uses Python big-rational integers and returns **finite binary64** or raises a `ValueError` if the exact final result overflows or a nonzero result underflows to zero. That underflow policy is an oracle choice, not a claim that subnormal measurements are intrinsically invalid. Input `NaN`, `inf`, implicit float sample-rate, ambiguous coefficient types, invalid windows, undefined coherent gain and unsupported sizes fail closed.

`inspect_float32` is a platform experiment with IEEE-style binary32 packing, not a universal runtime ABI guarantee. `RmsAccumulator` is a tiny **single logical producer**, no-thread, epoch-aware scaled sum-of-squares model. It preserves an integer `next_sample` without timestamps or rate conversion, rejects discontinuities and validates each block atomically. Changing clock/rate/epoch needs a new unique epoch; this model does **not** infer gaps or guarantee deterministic operation on GPUs.

## 4. Independent evidence and error budgets

Tests in [the regression suite](../../../tests/test_audio_numerical_stability_reference.py) establish exact analytic values for silence, DC, impulses, a 4-phase sine and window ENBW, rational high-exponent PSD/amplitude expected outputs, odd/even one-sided factors, half-even quantization and binary32 representable boundaries. Seeded partition and scale invariants challenge stateful and algebraic paths independently. A test using another call into the same PSD function is **not** considered an independent oracle.

The sample results, not hidden implementation constants, determine the tolerance. For exact binary/rational results assert exact equality. For floating scaled transforms with no singularity, use relative error `|observed/expected-1|<=2e-14` for validated binary64 cases; define a separate absolute tolerance only if expected is zero and establish a nonzero absolute noise/error scale from the acquisition chain. Close-to-zero cancellation and near-unit poles require conditioning/error analysis rather than blanket relative tolerance. A tested finite frequency grid, even with all green results, is not a proof over the full continuous frequency range.

## 5. Failure attribution and follow-up repairs

The source audit in [Lane A's research record](../../../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-04-audio-numerical-stability-lane-a-research-r01.md) identified intermediate squaring/normalization ordering in existing reference PSD/STFT and amplitude calculations. This skill **does not change those files or claim to fix them**. A separate issue/patch must reproduce the defect against current code, preserve original scaling and units, demonstrate a red test that fails for the intended reason, then show green results plus a realistic-domain regression.

**Unverified:** actual 32-bit/64-bit CPU behavior across language runtimes, FTZ/DAZ, SIMD/FMA differences, parallel reduction order, representative source material, hardware timing, true-peak/BS.1770, agent activation/efficacy and safety of production DSP changes.

### Primary technical sources

- LAPACK [DLASSQ](https://www.netlib.org/lapack/explore-html/d8/d76/group__lassq_gae8f40b0a34771b4f2d9c863de3af7be5.html), stable sum of squares; modern versions use additional thresholds beyond this elementary derivation.
- SciPy [periodogram](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.periodogram.html), density/power units and real one-sided convention.
- Python [floating-point tutorial](https://docs.python.org/3/tutorial/floatingpoint.html), a platform-specific illustration of finite representation.
