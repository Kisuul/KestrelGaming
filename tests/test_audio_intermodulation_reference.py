"""Analytic two-tone level, alias mapping, and measurement qualification fixtures."""

from dataclasses import replace
from fractions import Fraction as F
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
for skill in ("audio-intermodulation", "audio-oscilloscope", "audio-power-spectral-density", "audio-test-signals"):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_intermodulation import ImdProfile, measure_intermodulation
from reference_oscilloscope import CaptureWindow, ScopeEpoch
from reference_test_signals import ChannelSignal, SignalPlan, Tone, render_signal


ORIGIN = 2**60 + 37
RATE = 48_000
FRAMES = 480
EPOCH = ScopeEpoch("settled", ORIGIN, F(RATE), "adc", "post-drive", "FS", ("M",))
DIFFERENCE = (-1, 1)
SUM = (1, 1)
LOW_IM3 = (2, -1)
HIGH_IM3 = (-1, 2)
PRODUCTS = (DIFFERENCE, SUM, LOW_IM3, HIGH_IM3)
PROFILE = ImdProfile((70, 80), PRODUCTS, "digital_fold", "both_carriers")


def signal(carriers=(70, 80), *, frames=FRAMES, rate=RATE, peaks=(0.2, 0.1), phases=(0, 0)):
    epoch = replace(EPOCH, rate_hz=F(rate))
    recipe = ChannelSignal(tuple(
        Tone(F(index) * epoch.rate_hz / frames, peak, F(1, 4) + phase)
        for index, peak, phase in zip(carriers, peaks, phases)
    ))
    block = render_signal(SignalPlan(epoch, ORIGIN, frames, (recipe,)))
    return CaptureWindow(epoch, ORIGIN, block.planes)


def polynomial(source, linear=1, square=0.05, cubic=0.1):
    samples = tuple(linear*x + square*x*x + cubic*x*x*x for x in source.planes[0])
    return CaptureWindow(source.epoch, source.start_sample, (samples,))


def measure(capture, profile=PROFILE):
    return measure_intermodulation(capture, profile, channel_id="M")


class IntermodulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = signal()
        cls.response = polynomial(cls.source)
        cls.report = measure(cls.response)

    def assertLevel(self, actual, expected, *, tolerance=1e-10):
        self.assertTrue(math.isclose(actual, expected, rel_tol=tolerance), (float(actual), expected))

    def test_records_exact_capture_support_and_bin_grid(self):
        report = self.report
        self.assertEqual(report.epoch, EPOCH)
        self.assertEqual(report.channel_id, "M")
        self.assertEqual((report.start_sample, report.end_sample_exclusive), (ORIGIN, ORIGIN + FRAMES))
        self.assertEqual(report.bin_width_hz, F(100))
        self.assertEqual(report.band_hz, (0, 24_000))
        self.assertEqual(len(report.bins), 241)
        self.assertEqual(report.bins[70].frequency_hz, 7000)
        self.assertEqual(report.profile, PROFILE)

    def test_coherent_mixed_product_levels(self):
        for product, pair, index, peak in zip(
            self.report.products, PRODUCTS, (10, 150, 60, 90), (0.001, 0.001, 0.0003, 0.00015),
        ):
            with self.subTest(pair=pair):
                self.assertEqual(product.status, "resolved")
                self.assertEqual(product.coefficients, pair)
                self.assertEqual(product.order, sum(map(abs, pair)))
                self.assertEqual(product.nominal_bin, index)
                self.assertIs(product.observed_bin, self.report.bins[index])
                self.assertLevel(product.observed_bin.peak_amplitude, peak)
                self.assertLevel(product.observed_bin.power, peak**2 / 2)

    def test_output_carrier_power_defines_the_reference(self):
        report = self.report
        for line, peak, power in zip(report.carriers, (0.2009, 0.100675), (0.020180405, 0.0050677278125)):
            self.assertEqual(line.status, "resolved")
            self.assertLevel(line.observed_bin.peak_amplitude, peak)
            self.assertLevel(line.observed_bin.power, power)
        self.assertEqual(report.reference_power, sum(line.observed_bin.power for line in report.carriers))
        self.assertLevel(report.reference_power, 0.0252481328125)

    def test_named_carrier_references_and_im3_group(self):
        for ref, line_db, pair_db, pair_percent in (
            ("low_carrier", -56.5171736406, -55.5480735105, 0.1669538061847),
            ("high_carrier", -50.5160076712, -49.5469075411, 0.3331613574621),
            ("both_carriers", -57.4901675227, -56.5210673927, 0.1492610974148),
        ):
            with self.subTest(reference=ref):
                report = measure(self.response, replace(PROFILE, products=(LOW_IM3, HIGH_IM3), ratio_reference=ref))
                self.assertLevel(report.aggregate_power, 5.625e-8)
                self.assertAlmostEqual(report.products[0].ratio.decibels, line_db, places=8)
                self.assertAlmostEqual(report.aggregate_ratio.decibels, pair_db, places=8)
                self.assertLevel(report.aggregate_ratio.percent, pair_percent)

    def test_im2_group_uses_power_sum(self):
        report = measure(self.response, replace(PROFILE, products=(DIFFERENCE, SUM)))
        self.assertLevel(report.aggregate_power, 1e-6)
        self.assertLevel(report.aggregate_ratio.percent, 0.6293400451828085)
        self.assertGreater(0.6631849457017327 - report.aggregate_ratio.percent, 0.03)

    def test_input_level_sweep_uses_absolute_line_growth(self):
        doubled = measure(polynomial(signal(peaks=(0.4, 0.2))))
        for base, driven, expected in zip(self.report.products, doubled.products, (4, 4, 8, 8)):
            growth = driven.observed_bin.peak_amplitude / base.observed_bin.peak_amplitude
            self.assertLevel(growth, expected)
        self.assertGreater(doubled.reference_power, 4 * self.report.reference_power)

    def test_linear_square_and_cubic_controls(self):
        linear = measure(self.source)
        square = measure(polynomial(self.source, cubic=0))
        cubic = measure(polynomial(self.source, square=0))
        for i, base in enumerate(self.report.products):
            with self.subTest(product=base.coefficients):
                self.assertLess(linear.products[i].observed_bin.peak_amplitude, 1e-14)
                expected = square if base.order == 2 else cubic
                other = cubic if base.order == 2 else square
                self.assertLevel(expected.products[i].observed_bin.peak_amplitude, float(base.observed_bin.peak_amplitude))
                self.assertLess(other.products[i].observed_bin.peak_amplitude, 1e-14)

    def test_band_endpoint_is_inclusive_and_keeps_partial_group_unavailable(self):
        report = measure(self.response, replace(PROFILE, band_hz=(1000, 9000)))
        diff, above_band, low, high = report.products
        self.assertTrue(diff.observed_bin.admitted)
        self.assertTrue(high.observed_bin.admitted)
        self.assertEqual(above_band.status, "out_of_band")
        self.assertFalse(above_band.observed_bin.admitted)
        self.assertLevel(above_band.observed_bin.power, 5e-7)
        self.assertIsNone(above_band.ratio)
        self.assertIsNotNone(low.ratio)
        self.assertIsNone(report.aggregate_power)
        self.assertIsNone(report.aggregate_ratio)
        subset = measure(self.response, replace(report.profile, products=(LOW_IM3, HIGH_IM3)))
        self.assertLevel(subset.aggregate_power, 5.625e-8)

    def test_carrier_outside_band_keeps_raw_lines(self):
        report = measure(self.response, replace(PROFILE, band_hz=(1000, 7000), ratio_reference="low_carrier"))
        self.assertEqual(report.carriers[0].status, "resolved")
        self.assertEqual(report.carriers[1].status, "out_of_band")
        self.assertLevel(report.carriers[1].observed_bin.power, 0.0050677278125)
        self.assertIsNone(report.reference_power)
        self.assertIsNone(report.products[0].ratio)

    def test_floor_qualifies_both_carriers_at_equality(self):
        low, high = self.report.carriers
        floor = high.observed_bin.power
        qualified = measure(self.response, replace(PROFILE, minimum_carrier_power=floor))
        weak = measure(self.response, replace(PROFILE, ratio_reference="low_carrier", minimum_carrier_power=2*floor))
        self.assertEqual(qualified.carriers[1].status, "resolved")
        self.assertEqual(qualified.aggregate_ratio, self.report.aggregate_ratio)
        self.assertEqual(weak.carriers[0].observed_bin.power, low.observed_bin.power)
        self.assertEqual(weak.carriers[1].status, "below_floor")
        self.assertEqual(weak.aggregate_power, self.report.aggregate_power)
        self.assertIsNone(weak.reference_power)
        self.assertIsNone(weak.aggregate_ratio)

    def test_silence_or_dc_has_no_carrier_reference(self):
        for level in (0, 0.125):
            with self.subTest(level=level):
                captured = CaptureWindow(EPOCH, ORIGIN, ((level,) * FRAMES,))
                report = measure(captured)
                self.assertEqual([line.status for line in report.carriers], ["zero_power"] * 2)
                self.assertEqual(report.bins[0].power, F(level)**2)
                self.assertEqual(report.aggregate_power, 0)
                self.assertIsNone(report.reference_power)
                self.assertIsNone(report.aggregate_ratio)

    def test_qualified_zero_power_ratio_has_minus_infinity(self):
        # Supply exact zeros at product bins to isolate ratio behavior from DFT roundoff.
        powers = [F(0)] * (FRAMES//2 + 1)
        powers[70], powers[80] = F(1, 50), F(1, 200)
        with patch("reference_intermodulation._coherent_powers", return_value=tuple(powers)):
            report = measure(self.response)
        self.assertEqual(report.aggregate_power, 0)
        for ratio in (report.aggregate_ratio, *(line.ratio for line in report.products)):
            self.assertEqual((ratio.linear, ratio.percent, ratio.decibels), (0.0, 0.0, -math.inf))

    def test_signed_nominal_below_zero_reflects_without_alias_marker(self):
        source = signal((30, 70))
        profile = replace(PROFILE, carrier_bins=(30, 70), products=(LOW_IM3,))
        report = measure(polynomial(source, square=0), profile)
        (line,) = report.products
        self.assertEqual((line.nominal_bin, line.nominal_frequency_hz), (-10, -1000))
        self.assertEqual(line.observed_bin.index, 10)
        self.assertEqual(line.observed_bin.candidates, (LOW_IM3,))
        self.assertIsNone(line.possible_fold_bin)
        self.assertLevel(line.observed_bin.peak_amplitude, 0.0003)

    def test_conjugate_labels_change_sign_but_keep_the_same_line_measurement(self):
        positive = measure(self.response, replace(PROFILE, products=(DIFFERENCE,)))
        negative = measure(self.response, replace(PROFILE, products=((1, -1),)))
        self.assertEqual((positive.products[0].nominal_bin, negative.products[0].nominal_bin), (10, -10))
        self.assertEqual(positive.products[0].observed_bin, negative.products[0].observed_bin)
        self.assertEqual(positive.aggregate_ratio, negative.aggregate_ratio)

    def test_quadratic_sum_folds_at_48k_and_is_direct_at_96k(self):
        for rate, frames, index, expected_fold in ((48_000, 480, 90, 90), (96_000, 960, 390, None)):
            with self.subTest(rate=rate):
                source = signal((190, 200), frames=frames, rate=rate)
                square = polynomial(source, linear=0, square=1, cubic=0)
                profile = ImdProfile((190, 200), (SUM,), "digital_fold", "both_carriers", 2,
                                     minimum_carrier_power=1e-12)
                report = measure(square, profile)
                (line,) = report.products
                self.assertEqual(line.status, "resolved")
                self.assertEqual(line.nominal_frequency_hz, 39_000)
                self.assertEqual(line.possible_fold_bin, expected_fold)
                self.assertEqual(line.observed_bin.index, index)
                self.assertLevel(line.observed_bin.peak_amplitude, 0.02)
                self.assertIsNone(report.reference_power)
                cubic_family = measure(square, replace(profile, max_order=3))
                self.assertEqual(cubic_family.products[0].status, "collision")
                self.assertIn((3, 0), cubic_family.products[0].observed_bin.candidates)

    def test_band_limited_policy_keeps_the_possible_fold_as_diagnostic(self):
        source = signal((190, 200))
        profile = ImdProfile((190, 200), (SUM,), "band_limited", "both_carriers", 2)
        report = measure(source, profile)
        (line,) = report.products
        self.assertEqual(line.status, "above_nyquist")
        self.assertEqual(line.possible_fold_bin, 90)
        self.assertNotIn(SUM, report.bins[90].candidates)
        self.assertIsNone(line.observed_bin)
        self.assertIsNone(report.aggregate_ratio)

    def test_negative_out_of_region_uses_integer_fold_geometry(self):
        source = signal((190, 200))
        report = measure(source, replace(PROFILE, carrier_bins=(190, 200), products=((-1, -2),)))
        (line,) = report.products
        self.assertEqual(line.nominal_bin, -590)
        self.assertEqual(line.possible_fold_bin, 110)
        self.assertEqual(line.observed_bin.index, 110)
        self.assertIn((1, 2), line.observed_bin.candidates)

    def test_full_candidate_family_preserves_carrier_and_dc_collisions(self):
        source = signal((40, 80))
        profile = replace(PROFILE, carrier_bins=(40, 80), products=(DIFFERENCE, LOW_IM3, HIGH_IM3))
        report = measure(polynomial(source), profile)
        difference, dc, upper = report.products
        self.assertEqual(report.carriers[0].status, "collision")
        self.assertEqual(report.carriers[1].status, "collision")
        self.assertIs(difference.observed_bin, report.carriers[0].observed_bin)
        self.assertEqual(set(difference.observed_bin.candidates), {(1, 0), (1, -1)})
        self.assertEqual(set(report.carriers[1].observed_bin.candidates), {(0, 1), (2, 0)})
        self.assertEqual(dc.status, "collision")
        self.assertEqual(dc.observed_bin.index, 0)
        self.assertEqual(set(dc.observed_bin.candidates), {(0, 0), LOW_IM3})
        self.assertFalse(dc.observed_bin.admitted)
        self.assertEqual(set(upper.observed_bin.candidates), {(1, -2), SUM, (3, 0)})
        self.assertIsNone(report.reference_power)
        self.assertIsNone(report.aggregate_power)

    def test_aliased_dc_keeps_collision_even_when_dc_is_admitted(self):
        profile = replace(PROFILE, carrier_bins=(80, 200), products=((1, 2),), include_dc=True)
        report = measure(polynomial(signal((80, 200))), profile)
        (line,) = report.products
        self.assertEqual(line.nominal_bin, 480)
        self.assertEqual(line.possible_fold_bin, 0)
        self.assertTrue(line.observed_bin.admitted)
        self.assertEqual(line.status, "collision")
        self.assertIn((0, 0), line.observed_bin.candidates)
        self.assertIsNone(line.ratio)

    def test_phase_changes_the_total_amplitude_of_one_collided_bin(self):
        profile = replace(PROFILE, carrier_bins=(90, 150), products=(HIGH_IM3,))
        for phase, expected_peak in ((F(0), 0.00035), (F(1, 4), 0.00005)):
            with self.subTest(phase=phase):
                data = polynomial(signal((90, 150), phases=(0, phase)), square=0)
                report = measure(data, profile)
                (line,) = report.products
                self.assertIsNone(line.possible_fold_bin)
                self.assertEqual(line.status, "collision")
                self.assertEqual(line.observed_bin.index, 210)
                self.assertEqual(set(line.observed_bin.candidates), {(1, -2), (3, 0)})
                self.assertLevel(line.observed_bin.peak_amplitude, expected_peak)
                self.assertIsNone(line.ratio)
                self.assertIsNone(report.aggregate_power)

    def test_endpoint_power_weights_and_nyquist_policy(self):
        for frames, expected_power in ((32, 0.0004), (33, 0.0002)):
            with self.subTest(frames=frames):
                source = signal((5, 11), frames=frames)
                data = polynomial(source, square=1, cubic=0)
                profile = ImdProfile((5, 11), (SUM,), "digital_fold", "both_carriers", max_order=2)
                report = measure(data, profile)
                (line,) = report.products
                self.assertEqual(line.status, "resolved")
                self.assertEqual(line.observed_bin.index, 16)
                self.assertEqual(line.observed_bin.paired, frames == 33)
                self.assertLevel(line.observed_bin.power, expected_power)
                self.assertLevel(line.observed_bin.peak_amplitude, 0.02)
                excluded = measure(data, replace(profile, include_nyquist=False))
                self.assertEqual(excluded.products[0].status, "excluded_endpoint" if frames == 32 else "resolved")
                self.assertLevel(excluded.products[0].observed_bin.power, expected_power)
                if frames == 32:
                    self.assertLevel(report.aggregate_ratio.linear, math.sqrt(0.0004 / 0.025))
                    self.assertIsNone(excluded.aggregate_power)

    def test_report_keeps_unassigned_power_and_parseval_closure(self):
        observed = math.fsum(sample**2 for sample in self.response.planes[0]) / FRAMES
        bins = self.report.bins
        self.assertLevel(sum(entry.power for entry in bins), observed)
        self.assertFalse(bins[0].admitted)
        self.assertEqual(bins[10].candidates, ((1, -1),))
        self.assertEqual(bins[11].candidates, ())

    def test_exact_rational_rate_and_band_edge(self):
        rate = F(2**2050, 1001)
        data = CaptureWindow(replace(EPOCH, rate_hz=rate), ORIGIN, self.response.planes)
        width = rate / FRAMES
        report = measure(data, replace(PROFILE, band_hz=(10*width, 90*width)))
        self.assertEqual(report.bin_width_hz, width)
        self.assertEqual(report.products[0].nominal_frequency_hz, 10*width)
        self.assertTrue(report.products[0].observed_bin.admitted)
        self.assertTrue(report.products[-1].observed_bin.admitted)
        self.assertEqual(report.products[1].status, "out_of_band")

    def test_power_of_two_pcm_gain_preserves_the_ratios(self):
        boosted = CaptureWindow(EPOCH, ORIGIN, (tuple(8*x for x in self.response.planes[0]),))
        actual = measure(boosted)
        self.assertEqual(actual.reference_power, 64*self.report.reference_power)
        self.assertEqual(actual.aggregate_power, 64*self.report.aggregate_power)
        self.assertEqual(actual.aggregate_ratio, self.report.aggregate_ratio)

    def test_extreme_finite_pcm_keeps_power_when_peak_exceeds_float(self):
        largest = sys.float_info.max
        capture = CaptureWindow(EPOCH, ORIGIN, ((largest, largest, -largest, -largest) * 16,))
        profile = ImdProfile((5, 16), (DIFFERENCE,), "digital_fold", "both_carriers", 2)
        report = measure(capture, profile)
        self.assertIsNone(report.bins[16].peak_amplitude)
        self.assertAlmostEqual(float(report.bins[16].power / (F(largest)**2)), 1, places=14)

    def test_selects_a_declared_capture_channel(self):
        stereo = replace(EPOCH, channel_ids=("L", "R"))
        capture = CaptureWindow(stereo, ORIGIN, (self.response.planes[0], (0,) * FRAMES))
        left = measure_intermodulation(capture, PROFILE, channel_id="L")
        right = measure_intermodulation(capture, PROFILE, channel_id="R")
        self.assertEqual(left.aggregate_ratio, self.report.aggregate_ratio)
        self.assertIsNone(right.reference_power)
        with self.assertRaisesRegex(ValueError, "channel"):
            measure_intermodulation(capture, PROFILE, channel_id="M")

    def test_reject_invalid_profiles(self):
        for fields in (
            {"carrier_bins": (70, 70)}, {"carrier_bins": (80, 70)}, {"carrier_bins": (True, 70)},
            {"products": ()}, {"products": [(1, 1)]}, {"products": ((1, 0),)},
            {"products": ((1, True),)}, {"products": ((-1, 1), (1, -1))}, {"products": ((2, 2),)},
            {"max_order": True}, {"max_order": 4}, {"max_order": 2},
            {"sampling_policy": "guess"}, {"ratio_reference": "carrier"},
            {"band_hz": (0.0, 1200)}, {"band_hz": (2000, 1000)}, {"band_hz": (-1, 1000)},
            {"include_dc": 1}, {"include_nyquist": 1}, {"minimum_carrier_power": True},
            {"minimum_carrier_power": -1}, {"minimum_carrier_power": math.nan},
            {"minimum_carrier_power": math.inf},
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                replace(PROFILE, **fields)

    def test_rejects_outside_capture_geometry(self):
        for size, bins in ((4, (1, 2)), (480, (10, 240)), (480, (10, 241))):
            with self.subTest(size=size, bins=bins), self.assertRaisesRegex(ValueError, "interior"):
                capture = CaptureWindow(EPOCH, ORIGIN, ((0,) * size,))
                measure(capture, replace(PROFILE, carrier_bins=bins))
        with self.assertRaisesRegex(ValueError, "Nyquist"):
            measure(self.response, replace(PROFILE, band_hz=(0, 24_001)))


if __name__ == "__main__":
    unittest.main()
