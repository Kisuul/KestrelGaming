# FFT amplitude calibration and edge cases

Companion to [audio-fft-spectrum](../SKILL.md). This reference uses unnormalized DFT, a **real** sampled signal, a real finite window w[n] of length M, and Nfft >= M.

## Frequency layout and amplitude convention

The DFT frequency at k is k*fs/Nfft. One-sided output has floor(Nfft/2)+1 bins:

- DC (k=0) is unpaired; for DC signals, scale by 1/sum(w).
- Positive interior bins have negative-frequency counterparts; scale by 2/sum(w) for the declared **peak-amplitude bin** convention.
- For even Nfft, the last (Nyquist) bin is unpaired and scales by 1/sum(w).
- For odd Nfft, the highest returned bin is **not** Nyquist and takes the interior factor of two.
- The sum(w) divisor uses **all M window coefficients**, including any zeros, not Nfft padded positions. Zero padding does not change window coherent gain.

This calibration is valid for appropriate coherent, sufficiently isolated on-bin tones. Do not generalize a single-bin maximum into exact off-bin tone amplitude, total band power, or noise PSD. A log amplitude expressed as dBFS requires its explicitly declared full-scale *amplitude* reference. For a coherent full-scale peak sinusoid, conventions can differ from RMS-based references by about 3.0103 dB; label the reference.

## Analytic fixtures

| Input and transform | Expected output |
| --- | --- |
| All zeros, any valid window | All magnitude and amplitude bins exactly zero |
| Constant +0.25, rectangular window, even Nfft = M | A[0] = 0.25 |
| Alternating +0.25/-0.25, rectangular, even Nfft = M | A[Nyquist] = 0.25 |
| On-bin peak 0.7 sinusoid at interior k=7, M=Nfft=64, rectangular | A[7] = 0.7 within numerical tolerance |
| Same sinusoid, periodic Hann (M=64) | A[7] = 0.7 within numerical tolerance |
| On-bin peak 0.6 sinusoid at k=8, odd Nfft=M=63, rectangular | A[8] = 0.6 within numerical tolerance |
| Off-bin sinusoid | Spectral leakage; maximum bin not guaranteed to equal input peak |
| Unit impulse at sample 1, M=Nfft=8, rectangular | For the negative-exponent forward DFT, complex bin k=2 is -i; a conjugated/wrong-sign transform preserves magnitudes but fails this phase anchor |
| Window length M=64, Nfft=256 | df=fs/256 but window normalization still uses sum over 64 samples |

Fixtures above presume well-defined sample positions and a chosen sine phase. For Nyquist, alternation provides a directly sampled test; a sine at the exact Nyquist rate has phase-dependent degeneracy.

## What this skill does not cover

- PSD and noise-power calibration: these use window squared-sum, sample-rate and one-sided *power* factors, not the peak-amplitude correction above.
- Standardized filter-bank or octave-band measures.
- Complex spectra, analytic signals, frequency weighting, or deconvolution requiring additional conventions.
- Sample-accurate time history/STFT reconstruction: a separate spectrogram skill must document centering, hop, padding, and invertibility.

A deliberately slow [reference oracle](../scripts/reference_dft.py) and [analytic regression tests](../../../tests/test_audio_fft_reference.py) are supplied for small fixture frames. Treat the oracle as a cross-check, not a production FFT implementation or a substitute for testing the actual target analyzer.

References: [SciPy ShortTimeFFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.html), [SciPy FFT mode definitions](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.fft_mode.html), [Julius Smith's Spectral Audio Signal Processing](https://www.dsprelated.com/freebooks/sasp/).
