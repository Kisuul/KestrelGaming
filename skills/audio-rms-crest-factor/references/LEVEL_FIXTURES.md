# RMS and crest-factor reference fixtures

Companion to [audio-rms-crest-factor](../SKILL.md). These are analytical fixtures for finite unweighted sample windows, not instrument-certification tests.

## Measurement contract

Given M finite real samples x[n], M>0:

- Peak sample excursion P = max(abs(x[n])).
- Mean square Q = sum(x[n]²) / M. For tiny finite binary64 inputs with unrepresentable Q, the reference returns Q=0 with `mean_square_underflowed=True`. RMS can remain nonzero, but for an isolated subnormal impulse its RMS may also underflow; the reference marks `rms_underflowed=True` when input has nonzero peaks but output RMS rounds to zero. Neither zero field alone proves digital silence.
- RMS amplitude R = sqrt(Q) mathematically. Numerically scale by maximum |x[n]| before squaring, so nonzero RMS remains observable even when individual x[n]² underflows.
- Crest factor C = P/R for R>0; undefined for exact silence.
- Crest level in dB = 20*log10(C), not 10*log10(C).
- dB relative to unit sample amplitude = 20*log10(R), **not automatically AES17 dBFS**. Compute nonzero amplitude ratios as `20*(log10(R)-log10(reference))` to avoid an intermediate underflow/overflow.
- Negative infinity is the mathematical log-level of exact zero. A UI floor is separate.
- dB is unitless without a reference; store the actual reference or naming convention.

## Analytic expectations

| Signal | Sample peak | RMS | Crest factor |
| --- | --- | --- | --- |
| All zero | 0 | 0 | Undefined |
| Constant +0.25 | 0.25 | 0.25 | 1 (0 dB) |
| Alternating ±0.25 | 0.25 | 0.25 | 1 (0 dB) |
| Unit impulse in M=16 | 1 | 0.25 | 4 (~12.0412 dB) |
| Coherent sine of peak 1 with M multiple complete periods and sampled extrema | 1 | sqrt(0.5) | sqrt(2) (~3.0103 dB) |

If sine sample phases do not include an exact peak, **sample peak can be lower** than signal peak amplitude. A true-peak meter requires interpolation/oversampling; this reference intentionally does not do that.

## Multichannel and invalid signal tests

- L=+s, R=-s: each channel has identical positive mean-square level, even though L+R is zero.
- Independent channel analysis is required before any explicitly specified combination.
- Empty/nonfinite input and invalid accumulated energy must fail closed, not return zero or arbitrary finite numbers.
- Windows with tapering or streaming envelope time constants require their own definitions and tests.

[Oracle](../scripts/reference_levels.py) and [tests](../../../tests/test_audio_levels_reference.py) provide small-fixture checks. No production audio path, standardized loudness algorithm, calibrated microphone, or real-time performance is established by these tests.
