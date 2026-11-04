---
name: audio-fft-spectrum
description: Implement, review, and calibrate FFT-based audio amplitude spectra, frequency axes, and spectral displays with precise DFT/window conventions, one-sided bin handling, and deterministic reference fixtures; distinguish amplitude spectra from PSD and loudness.
---

# FFT amplitude spectrum — truthful frequency-domain values

## When to load

Use for FFT amplitude/magnitude displays, tone measurements, frequency-axis mapping, spectrum scaling, and audits of spectral visualization accuracy. Load [audio-window-functions](../audio-window-functions/SKILL.md) when window selection, leakage, or correction factors are involved, and [audio-dsp-core](../audio-dsp-core/SKILL.md) for timing or ingestion changes. For PSD and noise-power questions, this skill can expose mislabeling but a dedicated `audio-power-spectral-density` skill is still planned.

## Procedure

1. **Trace the measured signal.** Identify source, channel mapping, pre/post-gain tap, sample rate fs, frame length M, FFT length Nfft (possibly zero padded), frame start and timestamp, window choice, and any built-in API scaling or smoothing. Do not double-normalize a library that has already scaled the transform.
2. **Declare the output contract.** Distinguish complex DFT, magnitude, peak-amplitude spectrum, power spectrum, and power spectral density (PSD). For a visualizer also specify axis frequency, linear/log amplitude, display floor, hold time, and refresh cadence. Arbitrary normalized bars must not be labeled as dBFS, VU, LUFS, or dB SPL.
3. **Write the transform convention.** For unnormalized DFT X[k] = sum over n=0..M-1 of x[n]*w[n]*exp(-j*2*pi*k*n/Nfft), define Nfft >= M. Real one-sided bins run k=0..floor(Nfft/2), frequency f[k] = k*fs/Nfft. In an even-sized transform Nyquist is k=Nfft/2; in an odd-sized transform there is no Nyquist bin.
4. **Correct coherent tone amplitude carefully.** For an eligible positive-sum real window, A[k] = |X[k]|/sum(w) at DC and even-Nfft Nyquist; A[k] = 2*|X[k]|/sum(w) at interior one-sided bins. This is a *peak-amplitude bin convention* and is reliable for coherent, well-isolated on-bin tones; it is not a universal exact-amplitude estimator for arbitrary off-bin signals or transient content. See [FFT calibration reference](references/FFT_CALIBRATION.md).
5. **Treat leakage honestly.** Off-bin tones leak and window choice changes the highest-bin value, main-lobe width, and sidelobes. Zero padding samples the frequency transform more densely but does not improve intrinsic resolution. Establish whether DC removal/detrending is used; show how it changes low-frequency observations.
6. **Separate DSP history from animation.** FFT hop controls time resolution; render cadence only controls visual refresh. Preserve sample-accurate timing and discontinuity markers. If smoothing or averaging is applied, state whether it is on complex values, amplitudes, powers, or dB values: these have different meanings.
7. **Test with deterministic evidence.** Exercise silence, known DC, on-bin sines with both rectangular and periodic Hann windows, odd and even transform lengths, Nyquist, off-bin leakage, two tones, stereo anti-phase, zero padding, missing frames, and nonfinite inputs. For a slow small-N independent oracle use [reference DFT](scripts/reference_dft.py) and [regression tests](../../tests/test_audio_fft_reference.py). Run tests; do not describe a fixture list as evidence of a pass.
8. **Review output and performance.** Confirm bin labels, scale floor, logarithmic mapping, and display artifacts; profile actual transform sizes and ensure computations are outside any truly hard-realtime callback when they cannot meet the budget. Check channel-specific labels and reset paths.

## Acceptance gate

Report the transform definition, window and normalization, output units, input/timing metadata, fixtures actually run with results and tolerances, and untested cases. Do not infer compliance with hardware instrumentation standards from a screenshot or a synthetic test.

## References

- [Calibration and accuracy reference](references/FFT_CALIBRATION.md)
- [SciPy ShortTimeFFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.html) — frequency bins, hops, zero padding, and transform modes.
- [SciPy amplitude/PSD scaling](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.scale_to.html) — normalization depends on the measurement.
- [Spectral Audio Signal Processing](https://www.dsprelated.com/freebooks/sasp/) — DFT and leakage background.

Follow Kestrel's [verification rules](../../kestrel/VERIFICATION.md), not an assumed claim of accuracy.
