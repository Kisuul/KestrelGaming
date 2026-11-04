# PSD calibration and Welch reference fixtures

Companion to [audio-power-spectral-density](../SKILL.md). Definitions are for **real**, finite audio samples and an unnormalized DFT. The deliberately slow [oracle](../scripts/reference_psd.py) demonstrates these conventions; it does not implement production-grade real-time analysis.

## Normalization

For segment x[0:M], real window w[0:M], Nfft >= M, sampling rate fs and transform X[k]:

- Window energy S2 = sum(w[n]²), which must be finite and strictly positive.
- Two-sided PSD P2[k] = |X[k]|²/(fs*S2).
- Real one-sided density P1[k] = P2[k] at k=0 and at even-Nfft Nyquist. For all other returned positive bins, P1[k] = 2*P2[k].
- Frequency grid f[k] = k*fs/Nfft; integration grid spacing df = fs/Nfft.
- Sum(P1[k])*df = sum((x[n]*w[n])²)/S2 by discrete Parseval (when no detrending), independent of zero padding.
- For rectangular w[n]=1 and Nfft=M, the integral equals sum(x[n]²)/M: ordinary segment mean-square amplitude.

A **zero-sum** window with nonzero S2 cannot be calibrated for coherent tone amplitude by dividing by sum(w), but it is still valid for this PSD normalization. Don't reuse coherent-gain validity checks here.

For a stationary zero-mean noise process with known variance, the expected integrated PSD equals that variance; individual random records fluctuate. For a deterministic constant amplitude c, the integrated un-detrended PSD equals c² under any valid window. Subtracting a segment mean before windowing makes a constant signal's PSD zero.

## Deterministic fixtures

| Case | Expected check |
| --- | --- |
| All-zero input | Every PSD bin zero |
| Constant 0.25 with rectangular window, M=Nfft=64 | DC density = 0.25² * M / fs; integrated density = 0.0625 |
| Alternating ±0.25, M=Nfft=64 | Nyquist density = 0.25² * M / fs; integrated density = 0.0625 |
| Unit impulse in M=64 rectangular samples | Integrated density = 1/64 |
| On-bin sine with peak A=0.7, M=Nfft=64 rectangular | Integrated PSD = A²/2 (for integral cycles); interior bin density = (A²/2)/df |
| Periodic Hann and coherent interior sine away from edges | Integrated density = A²/2; expected side-lobe geometry differs from rectangular |
| Odd Nfft=63 | Last bin is paired and must be doubled |
| Zero padded Nfft=256, M=64 | Integral remains constant, df changes; don't divide power by Nfft instead of S2 |
| Welch (mean), hop=M and hop<M | Mean of corresponding linear segment PSDs; explicit segment count |
| Detrended constant signal | All-zero PSD after mean subtraction |

For a seeded nonstationary noise record, compare integration to the *actual* average segment mean square, rather than falsely asserting it must equal a desired ensemble variance. The Welch estimator is statistical; one short realization is not proof of unbiasedness across arbitrary processes.

## Edge cases and limitations

Reject M < 2, Nfft < M, nonpositive/nonfinite fs, zero-power or nonfinite window, nonfinite samples, nonpositive hops, and signals shorter than a full Welch segment. A sample-buffer overrun must create a discontinuity; never average across a gap as though samples had been contiguous.

The reference implementation intentionally supports only small transforms and **mean** Welch averaging, no padding of incomplete tail frames, and optional per-segment constant detrending. It intentionally does not claim median-bias correction, confidence intervals, physical calibration, or standardized instrument precision.

Sources: [SciPy periodogram](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.periodogram.html), [SciPy Welch](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html), [Spectral Audio Signal Processing](https://www.dsprelated.com/freebooks/sasp/).
