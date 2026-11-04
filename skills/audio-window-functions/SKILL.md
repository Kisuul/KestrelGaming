---
name: audio-window-functions
description: Choose, implement, verify, and document analysis window functions for audio FFT, STFT, amplitude estimation, and spectral measurements; distinguish periodic and symmetric windows, coherent gain, ENBW, and leakage tradeoffs.
---

# Audio window functions — choose the measurement tradeoff

## When to load

Use when selecting or changing an FFT/STFT window, correcting spectral amplitudes or noise bandwidth, or diagnosing leakage, scalloping, sidelobes, and spectral resolution. Do **not** load for ordinary unwindowed peak or RMS tasks. Read [audio-dsp-core](../audio-dsp-core/SKILL.md) when the signal path, timing, or numerical interface itself needs investigation. Consult the [window calibration reference](references/WINDOW_CALIBRATION.md) for derivations and acceptance fixtures.

## Procedure

1. **Name the measurement.** Is the objective a coherent tone amplitude, adjacent-tone discrimination, noise power/density, transient localization, or overlap-add reconstruction? Do not optimize every objective as though it were the same. Establish sample rate, true frame length M, FFT length Nfft, hop size, and channel policy.
2. **Name the exact window variant.** Record formula/coefficients, normalization, parameter values, and whether the window is **periodic (DFT-ready)** or **symmetric (typically FIR/filter design)**. Hann and Hamming are not interchangeable; Blackman-Harris, Nuttall, flat-top, and Kaiser families have variant-specific coefficients and tradeoffs. Prefer a documented library over an unnamed approximation.
3. **Measure the window before using it.** Compute coherent gain C = sum(w)/M, mean-square gain U = sum(w^2)/M, and equivalent noise bandwidth ENBW_bins = M*sum(w^2)/(sum(w)^2), ENBW_Hz = fs*sum(w^2)/(sum(w)^2). State whether the window has a usable nonzero sum; some derivatives/zero-mean windows cannot be amplitude-calibrated by dividing through sum(w).
4. **Match normalization to the observable.** For coherent on-bin sinusoid *peak amplitude*, correct the non-DC/non-Nyquist one-sided DFT magnitude with 2/sum(w) under the chosen unnormalized DFT convention. For PSD use fs*sum(w^2) as the power normalization basis, not sum(w)^2. Neither correction makes an arbitrary off-bin peak-bin estimate exact.
5. **Inspect temporal assumptions.** Identify frame centering/start conventions, padding, hop, and handling of incomplete frames. For STFT synthesis or overlap-add, verify the actual window and hop meet reconstruction conditions; analysis-only window selection does not prove invertibility.
6. **Compare the tradeoffs.** Rectangular: narrow main lobe but strong sidelobes. Hann: common leakage compromise. Blackman-Harris: stronger sidelobe suppression with wider main lobe. Flat-top: improved amplitude accuracy for tones with greater ENBW and poorer frequency separation. Parameterized windows require their parameter to be recorded. Avoid blanket claims that a window is universally best.
7. **Validate both math and behavior.** Use [analytic fixtures](references/WINDOW_CALIBRATION.md) for periodic Hann and rectangular windows; verify length, finite coefficients, known sums and ENBW, even/odd lengths, off-bin leakage, and zero padding. A numerical check of the coefficient arrays does not by itself validate the whole analyzer.
8. **Check performance and reporting.** Cache stable windows where appropriate, avoid allocating windows per realtime callback, preserve full configuration metadata, and display amplitude, power, or density units honestly. Report actual tests run and untested configurations.

## Acceptance gate

An implementation passes this skill's engineering gate only when its named window definition, coherent/power normalization, signal timing, and test results are recorded and correct for the intended observable. Do not claim instrument-class accuracy from synthetic windows alone. Follow Kestrel's [verification rules](../../kestrel/VERIFICATION.md).

## Sources

- [SciPy window API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.windows.get_window.html) — explicitly distinguishes FFT-periodic from symmetric variants.
- [SciPy ShortTimeFFT scaling](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.scale_to.html) — magnitude scaling differs from PSD scaling.
- [Spectral Audio Signal Processing](https://www.dsprelated.com/freebooks/sasp/) — window properties and spectral-analysis methods.

Do not infer that these sources alone certify a product against any formal measurement standard.
