# STFT timing, density and waterfall visualization contract

Companion to [audio-spectrogram-waterfall](../SKILL.md). These definitions intentionally use **left-aligned, unpadded, complete frames**. SciPy's ShortTimeFFT commonly uses *centered* frames, boundary extension, and separate spectrum modes: comparisons require aligning frame origins and scaling first.

## Frame geometry

For real input x[n], effective sample rate fs > 0, analysis window w[j] of M samples, hop H with 1 <= H <= M, and Nfft >= M:

- Frame q takes exactly x[q*H + j] for j in 0..M-1, provided q*H + M <= total sample count. No synthetic tail frame.
- Start sample s[q] = absolute_origin + q*H; end-exclusive e[q] = s[q] + M.
- **Nominal sample-coordinate center** c[q] = s[q] + (M-1)/2. Even-size frames have half-integer centers. The corresponding seconds are c[q]/fs in this convention.
- The reference encodes that center exactly as integer `center_sample_twice = 2*s[q]+M-1`, with implicit denominator 2. Use this field for precise sample-clock mapping. The existing `center_sample` and `center_seconds` fields are floating convenience coordinates and may round at large origins; adjacent centers can collapse in them. Start and end-exclusive sample fields remain integers.
- Frame-center spacing is H/fs; FFT bin spacing is fs/Nfft.
- A real-input one-sided transform has floor(Nfft/2)+1 bins; the last bin is Nyquist only for even Nfft.
- A source chunk boundary must not reset the frame origin or alter values. Seek, missing samples and sample-rate changes require explicit epoch/gap behavior.

This center convention averages *sample-index coordinates* and is not interchangeable with every library's nominal centered window coordinate. If the display shows a frame's interval rather than its center, label that as a time-span or pixel coverage rather than claiming it is a point sample.

## Spectral ordinate and visualization

With unnormalized DFT X_q[k] of windowed samples:

- **Peak-amplitude bin** A_q[k] = |X_q[k]| / sum(w), multiplied by 2 for interior bins. It is calibrated for appropriate isolated coherent tones, not arbitrary transient amplitudes.
- **PSD bin** P_q[k] = |X_q[k]|² / (fs*sum(w²)), multiplied by 2 for paired interior positive-frequency bins. PSD has units input-amplitude²/Hz.
- DC and even-length Nyquist are not doubled. Odd-length top bin is a paired bin.
- Integrating a one-sided PSD frame with df = fs/Nfft gives sum((x[j]*w[j])²) / sum(w²), by Parseval.
- For the PSD rendering in decibels, use 10 log10(P_q[k] / declared_density_reference); for amplitude bin ratios, use 20 log10(A_q[k] / declared_amplitude_reference).
- No generic “dBFS/Hz” unless the full-scale **power-density** reference and signal definition have been specified. dB SPL needs physical calibration. Never call uncalibrated colored bars a calibrated sound-level measurement.
- A display floor is a renderer cutoff, not a claim that silent/no-data measurements equal a finite dB value. Missing frames are marked as gaps, not zero-energy measurement columns.

## Deterministic fixtures

| Signal | Required observation |
| --- | --- |
| Silence across several full frames | All values zero; valid frame timestamps advance in sample-time intervals |
| Coherent sine with periodic Hann, M=64, H=16, bin k=7 | Stable amplitude ridge at k=7 across frames; correct center sample and Hz labels |
| Frequency step aligned with disjoint M-sample windows | Known ridge changes at the correct frame; overlapping transition spans can show both tones |
| Single unit impulse at absolute sample n=40 | Nonzero frames exactly those whose covered sample interval includes n=40, for an all-ones window |
| Off-bin tone | Leakage appears; peak-bin magnitude is not the exact tone amplitude in general |
| Odd Nfft and even Nfft | Correct one-sided bin count and Nyquist doubling policy |
| Nfft > M zero padding | PSD integration remains tied to M window energy and physical df; more displayed bins do not mean higher resolution |
| Input split into arbitrary source chunks | Bitwise/sufficiently close identical numerical frames and exactly identical sample timestamps |
| Origin `2**54`, even M=4 and odd M=5 | Exact integer `center_sample_twice` advances by `2*H`, including half-sample centers; floating convenience fields are not the exact clock |
| Length shorter than M; incomplete final tail | No frames emitted; no silent zero padding without an explicit policy |
| Stream seek, dropped blocks, sample-rate reset | A visible discontinuity/new analysis epoch, not a fabricated contiguous waterfall |

## Visualization integrity checklist

- Define fixed or auto color limits, reference, floor, transfer function and colorbar unit; record per-frame remapping if auto scaling changes comparability.
- Frequency: linear or logarithmic in Hz; show separate handling of DC on log axes. Clearly mark bins aggregated into a display row.
- Time: newest versus oldest direction, duration and pixel-to-time mapping, freeze/scroll policy, source origin, UTC/media time vs elapsed sample time.
- History: memory/time bounds, resizing and frequency rebinning, decimation method, dropped-frame and gap markers; no overwriting numerical samples with UI-clipped values.
- Time compression: choose max-amplitude, mean linear **power**, or another named statistic to fit columns; averaging dB is not the same as averaging power.
- On changing window, hop, FFT size, scale, channels, fs or input tap, mark a new analysis epoch or reprocess raw samples rather than silently relabel stale history.

## Fixture implementation and limits

The dependency-free [reference STFT](../scripts/reference_stft.py) computes complete left-aligned frames with no centering/padding and supports only PSD or peak-amplitude bin modes. It is intentionally O(frames*M*Nfft), limited to small inputs, and rejects invalid input. [Tests](../../../tests/test_audio_stft_reference.py) exercise mathematical expectations and chunking invariance.

In PSD mode, `fs*sum(w²)` must be finite and strictly positive after floating evaluation. Reject overflowing or underflowed normalization before division, as in the [PSD range contract](../../audio-power-spectral-density/references/PSD_CALIBRATION.md); a numerical range failure is not a valid silent frame. This denominator check does not make the reference a general wide-dynamic-range implementation. Seconds and other floating convenience coordinates must also be representable in the selected backend.

The reference does **not** implement an application waterfall widget, callback interruption/gap detector, GPU rendering, inverse STFT, or physical instrument calibration. Those remain target-app verification requirements.

References: [SciPy ShortTimeFFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.html), [ShortTimeFFT.spectrogram](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.spectrogram.html), and [Spectral Audio Signal Processing](https://www.dsprelated.com/freebooks/sasp/).
