"""Analytic fixtures for experimental finite-buffer intersample estimates."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                        "skills/audio-true-peak/scripts"))
from reference_true_peak import experimental_peak_estimate


class TruePeakReferenceTests(unittest.TestCase):
    def pair(self, level=1.0):
        out = [0.] * 128
        out[63] = out[64] = level
        return out

    def test_silence_and_log_zero(self):
        r = experimental_peak_estimate([0.] * 80)
        self.assertEqual(r["sample_peak_amplitude"], 0)
        self.assertEqual(r["estimated"]["peak_amplitude"], 0)
        self.assertEqual(r["estimated"]["level_db_re_reference"], -math.inf)
        self.assertEqual(r["supported_interior_estimate"]["peak_amplitude"], 0)

    def test_isolated_center_impulse(self):
        x = [0.] * 128
        x[63] = 1.
        r = experimental_peak_estimate(x)
        self.assertAlmostEqual(r["estimated"]["peak_amplitude"], 1.)
        self.assertEqual(r["sample_peak_at_sample"], 63)
        self.assertEqual(r["estimated"]["peak_position_subsample_index"], 63*8)

    def test_two_tap_analytic_overshoot(self):
        r = experimental_peak_estimate(self.pair(), origin_sample=1000)
        self.assertEqual(r["sample_peak_amplitude"], 1.)
        phase = math.pi * 0.5 / 32
        expected = (4/math.pi) * (math.sin(phase)/phase)
        self.assertAlmostEqual(r["estimated"]["peak_amplitude"], expected, places=11)
        self.assertGreater(r["estimated"]["peak_amplitude"], 1.25)
        self.assertEqual(r["estimated"]["peak_position_subsample_index"],
                         (1000+63)*8+4)
        self.assertEqual(r["estimated"], r["supported_interior_estimate"])
        self.assertFalse(r["peak_in_boundary_region"])

    def test_polarity_independence_and_no_stereo_cancellation(self):
        a = experimental_peak_estimate(self.pair(0.65))
        b = experimental_peak_estimate(self.pair(-0.65))
        self.assertEqual(a["estimated"], b["estimated"])
        self.assertGreater(a["estimated"]["peak_amplitude"], 0.65)

    def test_scaling_and_reference_log(self):
        a = experimental_peak_estimate(self.pair())
        b = experimental_peak_estimate(self.pair(0.25), reference=0.25)
        self.assertAlmostEqual(a["estimated"]["peak_amplitude"]/4,
                               b["estimated"]["peak_amplitude"], places=12)
        self.assertAlmostEqual(a["estimated"]["level_db_re_reference"],
                               b["estimated"]["level_db_re_reference"], places=11)
        self.assertEqual(a["estimated"]["peak_position_subsample_index"],
                         b["estimated"]["peak_position_subsample_index"])

    def test_phase_shift_sine_and_edge_artifact(self):
        x = [math.cos(math.pi*i/2 + math.pi/4) for i in range(128)]
        r = experimental_peak_estimate(x)
        self.assertAlmostEqual(r["sample_peak_amplitude"], math.sqrt(0.5), places=11)
        self.assertAlmostEqual(r["supported_interior_estimate"]["peak_amplitude"],
                               1.0, delta=0.002)
        self.assertGreater(r["estimated"]["peak_amplitude"],
                           r["supported_interior_estimate"]["peak_amplitude"]+0.05)
        self.assertTrue(r["peak_in_boundary_region"])

    def test_grid_refinement_nested_maxima(self):
        x = [0.25] * 128
        peaks = [experimental_peak_estimate(x, oversample_factor=k)
                 ["estimated"]["peak_amplitude"] for k in (4, 8, 16)]
        self.assertLessEqual(peaks[0], peaks[1])
        self.assertLessEqual(peaks[1], peaks[2])

    def test_short_record_has_no_interior(self):
        r = experimental_peak_estimate([1., 1.], radius=8)
        self.assertIsNone(r["supported_interior_estimate"])
        self.assertTrue(r["peak_in_boundary_region"])
        self.assertGreater(r["estimated"]["peak_amplitude"], 1.2)

    def test_rate_and_large_sample_origin_exact(self):
        r = experimental_peak_estimate(self.pair(), oversample_factor=4,
                                       origin_sample=2**54)
        self.assertEqual(r["evaluation_rate_hz"], 192000)
        self.assertEqual(r["estimated"]["peak_position_subsample_index"],
                         (2**54 + 63)*4 + 2)
        self.assertEqual(r["maturity"], "experimental_not_bs1770_compliant")

    def test_unrepresentable_estimate_rejected(self):
        with self.assertRaises(ValueError):
            experimental_peak_estimate(self.pair(1.7e308))

    def test_reject_invalid_inputs(self):
        cases = [
            ([], {}), ([1.], {}), ([math.nan, 1.], {}),
            ([math.inf, 1.], {}), ([0.]*513, {}),
            ([0., 1.], {"sample_rate_hz": 0}),
            ([0., 1.], {"sample_rate_hz": 1e308, "oversample_factor": 16}),
            ([0., 1.], {"oversample_factor": 3}),
            ([0., 1.], {"oversample_factor": True}),
            ([0., 1.], {"radius": 4}), ([0., 1.], {"radius": False}),
            ([0., 1.], {"reference": 0}),
            ([0., 1.], {"origin_sample": -1}),
            ([0., 1.], {"origin_sample": True}),
        ]
        for x, options in cases:
            with self.subTest(options=options, length=len(x)):
                with self.assertRaises(ValueError):
                    experimental_peak_estimate(x, **options)


if __name__ == "__main__":
    unittest.main()
