"""Independent analytic and Parseval checks for tiny PSD reference transforms."""
import math
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/audio-power-spectral-density/scripts"))
from reference_psd import periodogram, welch_mean

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/audio-fft-spectrum/scripts"))
from reference_dft import periodic_hann


class PSDReferenceTests(unittest.TestCase):
    def integrated(self, power, fs, nfft):
        return math.fsum(power) * fs / nfft

    def test_silence_and_constant_dc(self):
        fs, n = 48000, 64
        f, p = periodogram([0.] * n, [1.] * n, fs)
        self.assertEqual(len(f), 33)
        self.assertTrue(all(value == 0 for value in p))
        f, p = periodogram([0.25] * n, [1.] * n, fs)
        self.assertAlmostEqual(p[0], 0.0625 * n / fs, places=13)
        self.assertAlmostEqual(self.integrated(p, fs, n), 0.0625, places=12)

    def test_even_nyquist(self):
        n, fs = 64, 16000
        samples = [0.25 * (-1)**j for j in range(n)]
        _, power = periodogram(samples, [1.] * n, fs)
        self.assertAlmostEqual(power[n//2], 0.0625 * n / fs, places=12)
        self.assertAlmostEqual(self.integrated(power, fs, n), 0.0625, places=12)

    def test_unit_impulse_and_padding_parseval(self):
        n, fs = 64, 16000
        samples = [0.] * n
        samples[5] = 1
        for nfft in (n, 128, 256):
            with self.subTest(nfft=nfft):
                f, power = periodogram(samples, [1.] * n, fs, nfft=nfft)
                self.assertEqual(len(f), nfft // 2 + 1)
                self.assertAlmostEqual(self.integrated(power, fs, nfft), 1/n, places=11)

    def test_on_bin_tone_and_window_energy(self):
        n, fs, k, amplitude = 64, 48000, 7, 0.7
        tone = [amplitude * math.sin(2 * math.pi * k * j / n) for j in range(n)]
        for win in ([1.] * n, periodic_hann(n)):
            with self.subTest(first_window_sample=win[0]):
                _, p = periodogram(tone, win, fs)
                self.assertAlmostEqual(self.integrated(p, fs, n), amplitude**2 / 2, places=11)
                if win[0] == 1.:
                    self.assertAlmostEqual(p[k], (amplitude**2 / 2) / (fs/n), places=11)

    def test_odd_nfft_top_bin_is_paired(self):
        n, fs = 63, 18900
        samples = [math.cos(2*math.pi*31*j/n) for j in range(n)]
        _, p = periodogram(samples, [1.] * n, fs)
        self.assertEqual(len(p), 32)
        self.assertAlmostEqual(self.integrated(p, fs, n), 0.5, places=11)
        self.assertAlmostEqual(p[31], 0.5/(fs/n), places=11)

    def test_zero_sum_window_is_valid_for_psd(self):
        fs = 8000
        _, p = periodogram([1., 1., 1., 1.], [1., -1., 1., -1.], fs)
        self.assertAlmostEqual(self.integrated(p, fs, 4), 1, places=11)

    def test_detrend_removes_constant_before_windowing(self):
        n, fs = 64, 48000
        _, raw = periodogram([0.25] * n, periodic_hann(n), fs)
        _, detrended = periodogram([0.25] * n, periodic_hann(n), fs, detrend_mean=True)
        self.assertAlmostEqual(self.integrated(raw, fs, n), 0.0625, places=11)
        self.assertTrue(all(value == 0 for value in detrended))

    def test_welch_matches_arithmetic_linear_power_mean(self):
        fs, m, hop = 8000, 16, 8
        data = [math.sin(j/4) + 0.1*math.cos(j/7) for j in range(48)]
        f, avg, count = welch_mean(data, [1.] * m, fs, hop)
        self.assertEqual(count, 5)
        single = [periodogram(data[i:i+m], [1.] * m, fs)[1] for i in range(0, 33, hop)]
        self.assertEqual(len(f), m//2+1)
        for k, value in enumerate(avg):
            self.assertAlmostEqual(value, math.fsum(s[k] for s in single)/count, places=12)

    def test_seeded_noise_parseval_matches_actual_segments(self):
        random_source = random.Random(1003)
        data = [random_source.uniform(-0.8, 0.8) for _ in range(96)]
        m, hop, fs = 32, 16, 16000
        _, power, count = welch_mean(data, [1.] * m, fs, hop=hop)
        expected = math.fsum(
            math.fsum(x*x for x in data[start:start+m])/m
            for start in range(0, len(data)-m+1, hop)
        ) / count
        self.assertAlmostEqual(self.integrated(power, fs, m), expected, places=12)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            periodogram([0.] * 4, [0.] * 4, 48000)
        with self.assertRaises(ValueError):
            periodogram([0.] * 4, [1.] * 4, 0)
        with self.assertRaises(ValueError):
            periodogram([0.] * 4, [1.] * 4, 48000, nfft=2)
        with self.assertRaises(ValueError):
            periodogram([math.nan] * 4, [1.] * 4, 48000)
        with self.assertRaises(ValueError):
            welch_mean([1.] * 16, [1.] * 8, 48000, hop=0)
        with self.assertRaises(ValueError):
            welch_mean([1.] * 3, [1.] * 8, 48000, hop=2)


if __name__ == "__main__":
    unittest.main()
