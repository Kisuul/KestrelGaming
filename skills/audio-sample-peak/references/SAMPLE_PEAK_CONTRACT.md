# Sample-peak quantity, state and validation contract

Companion to [audio-sample-peak](../SKILL.md). This reference is for *finite sampled values* with an explicitly declared positive amplitude reference; it makes no claim of true-peak or clipping diagnosis.

## Three related quantities

For a channel block containing N >= 1 finite samples x[j], with absolute starting sample index s:

- **Block sample peak**: P_block = max(abs(x[j])); timestamp is s + j_peak. Ties select earliest index, including ties between a positive and a negative equal-magnitude excursion.
- **Program maximum**: maximum sample excursion observed **since explicit reset**. The implementation retains the earliest matching absolute sample position and never decays during that epoch.
- **Rolling sample peak**: at newest valid sample index t, P_hold(t) = max(abs(x[j])) for valid sample indices j in [t-H+1, t], with H >= 1. The reference requires sample continuity and therefore interprets this as exactly the trailing H contiguous sample slots (or fewer at stream start). It holds peaks only while their samples remain in the rolling window; it is not a timed plateau followed by an envelope release.
- **Sample-based timing**: x[s] is located using its index in the effective sample-rate domain. Hold interval in seconds is H/fs. If adapting user milliseconds, state how ms*fs/1000 is rounded, and reset on sample-rate change.
- **Signed excursion**: retain x[j_peak] if desired; the peak magnitude remains nonnegative.
- **Reference hits vs exceedances**: abs(x[j]) >= reference is a hit; abs(x[j]) > reference is a strict exceedance. Neither count alone establishes a clipped ADC, saturated file, or audible defect.

The reference implementation rejects missing, empty, out-of-order, negative-origin, nonfinite or inconsistent-channel blocks. It does not quietly insert zeros or guess times. To handle a known discontinuity, explicitly reset and then start a new epoch.

## Units and labels

With positive reference A_ref, amplitude ratio level is 20*log10(P/A_ref), -infinity for exact zero. For normalized PCM with reference=1, P=0.5 is about -6.0206 dB **re 1 peak-amplitude unit**. A floating point processing bus may have P>1, so the ratio may be positive. Do not conflate this convention with an AES17 RMS-defined full-scale reading, physical dB SPL, dB TP, or loudness LUFS.

**True peak** can exceed maximum abs(PCM samples) because the bandlimited reconstructed waveform has extrema between samples. Estimating that requires oversampling/filtering and a separate error/calibration budget; see [ITU-R BS.1770-5 Annex 2](https://www.itu.int/rec/R-REC-BS.1770-5-202311-I). Calling P_block “true peak” is incorrect.

## Deterministic reference fixtures

| Test | Expected observation |
| --- | --- |
| All-zero samples | Peak 0; magnitude level -infinity; hit/exceedance counts zero |
| Values [0.2, -0.8, +0.8] starting at s=40 | Peak 0.8 at absolute sample 41; signed value -0.8, earliest tie |
| [0.5, 1.0, 1.25] with ref 1.0 | Hit count 2, strict exceedance count 1; no automatic clip verdict |
| Two channels [+s, -s] | Equal per-channel peak and time locations; no cancellation from summing L+R |
| Rolling H=3: [0.9, 0.2, 0.3, 0.1] | Hold 0.9 through sample index 2; at sample 3 the older peak expires and held peak becomes 0.3 |
| Vary callback splits for one contiguous signal | Identical final program and rolling peak values/timestamps |
| Seek or missing sample index | Reject continuity mismatch until explicit reset |
| Bad channel count / NaN in any channel | Reject entire update; prior valid program and rolling states remain untouched |
| Short positive/negative impulse, any channel | Peak position equals the actual sampled location, independent of display FPS |

## Deliberate limits

The [small oracle](../scripts/reference_peak.py) and [unit tests](../../../tests/test_audio_sample_peak_reference.py) demonstrate unweighted sample-peak arithmetic and rolling-window semantics. They are not production-safe realtime code, sample-format decoders, true-peak reconstruction, clipping inference, or tests against a physical measurement system.

A production peak meter additionally needs stream lifecycle rules, bounded allocations, visual ballistics, peak hold/decay UX, data handoff and performance testing. These must be measured in the actual target application.
