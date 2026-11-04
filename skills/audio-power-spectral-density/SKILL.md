---
name: audio-power-spectral-density
description: Design, verify, or audit audio power spectral density estimates, periodograms, and Welch averaging with correct window-energy scaling, one-sided power bins, noise integration, detrending, and sample-based frame timing.
---

# Audio power spectral density — power per hertz, not amplitude per bin

## Activate when

Use for broadband noise measurements, periodograms, spectral power estimates, PSD smoothing or averaging, and Welch estimators. Do not load for an ordinary peak-amplitude spectrum or for standardized programme loudness. Load [audio-window-functions](../audio-window-functions/SKILL.md) for window ENBW and leakage; load [audio-fft-spectrum](../audio-fft-spectrum/SKILL.md) when comparing amplitude and power conventions. Consult [PSD calibration](references/PSD_CALIBRATION.md) for formulas and analytic tests.

## Procedure

1. **Identify the physical or digital signal reference.** Write down measured sample units (normalized amplitude, volts, pressure, etc.), sampling frequency fs, channels, measurement tap, time interval, and any calibration. With dimensionless normalized samples, PSD has units of sample-amplitude squared per Hz, **not** V²/Hz or dB SPL/Hz without calibration.
2. **Specify segment and frequency geometry.** Document M real input samples per window, Nfft >= M including zero padding, hop in samples, overlap, segment start timestamps, detrending mode, and how incomplete/invalid segments are handled. With Nfft and fs, positive-frequency bins are k*fs/Nfft; even transforms alone have a unique Nyquist bin.
3. **Select the appropriate window and normalization.** For unnormalized FFT of x[n]w[n], two-sided PSD is |X[k]|²/(fs*sum(w[n]²)). For real one-sided PSD, multiply paired positive-frequency **power** bins by two; do not double DC or even-length Nyquist. This differs from coherent-amplitude correction using sum(w), and from a squared peak-amplitude spectrum. Confirm scaling already performed by any third-party signal-processing API before applying corrections.
4. **Define detrending and integration.** Subtracting a per-segment mean is not the same as ignoring the DC display bin; explicitly state whether detrending occurs before windowing. For correctly normalized one-sided PSD, the sum over bins times df = fs/Nfft yields window-energy-normalized mean-square content (Parseval). With a rectangular unmodified segment, this equals the segment mean square. For nonstationary windowed data, it need not equal the *unweighted* segment mean square.
5. **Implement Welch averaging deliberately.** Average the **linear PSD ordinates** of complete segments, not amplitude spectra and not decibel values. State overlap, segment count and missing/gap policy. Overlapped segments are correlated; count is not independent-observation count. Mean-versus-median averaging and bias correction are separate decisions; do not silently substitute median for mean.
6. **Keep measurement independent of presentation.** Logarithmic PSD labels require 10*log10(Pxx/P_ref_density), an explicit reference density, and an explicitly marked visual floor for zeros. Never label density as total band energy, RMS amplitude, LUFS, or an exact single-bin tone amplitude. For band-power displays integrate the density over a declared frequency band.
7. **Verify mathematical invariants and adversarial cases.** Use [known fixtures](references/PSD_CALIBRATION.md) and the intentionally slow [reference estimator](scripts/reference_psd.py) with [unit tests](../../tests/test_audio_psd_reference.py): silence, DC, impulse, on-bin tone, odd/even Nfft, zero padding, window-energy scaling, segmented averaging, and detrending. Compare measured integrals to independently computed sample energy. Exercise invalid windows, nonfinite input, and insufficient segment data.
8. **Assess estimator uncertainty.** Report averaging mode, number of segments, window and overlap, and leakage/noise-floor limitations. More overlap does not yield as many statistically independent measurements as frames. When suitability depends on statistical confidence, verify via independent ensembles and confidence intervals rather than a single pretty spectrum.

## Acceptance gate

A PSD implementation is reviewable when the unit/reference, window normalization, one-sided power correction, integration behavior, segment policy, and test results are explicit and correct. Physical calibration, production performance, stochastic confidence and formal standard compliance remain separate gates. Follow [Kestrel verification](../../kestrel/VERIFICATION.md).

## References

- [SciPy periodogram](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.periodogram.html) — density/spectrum scaling, detrending and one-sided frequency behavior.
- [SciPy Welch](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html) — segmenting, overlap, averaging and scaling.
- [SciPy ShortTimeFFT scaling](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.scale_to.html) — magnitude and PSD use distinct normalization.
