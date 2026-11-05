# Window calibration, definitions, and reference cases

Companion to [audio-window-functions](../SKILL.md). The formulas assume a finite real analysis window w[n] of length M, with all M valid values.

## Reference quantities

- Coherent gain: CG = sum(w) / M.
- Mean-square gain: MSG = sum(w^2) / M.
- Equivalent noise bandwidth in **DFT-bin units**: ENBW_bins = M * sum(w^2) / (sum(w))^2.
- ENBW in **Hz**: ENBW_Hz = fs * sum(w^2) / (sum(w))^2.
- DFT-bin spacing: df = fs / Nfft; when Nfft = M, ENBW_Hz = ENBW_bins * df. With zero padding (Nfft > M), **do not** substitute the finer zero-padded display spacing into that last equality.

Calibration needs sum(w) != 0, sum(w^2) > 0, finite coefficients, fs > 0, and an explicit transform convention. A window's equivalent bandwidth describes its noise sensitivity, not the frequency resolution of arbitrarily close tones.

## Two analytic fixtures

| Window, M >= 4 | Formula | CG | MSG | ENBW bins |
| --- | --- | --- | --- | --- |
| Rectangular | w[n] = 1 | 1 | 1 | 1 |
| Periodic Hann | w[n] = 0.5 - 0.5*cos(2*pi*n/M) | 0.5 | 0.375 | 1.5 |

For M = 64 and fs = 48000 Hz, rectangular ENBW_Hz = 750 Hz and periodic Hann ENBW_Hz = 1125 Hz. These identities follow from the exact periodic definitions. A symmetric Hann has denominator M-1 in its cosine and does **not** share exactly the same finite-M sums.

An on-bin interior sinusoid (not DC/Nyquist), with M-point analysis and an appropriate periodic window, can be checked by comparing its corrected peak-amplitude bin with its generated peak amplitude. Test multiple bins away from edges and the window's special cases. An off-bin sinusoid must reveal spreading into nearby bins; its tallest bin is not its exact amplitude.

## Negative and boundary fixtures

- Reject nonsensical M and invalid/zero sample rate; define the expected policy for M = 1, M = 2, and incomplete frames.
- Reject nonfinite coefficients and zero-sum windows when using coherent-gain amplitude calibration.
- Verify periodic-vs-symmetric window selection against independent library output or documented coefficients.
- Change Nfft while keeping M and w fixed; ENBW_Hz should stay unchanged, even though displayed df changes.
- Run impulse, silence, DC, two close tones, and broadband-noise fixtures. Record the exact window name, periodicity, parameters, sample rate, M, and Nfft.
- Check overlap-add/COLA or synthesis dual-window behavior independently if reconstruction is promised.

## Verification reference

For small M, the shared independent [reference DFT](../../audio-fft-spectrum/scripts/reference_dft.py) and its [regression tests](../../../tests/test_audio_fft_reference.py) provide deterministic *mathematical* evidence. They are not proof of realtime safety, conformance to a standard, or correct processing in an application.

References: [SciPy get_window](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.windows.get_window.html), [SciPy ShortTimeFFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.html), and [DSP-related spectral analysis](https://www.dsprelated.com/freebooks/sasp/).
