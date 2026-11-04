# Independent audio DSP reference vectors

The pinned constants in [the standard-library test](../test_audio_external_goldens.py)
were computed separately from all Kestrel reference implementations, using
**SciPy 1.17.0** and **NumPy 2.3.5**, on 2026-11-03.

These are **frozen external-library golden values**, not a dynamic SciPy
comparison executed on every GitHub CI run. They check sample-domain
amplitude, PSD, STFT and Welch numerical scaling; they do not establish
instrument standard compliance, production speed, browser visuals or device
calibration. Changes to source contracts must trigger review of these constants.
Do not regenerate goldens merely to silence a failing regression.

## Reproduction

Create an isolated environment with `numpy==2.3.5 scipy==1.17.0`;
copy the `X8`, `XODD`, and `X20` arrays from the linked test into a
Python interpreter and run:

```python
import numpy as np
from scipy import signal

w = signal.windows.hann(8, sym=False)
x8 = np.array(X8, dtype=float)
xodd = np.array(XODD, dtype=float)
x20 = np.array(X20, dtype=float)

# Explicit detrend=False matters: SciPy otherwise removes the DC mean.
_, p_even = signal.periodogram(x8, fs=8000, window=w, nfft=16,
                                detrend=False, scaling="density")
_, p_odd = signal.periodogram(xodd, fs=11025, window=np.ones(7),
                               detrend=False, scaling="density")
# Correct one-sided peak-amplitude scaling (DC and Nyquist undoubled).
a8 = abs(np.fft.rfft(x8 * w)) * np.array([1, 2, 2, 2, 1]) / sum(w)

# Mode PSD and no detrending; result is frequency x frame, so transpose.
_, _, S = signal.spectrogram(
    x20, fs=8000, window=w, nperseg=8, noverlap=4, nfft=8,
    detrend=False, return_onesided=True, scaling="density", mode="psd")

_, p_welch = signal.welch(
    x20, fs=8000, window=w, nperseg=8, noverlap=4, nfft=8,
    detrend=False, return_onesided=True, scaling="density", average="mean")

for label, values in [
    ("PSD_EVEN_PADDED", p_even), ("PSD_ODD", p_odd),
    ("AMPLITUDE_HANN", a8), ("PSD_STFT_FRAMES", S.T),
    ("PSD_WELCH", p_welch),
]:
    print(label, np.asarray(values).tolist())
```

Note that SciPy's spectrogram reports different *nominal time coordinates*
from the Kestrel left-aligned sample-center convention; compare **values**,
and validate time metadata in the separate sample-index unit tests.

References: [SciPy periodogram](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.periodogram.html),
[SciPy Welch](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html),
[SciPy spectrogram](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.spectrogram.html).
