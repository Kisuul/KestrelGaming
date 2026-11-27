"""Analytic coherent ratios and independent off-bin rejection probes."""

from dataclasses import replace
from fractions import Fraction
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in ("audio-thd-thdn", "audio-power-spectral-density", "audio-oscilloscope"):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_oscilloscope import CaptureWindow, ScopeEpoch
from reference_thd_thdn import ThdProfile, measure_thd_thdn


ORIGIN = 2**60 + 37
RATE = 48_000
FRAMES = 480
EPOCH = ScopeEpoch("settled", ORIGIN, Fraction(RATE), "adc", "post-drive", "FS", ("M",))
PROFILE = ThdProfile(10)


def capture(samples, **epoch_fields):
    return CaptureWindow(replace(EPOCH, **epoch_fields), ORIGIN, (samples,))


def coherent(frames=FRAMES, dc=0.05, tones=((10, 0.5), (30, 0.005), (17, 0.002))):
    return tuple(
        dc + sum(amplitude * math.cos(math.tau * (index * n % frames) / frames)
                 for index, amplitude in tones)
        for n in range(frames)
    )


def mean_square(samples):
    return math.fsum(x * x for x in samples) / len(samples)


class CoherentThdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples = coherent()
        cls.report = measure_thd_thdn(capture(cls.samples), PROFILE)

    def assertPower(self, actual, expected, *, relative=1e-10):
        self.assertTrue(math.isclose(actual, expected, rel_tol=relative), (actual, expected))

    def test_named_ratios_and_amplitude_power_conversions(self):
        report = self.report
        for ratio, expected, decibels in (
            (report.thd, 0.01, -40.0),
            (report.thdn_fundamental, math.sqrt(0.0000145 / 0.125), -39.35542010773081),
            (report.thdn_total, math.sqrt(0.0000145 / 0.1250145), -39.355923860112746),
        ):
            self.assertPower(ratio.linear, expected)
            self.assertPower(ratio.percent, 100 * expected)
            self.assertAlmostEqual(ratio.decibels, decibels, places=8)

    def test_powers_and_exact_ledger_closure(self):
        report = self.report
        self.assertPower(report.fundamental_power, 0.125)
        self.assertPower(report.distortion_power, 0.0000125)
        self.assertPower(report.residual_power, 0.0000145)
        self.assertPower(report.band_power, 0.1250145)
        self.assertEqual(report.band_power, report.fundamental_power + report.residual_power)
        self.assertEqual(sum(entry.power for entry in report.bins if entry.admitted), report.band_power)
        self.assertLess(report.distortion_power, report.residual_power)
        self.assertPower(sum(entry.power for entry in report.bins), mean_square(self.samples))
        self.assertPower(report.bins[17].power, 0.000002)
        self.assertEqual(report.fundamental_status, "qualified")

    def test_support_and_frequency_grid_are_exact(self):
        report = self.report
        self.assertEqual(report.epoch, EPOCH)
        self.assertEqual(report.channel_id, "M")
        self.assertEqual((report.start_sample, report.end_sample_exclusive), (ORIGIN, ORIGIN + FRAMES))
        self.assertEqual(len(report.bins), 241)
        self.assertEqual(report.bin_width_hz, Fraction(100))
        self.assertEqual(report.bins[10].frequency_hz, Fraction(1000))
        self.assertEqual(report.bins[-1].frequency_hz, Fraction(24_000))

    def test_dc_admission_uses_both_band_and_policy(self):
        report = measure_thd_thdn(capture(self.samples), replace(PROFILE, include_dc=True))
        self.assertTrue(report.bins[0].admitted)
        self.assertFalse(self.report.bins[0].admitted)
        self.assertPower(report.bins[0].power, 0.0025)
        self.assertEqual(report.residual_power - self.report.residual_power, report.bins[0].power)
        self.assertEqual(report.distortion_power, self.report.distortion_power)
        filtered = measure_thd_thdn(
            capture(self.samples), replace(PROFILE, band_hz=(1, 24_000), include_dc=True)
        )
        self.assertFalse(filtered.bins[0].admitted)
        self.assertEqual(filtered.residual_power, self.report.residual_power)

    def test_inclusive_band_excludes_harmonic_but_keeps_spur(self):
        report = measure_thd_thdn(capture(self.samples), replace(PROFILE, band_hz=(1000, 1700)))
        self.assertTrue(report.bins[10].admitted)
        self.assertTrue(report.bins[17].admitted)
        self.assertEqual(report.distortion_power, 0)
        self.assertPower(report.residual_power, 0.000002)
        third_order = report.harmonics[1]
        self.assertEqual(third_order.status, "out_of_band")
        self.assertEqual(third_order.nominal_frequency_hz, 3000)
        self.assertIsNone(third_order.admitted_power)

    def test_unrequested_harmonic_still_enters_residual(self):
        report = measure_thd_thdn(capture(self.samples), replace(PROFILE, harmonic_orders=()))
        self.assertEqual(report.harmonics, ())
        self.assertEqual(report.distortion_power, 0)
        self.assertEqual(report.residual_power, self.report.residual_power)

    def test_out_of_band_line_has_power_but_does_not_enter_band(self):
        samples = coherent(tones=((10, 0.5), (30, 0.005), (17, 0.002), (125, 0.2)))
        full = measure_thd_thdn(capture(samples), PROFILE)
        filtered = measure_thd_thdn(capture(samples), replace(PROFILE, band_hz=(400, 5000)))
        self.assertPower(filtered.bins[125].power, 0.02)
        self.assertFalse(filtered.bins[125].admitted)
        self.assertPower(filtered.residual_power, 0.0000145)
        self.assertPower(full.residual_power, 0.0200145)

    def test_equal_residual_and_fundamental_distinguish_references(self):
        report = measure_thd_thdn(
            capture(coherent(dc=0, tones=((10, 0.5), (17, 0.5)))), PROFILE
        )
        self.assertAlmostEqual(report.thdn_fundamental.decibels, 0.0, places=12)
        self.assertAlmostEqual(report.thdn_total.decibels, -3.010299956639812, places=12)

    def test_weak_distortion_survives_rounded_total(self):
        report = measure_thd_thdn(
            capture(coherent(dc=0, tones=((10, 0.5), (30, 2.0**-32)))), PROFILE
        )
        self.assertEqual(float(report.band_power), float(report.fundamental_power))
        self.assertPower(report.distortion_power, 2.0**-65, relative=2e-5)
        self.assertPower(report.residual_power, 2.0**-65, relative=2e-5)
        self.assertEqual(report.band_power - report.fundamental_power, report.residual_power)
        self.assertLess(report.thd.decibels, -180.0)

    def test_nyquist_counted_once_and_possible_fold_not_reassigned(self):
        samples = coherent(dc=0, tones=((80, 0.5), (160, 0.005), (240, 0.003)))
        report = measure_thd_thdn(capture(samples), ThdProfile(80, (4, 3, 2)))
        second, third, fourth = report.harmonics
        self.assertEqual([h.order for h in report.harmonics], [2, 3, 4])
        self.assertEqual(second.status, "admitted")
        self.assertEqual(third.status, "admitted")
        self.assertPower(third.admitted_power, 0.000009)
        self.assertEqual(fourth.status, "above_nyquist")
        self.assertEqual(fourth.nominal_frequency_hz, 32_000)
        self.assertEqual(fourth.possible_fold_bin, second.nominal_bin)
        self.assertIsNone(fourth.admitted_power)
        self.assertPower(report.distortion_power, 0.0000215)
        self.assertPower(report.residual_power, 0.0000215)

    def test_possible_fold_into_dc_fundamental_or_spur_keeps_bin_assignment(self):
        samples = coherent(frames=24, tones=((5, 0.5), (1, 0.002)))
        report = measure_thd_thdn(capture(samples), ThdProfile(5, (5, 23, 24), include_dc=True))
        self.assertEqual([h.possible_fold_bin for h in report.harmonics], [1, 5, 0])
        self.assertTrue(all(h.status == "above_nyquist" for h in report.harmonics))
        self.assertEqual(report.distortion_power, 0)
        self.assertPower(report.residual_power, 0.002502)

    def test_odd_highest_bin_has_pair_weight_and_exact_frequency(self):
        samples = coherent(frames=253, dc=0, tones=((42, 0.5), (126, 0.006)))
        report = measure_thd_thdn(capture(samples, rate_hz=Fraction(48_000_000, 1001)), ThdProfile(42, (3, 4)))
        self.assertEqual(len(report.bins), 127)
        self.assertEqual(report.harmonics[0].admitted_power, report.bins[-1].power)
        self.assertPower(report.distortion_power, 0.000018)
        top_hz = 126 * Fraction(48_000_000, 1001 * 253)
        self.assertEqual(report.bins[-1].frequency_hz, top_hz)
        self.assertLess(top_hz, report.epoch.rate_hz / 2)
        high = measure_thd_thdn(capture(samples, rate_hz=report.epoch.rate_hz), ThdProfile(126, band_hz=(top_hz, top_hz)))
        self.assertEqual(high.fundamental_status, "qualified")
        self.assertPower(high.fundamental_power, 0.000018)

    def test_exact_grid_handles_rate_beyond_binary64(self):
        rate = Fraction(2**2048, 3)
        samples = (1, 0, -1, 0)
        frequency = rate / len(samples)
        report = measure_thd_thdn(capture(samples, rate_hz=rate), ThdProfile(1, band_hz=(frequency, frequency)))
        self.assertEqual(report.bins[1].frequency_hz, frequency)
        self.assertEqual(report.fundamental_status, "qualified")
        self.assertEqual(report.fundamental_power, Fraction(1, 2))

    def test_extreme_pcm_scale_does_not_erase_fundamental(self):
        pattern = (1, 0, -1, 0)
        for amplitude in (float.fromhex("0x0.0000000000001p-1022"), sys.float_info.max):
            with self.subTest(amplitude=amplitude):
                samples = tuple(amplitude * value for value in pattern)
                report = measure_thd_thdn(capture(samples), ThdProfile(1, band_hz=(12_000, 12_000)))
                expected_power = Fraction(amplitude) ** 2 / 2
                self.assertEqual(report.fundamental_status, "qualified")
                self.assertAlmostEqual(float(report.fundamental_power / expected_power), 1.0, places=14)
                self.assertEqual(report.thdn_total.linear, 0)

    def test_pcm_gain_scales_power_and_preserves_ratios(self):
        boosted = measure_thd_thdn(capture(tuple(8 * x for x in self.samples)), PROFILE)
        self.assertEqual(boosted.fundamental_power, 64 * self.report.fundamental_power)
        self.assertEqual(boosted.residual_power, 64 * self.report.residual_power)
        self.assertEqual(boosted.thdn_total, self.report.thdn_total)
        self.assertEqual(boosted.thd, self.report.thd)

    def test_select_only_declared_channel(self):
        stereo = replace(EPOCH, channel_ids=("L", "R"))
        samples = CaptureWindow(stereo, ORIGIN, (self.samples, (0,) * FRAMES))
        self.assertEqual(measure_thd_thdn(samples, PROFILE, channel_id="L").thd, self.report.thd)
        self.assertEqual(measure_thd_thdn(samples, PROFILE, channel_id="R").fundamental_status, "zero_power")
        for channel in (None, "M"):
            with self.subTest(channel=channel), self.assertRaisesRegex(ValueError, "channel"):
                measure_thd_thdn(samples, PROFILE, channel_id=channel)

    def test_zero_numerators_with_qualified_reference(self):
        report = measure_thd_thdn(capture(self.samples), replace(PROFILE, band_hz=(1000, 1000)))
        self.assertEqual(report.residual_power, 0)
        for ratio in (report.thd, report.thdn_fundamental, report.thdn_total):
            self.assertEqual((ratio.linear, ratio.percent, ratio.decibels), (0.0, 0.0, -math.inf))

    def test_silence_and_dc_only_are_unavailable(self):
        for sample, expected_band_power in ((0, 0), (0.25, Fraction(1, 16))):
            with self.subTest(sample=sample):
                report = measure_thd_thdn(capture((sample,) * FRAMES), replace(PROFILE, include_dc=True))
                self.assertEqual(report.fundamental_status, "zero_power")
                self.assertEqual(report.band_power, expected_band_power)
                self.assertEqual(report.residual_power, expected_band_power)
                self.assertEqual((report.thd, report.thdn_fundamental, report.thdn_total), (None, None, None))

    def test_out_of_band_fundamental_retains_measured_power(self):
        report = measure_thd_thdn(capture(self.samples), replace(PROFILE, band_hz=(1700, 3000)))
        self.assertEqual(report.fundamental_status, "out_of_band")
        self.assertEqual(report.fundamental_power, self.report.fundamental_power)
        self.assertEqual(report.band_power, report.residual_power)
        self.assertPower(report.residual_power, 0.0000145)
        self.assertEqual((report.thd, report.thdn_fundamental, report.thdn_total), (None, None, None))

    def test_power_floor_is_inclusive_and_retains_powers(self):
        floor = self.report.fundamental_power
        equality = measure_thd_thdn(capture(self.samples), replace(PROFILE, minimum_fundamental_power=floor))
        below = measure_thd_thdn(capture(self.samples), replace(PROFILE, minimum_fundamental_power=floor + 1))
        self.assertEqual(equality.thd, self.report.thd)
        self.assertEqual(below.fundamental_status, "below_floor")
        self.assertEqual(below.fundamental_power, floor)
        self.assertEqual(below.band_power, self.report.band_power)
        self.assertEqual((below.thd, below.thdn_fundamental, below.thdn_total), (None, None, None))

    def test_invalid_profile_values(self):
        for fields in (
            {"fundamental_bin": True}, {"fundamental_bin": 0}, {"harmonic_orders": (1,)},
            {"harmonic_orders": (True,)}, {"harmonic_orders": (2, 2)}, {"harmonic_orders": [2]},
            {"harmonic_orders": tuple(range(2, 67))}, {"band_hz": (0.0, 1200)},
            {"band_hz": (1200, 0)}, {"band_hz": (-1, 1200)}, {"band_hz": (1200,)},
            {"include_dc": 1}, {"minimum_fundamental_power": -1}, {"minimum_fundamental_power": True},
            {"minimum_fundamental_power": math.inf}, {"minimum_fundamental_power": math.nan},
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                replace(PROFILE, **fields)

    def test_invalid_capture_geometry(self):
        for samples, profile in (
            ((1,), ThdProfile(1)), ((1, -1), ThdProfile(1)),
            ((1, 0, -1, 0), ThdProfile(2)), ((1, 0, -1, 0), ThdProfile(3)),
        ):
            with self.subTest(samples=samples, profile=profile), self.assertRaisesRegex(ValueError, "interior"):
                measure_thd_thdn(capture(samples), profile)
        with self.assertRaisesRegex(ValueError, "Nyquist"):
            measure_thd_thdn(capture(self.samples), replace(PROFILE, band_hz=(0, 24_001)))


def tone(frames, frequency, amplitude, phase):
    return tuple(amplitude * math.sin(math.tau * frequency * n / RATE + phase) for n in range(frames))


def known_frequency_residual(samples, frequency):
    """Two-column oracle for the well-conditioned synthetic fixtures below."""
    sines = tone(len(samples), frequency, 1, 0)
    cosines = tuple(math.cos(math.tau * frequency * n / RATE) for n in range(len(samples)))

    def dot(left, right):
        return math.fsum(x * y for x, y in zip(left, right))

    ss, cc, sc = dot(sines, sines), dot(cosines, cosines), dot(sines, cosines)
    ys, yc = dot(samples, sines), dot(samples, cosines)
    determinant = ss * cc - sc * sc
    if determinant <= 0.99 * ss * cc:
        raise ValueError("fixture fit requires nearly orthogonal columns")
    a = (ys * cc - yc * sc) / determinant
    b = (yc * ss - ys * sc) / determinant
    return tuple(y - (a * s + b * c) for y, s, c in zip(samples, sines, cosines))


class OffBinComparatorTests(unittest.TestCase):
    def test_clean_off_bin_tone_and_frequency_error(self):
        samples = tone(4800, 1002.5, 0.5, 0.37)
        original_power = mean_square(samples)
        nearest = known_frequency_residual(samples, 1000)
        self.assertAlmostEqual(math.sqrt(mean_square(nearest) / original_power), 0.43474928946, places=10)
        known = known_frequency_residual(samples, 1002.5)
        self.assertLess(math.sqrt(mean_square(known) / original_power), 3e-15)
        offset = known_frequency_residual(samples, 1003)
        self.assertAlmostEqual(math.sqrt(mean_square(offset) / original_power), 0.0903791, places=6)

    def test_nearby_spur_survives_known_frequency_rejection(self):
        fundamental = tone(4800, 1002.5, 0.5, 0.37)
        spur = tone(4800, 1015, 0.002, -0.8)
        mixed = tuple(a + b for a, b in zip(fundamental, spur))
        residual = known_frequency_residual(mixed, 1002.5)
        spur_after_rejection = known_frequency_residual(spur, 1002.5)
        self.assertGreater(mean_square(residual) / mean_square(spur), 0.95)
        self.assertLess(mean_square(residual), mean_square(spur))
        error = tuple(a - b for a, b in zip(residual, spur_after_rejection))
        self.assertLess(math.sqrt(mean_square(error)), 2e-15)

    def test_joint_line_removal_can_leave_a_cross_term(self):
        fundamental = tone(57, 1002.5, 0.5, 0)
        harmonic = tuple(0.12 * math.cos(math.tau * 2005 * n / RATE - 0.8) for n in range(57))
        combined = tuple(a + b for a, b in zip(fundamental, harmonic))
        cross_power = 2 * math.fsum(a * b for a, b in zip(fundamental, harmonic)) / 57
        self.assertAlmostEqual(cross_power, 0.006146127204540885, places=12)
        self.assertAlmostEqual(mean_square(combined), mean_square(fundamental) + mean_square(harmonic) + cross_power)

    def test_padding_changes_one_bin_mass_at_same_duration(self):
        samples = tone(4800, 1000, 0.5, 0)
        sines = tone(len(samples), 1000, 1, 0)
        dft_magnitude = math.fsum(x * s for x, s in zip(samples, sines))
        for transform_frames, expected in ((4800, 0.125), (9600, 0.0625)):
            with self.subTest(transform_frames=transform_frames):
                integrated_bin = 2 * dft_magnitude**2 / (len(samples) * transform_frames)
                self.assertAlmostEqual(integrated_bin, expected, places=12)
        self.assertAlmostEqual(mean_square(samples), 0.125, places=12)


if __name__ == "__main__":
    unittest.main()
