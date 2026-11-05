"""Frozen external SciPy/NumPy spectral regression vectors (not Kestrel-generated).

Generated with SciPy 1.17.0 / NumPy 2.3.5 on 2026-11-03; see
tests/fixtures/AUDIO_EXTERNAL_GOLDENS.md for independent regeneration.
All tests run with Python's standard library, without SciPy on GitHub CI.
"""
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-fft-spectrum/scripts"))
from reference_dft import periodic_hann, one_sided_amplitude
sys.path.insert(0, str(ROOT / "skills/audio-power-spectral-density/scripts"))
from reference_psd import periodogram, welch_mean
sys.path.insert(0, str(ROOT / "skills/audio-spectrogram-waterfall/scripts"))
from reference_stft import stft_frames


X8 = [0.125, -0.5, 0.75, -0.125, 0.0, 0.3125, -0.25, 0.625]
XODD = [0.125, 0.25, -0.5, 0.75, 0.125, -0.375, 0.0625]
X20 = X8 + [-0.0625, 0.25, -0.125, 0.4375, 0.5, -0.75, 0.25,
            0.0, -0.5, 0.75, 0.125, 0.0625]

PSD_EVEN_PADDED = [
    7.645051119419362e-06, 9.450042899292884e-06,
    2.0260208439448357e-06, 1.8889658384811365e-06,
    8.83718020405264e-06, 3.773012554695913e-05,
    6.545138297760989e-05, 3.5104423358376264e-05,
    2.139224980827114e-07,
]
AMPLITUDE_HANN = [
    0.1070867717280199, 0.07796193001609507,
    0.16282364881109232, 0.44311866236125697,
    0.017913228271980094,
]
PSD_ODD = [
    2.48015873015873e-06, 4.2119032538383755e-06,
    5.166540365484614e-05, 3.69514912772565e-05,
]
PSD_STFT_FRAMES = [
    [7.645051119419362e-06, 2.0260208439448353e-06, 8.83718020405264e-06,
     6.545138297760988e-05, 2.1392249808271132e-07],
    [1.5336575856340792e-05, 1.4438997955012442e-05, 1.0844306152013268e-05,
     2.8268842152355722e-05, 5.1032166432347425e-05],
    [4.603081256384947e-06, 3.247131965745646e-05, 9.549183585764301e-05,
     0.00011463411662835694, 2.6177185838452124e-05],
    [2.1467200760404163e-06, 1.87943129366596e-05, 6.202349128748961e-05,
     0.00011728735803300625, 3.024479293946911e-05],
]
PSD_WELCH = [
    7.432857077046381e-06, 1.6932662848268332e-05,
    4.429920337529965e-05, 8.141042494783221e-05,
    2.6917016927087837e-05,
]


class ExternalGoldenTests(unittest.TestCase):
    def assert_vector(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for idx, (got, want) in enumerate(zip(actual, expected)):
            with self.subTest(bin=idx):
                self.assertTrue(math.isclose(got, want, rel_tol=2e-10, abs_tol=2e-14),
                                f"bin {idx}: actual={got!r} independent={want!r}")

    def test_scipy_periodogram_hann_zero_padded(self):
        frequencies, power = periodogram(X8, periodic_hann(8), 8000, nfft=16)
        self.assert_vector(frequencies, [i * 500 for i in range(9)])
        self.assert_vector(power, PSD_EVEN_PADDED)

    def test_numpy_fft_coherent_amplitude_hann(self):
        self.assert_vector(one_sided_amplitude(X8, periodic_hann(8)), AMPLITUDE_HANN)

    def test_scipy_periodogram_odd_length_rectangle(self):
        frequencies, power = periodogram(XODD, [1.] * 7, 11025)
        self.assert_vector(frequencies, [i * 11025 / 7 for i in range(4)])
        self.assert_vector(power, PSD_ODD)

    def test_scipy_spectrogram_complete_frames(self):
        data = stft_frames(X20, periodic_hann(8), 8000, 4, nfft=8, scaling="psd")
        self.assertEqual([f["start_sample"] for f in data["frames"]], [0, 4, 8, 12])
        self.assertEqual(len(data["frames"]), len(PSD_STFT_FRAMES))
        for frame, expected in zip(data["frames"], PSD_STFT_FRAMES):
            self.assert_vector(frame["values"], expected)

    def test_scipy_welch_linear_mean_psd(self):
        frequencies, power, count = welch_mean(X20, periodic_hann(8), 8000, 4, nfft=8)
        self.assertEqual(count, 4)
        self.assert_vector(frequencies, [i * 1000 for i in range(5)])
        self.assert_vector(power, PSD_WELCH)


if __name__ == "__main__":
    unittest.main()
