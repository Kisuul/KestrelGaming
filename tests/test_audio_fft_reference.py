"""Analytic regression fixtures for the deliberately slow audio DFT oracle."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/audio-fft-spectrum/scripts"))
from reference_dft import one_sided_amplitude, one_sided_dft, periodic_hann, window_gains


class ReferenceDFTTests(unittest.TestCase):
    def test_rectangular_window_gains(self):
        g = window_gains([1.] * 64, 48000)
        self.assertAlmostEqual(g["coherent_gain"], 1)
        self.assertAlmostEqual(g["mean_square_gain"], 1)
        self.assertAlmostEqual(g["enbw_bins"], 1)
        self.assertAlmostEqual(g["enbw_hz"], 750)

    def test_periodic_hann_gains(self):
        g = window_gains(periodic_hann(64), 48000)
        self.assertAlmostEqual(g["coherent_gain"], 0.5)
        self.assertAlmostEqual(g["mean_square_gain"], 0.375)
        self.assertAlmostEqual(g["enbw_bins"], 1.5)
        self.assertAlmostEqual(g["enbw_hz"], 1125)

    def test_silence(self):
        self.assertTrue(all(v == 0 for v in one_sided_amplitude([0] * 32, periodic_hann(32))))

    def test_dc_and_even_nyquist(self):
        n = 64
        self.assertAlmostEqual(one_sided_amplitude([0.25] * n, [1.] * n)[0], 0.25)
        self.assertAlmostEqual(one_sided_amplitude([0.25 * (-1)**j for j in range(n)], [1.] * n)[n//2], 0.25)

    def test_on_bin_sine_rectangular_and_periodic_hann(self):
        n, k, a = 64, 7, 0.7
        tone = [a * math.sin(2 * math.pi * k * j / n) for j in range(n)]
        for window in ([1.] * n, periodic_hann(n)):
            with self.subTest(window=window[0]):
                spec = one_sided_amplitude(tone, window)
                self.assertAlmostEqual(spec[k], a, places=11)

    def test_odd_length_has_no_nyquist(self):
        n, k, a = 63, 8, 0.6
        tone = [a * math.sin(2 * math.pi * k * j / n) for j in range(n)]
        self.assertAlmostEqual(one_sided_amplitude(tone, [1.] * n)[k], a, places=11)
        self.assertEqual(len(one_sided_dft(tone, [1.] * n)), n//2 + 1)

    def test_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            periodic_hann(0)
        with self.assertRaises(ValueError):
            window_gains([0.] * 16, 48000)
        with self.assertRaises(ValueError):
            one_sided_amplitude([1., 2.], [1.])
        with self.assertRaises(ValueError):
            one_sided_amplitude([math.nan, 0], [1., 1.])
        with self.assertRaises(ValueError):
            one_sided_amplitude([0., 0.], [0., 0.])


if __name__ == "__main__":
    unittest.main()
