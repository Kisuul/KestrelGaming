# True-peak measurement and boundary contract

Companion to [audio-true-peak](../SKILL.md); contrast with [sample-peak metering](../../audio-sample-peak/references/SAMPLE_PEAK_CONTRACT.md).

## Meaning

A digital PCM sample maximum is not necessarily the maximum of a reconstructed bandlimited signal. ITU-R BS.1770-5, Annex 2 describes 4× oversampling at 48 kHz (192 kHz) with an interpolation FIR, absolute-value peak search, and a defined full-scale dB TP level. Its initial -12.04 dB attenuation addresses fixed-point headroom and is optional for suitable floating-point processing. Fourfold oversampling **alone** proves nothing about filter compliance or error. The informative attachment gives approximately 0.554 dB *pure-tone grid under-read* at normalized frequency 0.45 with 4×; this does not include filter and boundary error.

## Deliberately non-normative reference

The accompanying [offline oracle](../scripts/reference_true_peak.py) uses zero extension for all unknown samples outside the finite input, and a radius-limited **Lanczos-windowed sinc** kernel:

`y(t) = sum_j x[j] * sinc(t-j) * sinc((t-j)/R)` for `abs(t-j) < R`.

Here `sinc(v)=sin(pi*v)/(pi*v)`, with `sinc(0)=1`. The finite oversampled evaluation domain is `0 <= t <= N-1`, at steps of `1/L`. **It is not the Annex 2 example FIR** and does not guarantee the continuous-time maximum, a true-peak error budget, DC preservation or standard conformance. All original samples are included; no time outside the finite record is searched.

The oracle returns both:

- The **full-grid maximum** under zero extension, which may overshoot or under-read due to *invented* exterior zeros.
- A **fully supported interior maximum**, restricted to `R <= t <= N-1-R`. It is `None` for short records and is still subject to finite-kernel and grid error.

Returns use an exact integer `peak_position_subsample_index`, together with an `oversample_factor`, origin and effective sample rate. They allow precise long-running sample clocks without depending on rounded large floating timestamps. Both peak magnitudes are in the original sample amplitude units, with separately labeled dB ratios to a declared positive reference; they are **not dBTP**.

## Verification fixtures

| Signal | Grounded observation |
| --- | --- |
| Silence | Both magnitudes exactly zero, logarithmic level negative infinity |
| Single centered unit impulse | Sample maximum and oversampled maximum 1 at the original sample coordinate |
| Two adjacent +1 samples well inside an otherwise zero record | Sample peak = 1. Ideal sinc midpoint = 4/pi; the reference midpoint is `(4/pi)*sinc(0.5/R)`, an intersample peak above 1.25 |
| Sign/polarity inversion and stereo antiphase | Same peak amplitudes and times for each channel independently; do not downmix first |
| Phase-shifted quarter-rate cosine | Sample maximum approximately sqrt(1/2), while *supported-interior* reconstructed magnitude approximates 1; zero-extended outer edges can show larger artifacts |
| L = 4, 8, 16 under an identical kernel and edges | Nested evaluation grids yield nondecreasing full-grid maxima; that is not a conformance claim |
| N < 2R+1 | No interior maximum: return `None`, never an unearned numerical confidence |
| 48 kHz and L=4 | Evaluation rate 192 kHz; still not BS.1770-compliant merely by matching a rate |
| Very large finite PCM values | If reconstructed output would exceed binary64 range, reject explicitly |
| Missing samples, realtime callbacks and seeks | This offline reference cannot safely infer outside context or maintain streaming filter state |

## Acceptance and remaining work

The [tests](../../../tests/test_audio_true_peak_reference.py) exercise these fixtures. Independent *normative* vector comparisons, filter frequency-response checks, latency and channel tests, codec/DAC behavior and long-running streaming continuity remain unverified. A production device requires an explicit supported sample-rate/filter design, calibrated full-scale convention, and recorded tolerances. Never equate a successful analytic interpolation test to an instrument conformance result.

Sources: [ITU-R BS.1770-5](https://www.itu.int/rec/R-REC-BS.1770-5-202311-I), [ITU-R BS.2217](https://www.itu.int/rec/R-REP-BS.2217), [EBU R 128](https://tech.ebu.ch/publications/r128).
