"""Analytic tests for sample-peak magnitude, state, sample time, hold and failures."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/audio-sample-peak/scripts"))
from reference_peak import RollingPeakMeter, amplitude_level_db, scan_peak


class SamplePeakTests(unittest.TestCase):
    def test_exact_silence_has_negative_infinite_level(self):
        r = scan_peak([0.] * 8)
        self.assertEqual(r["peak"], 0)
        self.assertEqual(r["at_sample"], 0)
        self.assertEqual(r["level_db_re_reference"], -math.inf)
        self.assertEqual(r["reference_hits"], 0)
        self.assertEqual(r["strict_reference_exceedances"], 0)

    def test_signed_negative_peak_and_earliest_absolute_tie(self):
        r = scan_peak([0.2, -0.8, 0.8], start_sample=40)
        self.assertEqual(r["peak"], 0.8)
        self.assertEqual(r["at_sample"], 41)
        self.assertEqual(r["signed_value"], -0.8)
        self.assertEqual(scan_peak([-1., 1., -1.], 8)["at_sample"], 8)

    def test_reference_hit_is_not_strict_exceedance(self):
        r = scan_peak([0.5, 1., 1.25, -1.], reference=1.)
        self.assertEqual(r["reference_hits"], 3)
        self.assertEqual(r["strict_reference_exceedances"], 1)
        self.assertEqual(r["peak"], 1.25)
        self.assertGreater(r["level_db_re_reference"], 0)

    def test_amplitude_level_with_explicit_reference(self):
        self.assertEqual(amplitude_level_db(1.), 0)
        self.assertAlmostEqual(amplitude_level_db(0.5), -6.020599913279624)
        self.assertAlmostEqual(amplitude_level_db(0.5, 0.5), 0)
        self.assertEqual(amplitude_level_db(0), -math.inf)

    def test_holds_expire_on_sample_clock_not_render_frames(self):
        m = RollingPeakMeter(channels=1, hold_samples=3, sample_rate_hz=48000)
        results = [m.update([[v]], start_sample=i)["channels"][0]["rolling_peak"]
                   for i, v in enumerate([0.9, 0.2, 0.3, 0.1])]
        self.assertEqual([x["peak"] for x in results], [0.9, 0.9, 0.9, 0.3])
        self.assertEqual([x["at_sample"] for x in results], [0, 0, 0, 2])
        self.assertEqual(m.hold_samples / m.sample_rate_hz, 3/48000)

    def test_rolling_ties_prefer_earlier_until_expired(self):
        m = RollingPeakMeter(channels=1, hold_samples=2)
        self.assertEqual(m.update([[0.5, -0.5]], 11)["channels"][0]["rolling_peak"]["at_sample"], 11)
        r = m.update([[0.1]], 13)["channels"][0]["rolling_peak"]
        self.assertEqual(r["peak"], 0.5)
        self.assertEqual(r["at_sample"], 12)

    def test_program_peak_persists_after_window_expires(self):
        m = RollingPeakMeter(1, 2)
        first = m.update([[-0.9, 0.2]], 10)
        second = m.update([[0.1, 0.3]], 12)
        self.assertEqual(first["channels"][0]["program_peak"]["at_sample"], 10)
        self.assertEqual(second["channels"][0]["program_peak"]["at_sample"], 10)
        self.assertEqual(second["channels"][0]["program_peak"]["peak"], 0.9)
        self.assertEqual(second["channels"][0]["rolling_peak"]["peak"], 0.3)

    def test_antiphase_stereo_remains_independent(self):
        m = RollingPeakMeter(channels=2, hold_samples=4)
        result = m.update([[0., -0.75, 0.2], [0., 0.75, -0.2]], start_sample=21)
        left, right = result["channels"]
        self.assertEqual([left["block"]["peak"], right["block"]["peak"]], [0.75, 0.75])
        self.assertEqual([left["block"]["at_sample"], right["block"]["at_sample"]], [22, 22])
        self.assertEqual([left["block"]["signed_value"], right["block"]["signed_value"]], [-0.75, 0.75])

    def test_chunk_partitions_same_program_and_hold_result(self):
        data = [0.1, -0.7, 0.2, 0.8, -0.4, 0.3, -0.6, 0.1, -0.8, 0.5]
        a = RollingPeakMeter(1, 5)
        whole = a.update([data], start_sample=1000)
        b = RollingPeakMeter(1, 5)
        pos = 1000
        for size in (1, 3, 2, 4):
            part = b.update([data[pos-1000:pos-1000+size]], start_sample=pos)
            pos += size
        self.assertEqual(whole["channels"][0]["program_peak"], part["channels"][0]["program_peak"])
        self.assertEqual(whole["channels"][0]["rolling_peak"], part["channels"][0]["rolling_peak"])
        self.assertEqual(whole["end_sample_exclusive"], part["end_sample_exclusive"])

    def test_seek_requires_explicit_reset(self):
        m = RollingPeakMeter(1, 3)
        m.update([[0.8, 0.3]], 10)
        with self.assertRaises(ValueError):
            m.update([[0.2]], 20)
        with self.assertRaises(ValueError):
            m.update([[0.2]], 11)
        m.reset()
        r = m.update([[0.2]], 20)
        self.assertEqual(r["channels"][0]["program_peak"]["at_sample"], 20)
        self.assertEqual(r["channels"][0]["program_peak"]["peak"], 0.2)

    def test_invalid_multichannel_block_does_not_mutate_valid_state(self):
        m = RollingPeakMeter(2, 3)
        baseline = m.update([[0.5], [0.4]], 40)
        for bad in ([[1.], [math.nan]], [[0.1], [0.2, 0.3]], [[0.1]], [[], []]):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    m.update(bad, 41)
        r = m.update([[0.1], [0.2]], 41)
        self.assertEqual(r["channels"][0]["program_peak"], baseline["channels"][0]["program_peak"])
        self.assertEqual(r["channels"][1]["program_peak"], baseline["channels"][1]["program_peak"])

    def test_invalid_constructor_scan_and_origin(self):
        for args in [(0, 3), (1, 0), (True, 3), (1, True)]:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    RollingPeakMeter(*args)
        with self.assertRaises(ValueError):
            RollingPeakMeter(1, 3, reference=0)
        with self.assertRaises(ValueError):
            RollingPeakMeter(1, 3, sample_rate_hz=0)
        for bad in ([], [math.nan], [math.inf]):
            with self.assertRaises(ValueError):
                scan_peak(bad)
        with self.assertRaises(ValueError):
            scan_peak([1.], start_sample=-1)
        with self.assertRaises(ValueError):
            scan_peak([1.], start_sample=True)
        with self.assertRaises(ValueError):
            amplitude_level_db(-0.1)
        with self.assertRaises(ValueError):
            amplitude_level_db(1., reference=0)


    def test_extreme_finite_peak_reference_ratios(self):
        self.assertAlmostEqual(amplitude_level_db(1e-300, reference=1e300), -12000)
        self.assertAlmostEqual(amplitude_level_db(1e300, reference=1e-300), 12000)

    def test_long_block_can_hide_transient_from_final_rolling_hold(self):
        meter = RollingPeakMeter(channels=1, hold_samples=2)
        result = meter.update([[0.95, 0.1, 0.1, 0.1, 0.1]], start_sample=100)
        channel = result["channels"][0]
        self.assertEqual(channel["block"]["peak"], 0.95)
        self.assertEqual(channel["block"]["at_sample"], 100)
        self.assertEqual(channel["program_peak"]["peak"], 0.95)
        self.assertEqual(channel["rolling_peak"]["peak"], 0.1)
        self.assertEqual(channel["rolling_peak"]["at_sample"], 103)


if __name__ == "__main__":
    unittest.main()
