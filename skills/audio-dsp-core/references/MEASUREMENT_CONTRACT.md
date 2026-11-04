# Measurement definitions and data contract

Reference for [audio-dsp-core](../SKILL.md). This is mathematical design guidance, not a substitute for an instrument standard or a certified measurement method.

## What a sample-derived quantity means

Assume normalized digital input x[n] with an explicitly stated full-scale convention. Let N be the number of valid samples in the measured window. For an unweighted mono window:

| Measurement | Definition | Caution |
| --- | --- | --- |
| Sample peak | max(abs(x[n])) | Misses intersample overs; not true peak |
| Mean square | (1/N) sum(x[n]^2) | Units are amplitude squared; not RMS |
| RMS amplitude | sqrt((1/N) sum(x[n]^2)) | State window duration, channel policy and DC treatment |
| Amplitude level | 20 log10(A / A_ref) | Requires positive A and declared reference |
| Power ratio | 10 log10(P / P_ref) | Requires positive P and declared reference |
| Crest factor | peak / RMS, or its ratio in dB | State which peak definition is used |
| Energy/activity event | Explicit detector rule over defined observations | Not an objective acoustic event unless established by evidence |

For exact digital silence, log-level is negative infinity mathematically. A configurable display floor is a *rendering* choice, not the measured numerical value. Never hide missing/corrupt frames behind a zero value.

For a full-scale peak sine, RMS amplitude is about 0.7071, corresponding to approximately -3.0103 dB relative to unit-amplitude RMS reference. State other reference conventions rather than assuming them.

## Multi-channel and window policies

- Compute per-channel observations before aggregating unless the required standard prescribes a specific combination. Summing L+R before squaring can make anti-phase content disappear.
- Distinguish a mean-square average across channels from a sum, max-channel operation, downmix, and psychoacoustic weighting; they are not interchangeable.
- Windowing changes measured RMS and FFT amplitude unless corrected for the target quantity. Do not apply a single arbitrary factor to every spectral estimator.

## FFT conventions

With a real-input N-point DFT of windowed samples x[n]w[n], the window coherent gain is sum(w[n])/N. For an on-bin sinusoidal amplitude estimate, a one-sided amplitude spectrum commonly uses 2*abs(DFT[k])/sum(w[n]) for interior positive-frequency bins. **Do not double DC or the Nyquist bin** (when N is even). Off-bin sinusoids spread energy across bins, so the largest bin is not a general-purpose exact amplitude estimator.

A power spectral density requires a different normalization, typically involving sample rate and sum(w[n]^2), plus correct one-sided handling. State whether a spectrum is amplitude, amplitude spectral density, power spectrum, or PSD, and document dB units accordingly. For a spectrogram, define window, hop, bin spacing, timestamp placement, and color-scale reference. Zero padding interpolates sample locations in the DFT; it does not improve physical resolving power.

## Suggested observation metadata

| Property | Meaning |
| --- | --- |
| source and channel IDs | Which input and channels produced it |
| quantity and unit | The measured type and its reference |
| sample_rate_hz | Effective sample rate at the measurement point |
| frame_start_sample and frame_length | Exact covered samples |
| timestamp_policy | Start, center, or end of frame |
| analysis configuration/version | Window, FFT size, hop, filters, and detector configuration |
| validity/discontinuity | Valid, incomplete, dropped, reset, or invalid input |
| calibration metadata | Available calibration, or explicitly none |

Use typed structures where the target architecture permits. Do not add all metadata to every numeric array if a stable immutable stream descriptor and frame header represent it more efficiently.

## Energy detector versus loudness

An activity detector is allowed to be application-specific, but its threshold must identify the signal reference, numerical operation, temporal averaging, and reset/hysteresis policy. A gate set on FFT magnitude, RMS, or absolute samples behaves differently. An ungated digital RMS proxy must not be presented as LUFS, VU, dB SPL, or true peak. Standardized loudness and acoustic measurements need their defined filters, time behavior, and calibration where applicable.

Sources: [ITU-R BS.1770](https://www.itu.int/rec/R-REC-BS.1770); [EBU R 128](https://tech.ebu.ch/publications/r128); [SciPy STFT scaling reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.scale_to.html); [Spectral Audio Signal Processing](https://www.dsprelated.com/freebooks/sasp/).
