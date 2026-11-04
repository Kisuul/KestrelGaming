"""Analytic level measurements, channel semantics and negative fixtures."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/audio-rms-crest-factor/scripts"))
from reference_levels import level_db, sample_levels


class LevelsReferenceTests(unittest.TestCase):
    def test_silence_is_not_a_zero_crest_factor(self):
        levels = sample_levels([0.] * 16)
        self.assertEqual(levels["sample_peak"], 0)
        self.assertEqual(levels["rms"], 0)
        self.assertIsNone(levels["crest_factor"])
        self.assertIsNone(levels["crest_db"])
        self.assertEqual(levels["rms_db_re_1"], -math.inf)

    def test_constant_and_alternating_level(self):
        for samples in ([0.25] * 16, [0.25 * (-1)**i for i in range(16)]):
            levels = sample_levels(samples)
            self.assertAlmostEqual(levels["sample_peak"], 0.25)
            self.assertAlmostEqual(levels["rms"], 0.25)
            self.assertAlmostEqual(levels["mean_square"], 0.0625)
            self.assertAlmostEqual(levels["crest_factor"], 1)
            self.assertAlmostEqual(levels["crest_db"], 0)

    def test_impulse_crest(self):
        levels = sample_levels([1.] + [0.] * 15)
        self.assertAlmostEqual(levels["mean_square"], 1/16)
        self.assertAlmostEqual(levels["rms"], 0.25)
        self.assertAlmostEqual(levels["crest_factor"], 4)
        self.assertAlmostEqual(levels["crest_db"], 20*math.log10(4))

    def test_full_peak_sine(self):
        samples = [math.sin(2*math.pi*4*i/64) for i in range(64)]
        levels = sample_levels(samples)
        self.assertAlmostEqual(levels["sample_peak"], 1, places=12)
        self.assertAlmostEqual(levels["rms"], math.sqrt(0.5), places=12)
        self.assertAlmostEqual(levels["crest_db"], 10*math.log10(2), places=12)
        self.assertAlmostEqual(levels["rms_db_re_1"], -10*math.log10(2), places=12)

    def test_antiphase_stereo_cannot_cancel_per_channel_rms(self):
        left = [math.sin(2*math.pi*3*i/32) for i in range(32)]
        right = [-s for s in left]
        self.assertAlmostEqual(sample_levels(left)["rms"], sample_levels(right)["rms"])
        self.assertGreater(sample_levels(right)["mean_square"], 0)
        self.assertTrue(all(abs(l+r)<1e-14 for l, r in zip(left, right)))

    def test_unit_reference_and_silence(self):
        self.assertEqual(level_db(1), 0)
        self.assertAlmostEqual(level_db(0.5), -6.020599913279624)
        self.assertAlmostEqual(level_db(0.5, reference=0.5), 0)
        self.assertEqual(level_db(0), -math.inf)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            sample_levels([])
        with self.assertRaises(ValueError):
            sample_levels([math.nan])
        with self.assertRaises(ValueError):
            sample_levels([math.inf])
        with self.assertRaises(ValueError):
            sample_levels([1e300, 1e300])
        with self.assertRaises(ValueError):
            level_db(-1)
        with self.assertRaises(ValueError):
            level_db(1, 0)


    def test_extreme_finite_log_ratios(self):
        self.assertAlmostEqual(level_db(1e-300, reference=1e300), -12000)
        self.assertAlmostEqual(level_db(1e300, reference=1e-300), 12000)
        self.assertAlmostEqual(level_db(5e-324, reference=1e308), -12626.124306862315)

    def test_tiny_nonzero_rms_not_false_silence(self):
        result = sample_levels([1e-200] * 4)
        self.assertEqual(result["rms"], 1e-200)
        self.assertTrue(result["mean_square_underflowed"])
        self.assertEqual(result["mean_square"], 0.0)
        self.assertAlmostEqual(result["crest_factor"], 1)
        silence = sample_levels([0.] * 4)
        self.assertFalse(silence["mean_square_underflowed"])
        ordinary = sample_levels([0.5] * 4)
        self.assertFalse(ordinary["mean_square_underflowed"])
        self.assertEqual(ordinary["mean_square"], 0.25)

    def test_smallest_subnormal_is_nonzero_rms(self):
        result = sample_levels([5e-324] * 4)
        self.assertGreater(result["rms"], 0)
        self.assertTrue(result["mean_square_underflowed"])


if __name__ == "__main__":
    unittest.main()
