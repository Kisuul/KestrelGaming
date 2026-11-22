"""Model derivatives, phase branch validity, and transfer support fixtures."""

import cmath
from dataclasses import replace
from fractions import Fraction as F
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in ("audio-oscilloscope", "audio-phase-coherence", "audio-group-delay"):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_group_delay import (
    RationalSection, SlopeProfile, TransferProvenance, TransferSample, WelchQuality,
    model_group_delay, sampled_group_delay, welch_group_delay,
)
from reference_oscilloscope import CaptureWindow, ScopeEpoch
from reference_phase_coherence import WelchProfile, analyze_phase_coherence


RATE = 48_000
BIG = sys.float_info.max
TINY = math.ulp(0.0)


def model(numerator, grid, denominator=(1,), **options):
    return model_group_delay((RationalSection(numerator, denominator),), grid,
                             sample_rate_hz=RATE, **options)


def response(grid, delay, gain=1, rate=RATE):
    bins = []
    for frequency in grid:
        h = gain * cmath.exp(-1j * math.tau * float(F(delay) * frequency / rate))
        bins.append(TransferSample(frequency, h.real, h.imag))
    return tuple(bins)


def slopes(bins, bound, *, mask=None, **options):
    if mask is None:
        mask = (True,) * (len(bins) - 1)
    return sampled_group_delay(bins, SlopeProfile(RATE, bound, **options), supported_edges=mask)


class FilterModels(unittest.TestCase):
    def test_inverted_pure_delay_has_exact_signed_units_on_the_whole_grid(self):
        grid = tuple(F(RATE * k, 128) for k in range(65))
        measured = model((0,) * 12 + (-2,), grid)
        self.assertEqual(measured.sample_rate_hz, RATE)
        self.assertEqual(tuple(p.frequency_hz for p in measured.points), grid)
        for point in measured.points:
            self.assertEqual((point.status, point.delay_samples, point.delay_seconds), ("valid", 12, F(1, 4_000)))
        for point in model((-2,), (0, RATE // 2)).points:
            self.assertEqual((point.status, point.delay_samples), ("valid", 0))

    def test_symmetric_fir_derivative_at_endpoints_and_exact_axes(self):
        half = model((0.5, 0.5), (0, 6000, 12000, 24000)).points
        self.assertEqual((half[0].delay_samples, half[2].delay_samples), (F(1, 2), F(1, 2)))
        self.assertAlmostEqual(float(half[1].delay_samples), 0.5, delta=1e-15)
        self.assertEqual((half[-1].status, half[-1].delay_samples), ("numerator_zero", None))
        one = model((1, 0, 1), (0, 6000, 12000, 18000, 24000)).points
        self.assertEqual([p.delay_samples for p in one], [1, 1, None, 1, 1])
        self.assertEqual(one[2].status, "numerator_zero")

    def test_allpass_closed_form_and_true_endpoint_derivatives(self):
        frequencies = (0, 125, 500, 1_500, 3_000, 24_000)
        c = 0.75
        points = model((-c, 1), frequencies, (1, -c)).points
        self.assertEqual((points[0].delay_samples, points[-1].delay_samples), (7, F(1, 7)))
        for point in points:
            omega = math.tau * float(point.frequency_hz / RATE)
            g = (1 - c*c) / (1 + c*c - 2*c*math.cos(omega))
            self.assertAlmostEqual(float(point.delay_samples), g, delta=2e-13)

    def test_cascade_adds_valid_section_derivatives_and_explicit_bulk_delay(self):
        c = F(3, 4)
        allpass = RationalSection((-c, 1), (1, -c))
        fir = RationalSection((F(1, 2), F(1, 2)))
        grid = (0, 125, 12000, 24000)
        both = model_group_delay((allpass, fir), grid, sample_rate_hz=RATE, bulk_delay_samples=12)
        one = model_group_delay((allpass,), grid, sample_rate_hz=RATE)
        self.assertEqual(both.sections, (allpass, fir))
        self.assertEqual(both.bulk_delay_samples, 12)
        for left, right in zip(both.points[:-1], one.points):
            self.assertAlmostEqual(float(left.delay_samples - right.delay_samples), 12.5, delta=1e-14)
        self.assertEqual(both.points[-1].status, "numerator_zero")

    def test_causal_echo_delay_can_be_negative(self):
        impulse = (1,) + (0,) * 23 + (F(3, 4),)
        dc, tone = model(impulse, (0, 1000)).points
        self.assertEqual((dc.delay_samples, tone.delay_samples), (F(72, 7), -72))
        self.assertEqual(tone.delay_seconds, -F(3, 2000))
        self.assertEqual(impulse.index(max(impulse)), 0)

    def test_distinguishes_zero_pole_and_common_root_from_zero_delay(self):
        notch = RationalSection((1, -1))
        pole = RationalSection((1,), (1, -1))
        cases = ((notch,), (pole,), (notch, pole), (RationalSection((1, -1), (1, -1)),))
        for sections, status in zip(cases, ("numerator_zero", "denominator_zero", "common_zero", "common_zero")):
            dc = model_group_delay(sections, (0,), sample_rate_hz=RATE).points[0]
            self.assertEqual((dc.status, dc.delay_samples, dc.delay_seconds), (status, None, None))
        constant = model((2,), (0,)).points[0]
        self.assertEqual((constant.status, constant.delay_samples), ("valid", 0))

    def test_model_moments_and_relative_floor_are_invariant_to_extreme_gain(self):
        grid = (0, 6000, 12000, 23999, 24000)
        expected = model((1, 1), grid, relative_polynomial_floor=F(1, 1000)).points
        self.assertEqual(expected[-2].status, "below_polynomial_floor")
        for gain in (BIG, TINY, -BIG):
            with self.subTest(gain=gain):
                self.assertEqual(model((gain, gain), grid, relative_polynomial_floor=F(1, 1000)).points,
                                 expected)

    def test_finite_exact_model_delay_beyond_binary64_is_retained(self):
        tiny = F(1, 2**1200)
        dc = model((1,), (0,), (1, tiny - 1)).points[0]
        self.assertEqual((dc.status, dc.delay_samples), ("valid", 2**1200 - 1))

    def test_rational_rate_and_analytic_frequency_coordinates_are_preserved(self):
        rate = F(48_000_000, 1001)
        result = model_group_delay((RationalSection((0, 1)),), (0, rate / 2), sample_rate_hz=rate)
        self.assertEqual((result.sample_rate_hz, result.points[-1].frequency_hz), (rate, rate / 2))
        self.assertEqual(result.points[-1].delay_seconds, 1 / rate)

    def test_model_geometry_and_work_budget_are_validated(self):
        valid = (RationalSection((1, 1)),)
        for grid, extra in (((), {}), ((1, 1), {}), ((0, 24001), {}), ((-1, 0), {}),
                            ((0, math.nan), {}), ((0,), {"relative_polynomial_floor": -1}),
                            ((0,), {"bulk_delay_samples": True})):
            with self.subTest(grid=grid, extra=extra), self.assertRaises(ValueError):
                model_group_delay(valid, grid, sample_rate_hz=RATE, **extra)
        for b, a in (((), (1,)), ((1,), (0,)), ((1,), (0, 1)), ((math.inf,), (1,)), ((1,) * 130, (1,))):
            with self.subTest(numerator_length=len(b), denominator=a), self.assertRaises(ValueError):
                RationalSection(b, a)
        long = RationalSection((1,) * 129, (1,) * 129)
        with self.assertRaisesRegex(ValueError, "work limit"):
            model_group_delay((long, long), tuple(range(1024)), sample_rate_hz=RATE)


class SampledSlopes(unittest.TestCase):
    def test_pure_delays_use_reference_order_and_constant_phase_is_irrelevant(self):
        grid = (0, 375, 750, 1250)
        for delay, gain in ((12, -2), (-12, -2), (0, -2)):
            result = slopes(response(grid, delay, gain), 12)
            self.assertEqual(len(result.points), 3)
            for point in result.points:
                self.assertEqual(point.status, "valid")
                self.assertAlmostEqual(float(point.delay_samples), delay, delta=2e-13)
                self.assertAlmostEqual(float(point.delay_seconds), delay / RATE, delta=5e-18)

    def test_coarse_grid_requires_a_qualified_branch_then_restores_offset(self):
        grid = tuple(F(RATE * k, 64) for k in range(33))
        bins = response(grid, 40)
        self.assertTrue(all(p.status == "unresolved_branch" for p in slopes(bins, None).points))
        self.assertTrue(all(p.status == "unresolved_branch" for p in slopes(bins, 40).points))
        recovered = slopes(bins, 2, fit_advance_samples=38)
        for point in recovered.points:
            self.assertEqual(point.status, "valid")
            self.assertAlmostEqual(float(point.residual_delay_samples), 2, delta=3e-13)
            self.assertAlmostEqual(float(point.delay_samples), 40, delta=3e-13)

    def test_half_turn_equality_and_margin_make_branch_unavailable(self):
        grid = (0, 600)
        point = slopes(response(grid, 40), 40).points[0]
        self.assertEqual((point.status, point.delay_samples), ("unresolved_branch", None))
        point = slopes(response(grid, 5), 30, phase_margin_turns=F(1, 8)).points[0]
        self.assertEqual(point.status, "unresolved_branch")
        exact_half_turn = (TransferSample(0, 1, 0), TransferSample(600, -1, 0))
        self.assertEqual(slopes(exact_half_turn, 39).points[0].status, "unresolved_branch")

    def test_observed_phase_must_agree_with_the_declared_residual_bound(self):
        bins = (TransferSample(0, 1, 0), TransferSample(6000, 0, -1))
        self.assertEqual(slopes(bins, 1).points[0].status, "phase_mismatch")
        allowed = slopes(bins, 1, phase_margin_turns=F(1, 8)).points[0]
        self.assertEqual((allowed.status, allowed.delay_samples), ("valid", 2))

    def test_wide_aperture_sums_adjacent_phase_before_dividing(self):
        grid = tuple(F(RATE * k, 128) for k in range(5))
        result = slopes(response(grid, 40), 40, aperture_steps=4)
        (point,) = result.points
        self.assertEqual((point.frequency_hz, point.low_hz, point.high_hz, point.aperture_hz),
                         (750, 0, 1500, 1500))
        self.assertEqual(len(result.increments), 4)
        self.assertAlmostEqual(float(point.delay_samples), 40, delta=2e-13)

    def test_already_applied_and_fit_advances_are_restored_once(self):
        bins = response((0, 750, 1500, 2250), 35)
        r = slopes(bins, 3, input_advance_samples=5, fit_advance_samples=32)
        for point in r.points:
            self.assertAlmostEqual(float(point.residual_delay_samples), 3, delta=2e-13)
            self.assertAlmostEqual(float(point.delay_samples), 40, delta=2e-13)

    def test_huge_rational_fit_rotation_reduces_before_trigonometry(self):
        advance = 64 * 2**120 + 38
        bins = response((0, 750, 1500), 40)
        result = slopes(bins, 2, fit_advance_samples=advance)
        for point in result.points:
            self.assertAlmostEqual(float(point.residual_delay_samples), 2, delta=2e-13)
            self.assertLess(abs(point.delay_samples - (advance + 2)), F(1, 10**12))

    def test_sampled_zero_breaks_an_aperture_and_preserves_both_sides(self):
        bins = response((0, 375, 750, 1125, 1500), 1)
        bins = bins[:2] + (TransferSample(750, 0, 0),) + bins[3:]
        adjacency = slopes(bins, 2)
        self.assertEqual([p.status for p in adjacency.points], ["valid", "zero_response", "zero_response", "valid"])
        result = slopes(bins, 2, aperture_steps=4)
        self.assertEqual((result.points[0].status, result.points[0].first_failed_edge), ("zero_response", 1))

    def test_nonzero_notch_endpoints_need_continuity_evidence(self):
        f = tuple(F(RATE * k, 126) for k in (30, 31, 32, 33))
        bins = []
        for frequency in f:
            w = math.tau * float(frequency / RATE)
            h = 1 + cmath.exp(-2j * w)
            bins.append(TransferSample(frequency, h.real, h.imag))
        self.assertTrue(all(n.real or n.imag for n in bins))
        result = slopes(bins, 2, mask=(True, False, True))
        self.assertEqual([p.status for p in result.points], ["valid", "unqualified_interval", "valid"])
        for point in (result.points[0], result.points[2]):
            self.assertAlmostEqual(float(point.delay_samples), 1, delta=1e-12)
        wider = slopes(bins, 2, mask=(True, False, True), aperture_steps=3)
        self.assertIsNone(wider.points[0].delay_samples)
        self.assertEqual(wider.points[0].first_failed_edge, 1)

    def test_bin_quality_rejection_blocks_both_adjacent_edges(self):
        points = response((0, 375, 750), 0)
        result = slopes((points[0], replace(points[1], usable=False), points[2]), 0)
        self.assertTrue(all(p.status == "rejected_bin" for p in result.points))

    def test_phase_consistency_cannot_qualify_a_declared_frequency_gap(self):
        points = response((0, 375, 750, 1500), 12)
        result = slopes(points, 12, mask=(True, False, True))
        self.assertEqual([p.status for p in result.points], ["valid", "unqualified_interval", "valid"])
        wider = slopes(points, 12, mask=(True, False, True), aperture_steps=3)
        self.assertEqual(wider.points[0].first_failed_edge, 1)
        self.assertIsNone(wider.points[0].delay_samples)

    def test_using_actual_hz_recovers_slope_on_irregular_grid(self):
        grid = (100, 145, 300, 310, 425, 659)
        result = slopes(response(grid, 12, -2), 12, aperture_steps=2)
        self.assertEqual([p.aperture_hz for p in result.points], [200, 165, 125, 349])
        for point in result.points:
            self.assertAlmostEqual(float(point.delay_samples), 12, delta=1e-12)

    def test_exact_endpoint_products_survive_binary64_extremes(self):
        for x in (BIG, TINY):
            bins = (TransferSample(0, x, x), TransferSample(12000, x, -x))
            (point,) = slopes(bins, 1).points
            self.assertEqual((point.status, point.delay_samples, point.delay_seconds), ("valid", 1, F(1, RATE)))

    def test_phase_angle_underflow_has_its_own_state(self):
        bins = (TransferSample(0, BIG, 0), TransferSample(12000, BIG, TINY))
        (point,) = slopes(bins, 1).points
        self.assertEqual((point.status, point.delay_samples), ("phase_underflow", None))

    def test_aperture_noise_examples_preserve_different_noiseless_secants(self):
        c = 0.98
        for grid, expected in (((190, 210), 36.981683), ((20, 200, 380), 44.826944)):
            bins = []
            for f in grid:
                z = cmath.exp(-1j * math.tau * f / RATE)
                h = (z - c) / (1 - c * z)
                bins.append(TransferSample(f, h.real, h.imag))
            (point,) = slopes(bins, 100, aperture_steps=len(grid)-1).points
            self.assertAlmostEqual(float(point.delay_samples), expected, delta=5e-7)

    def test_profile_grid_and_mask_require_explicit_finite_coordinates(self):
        base = SlopeProfile(RATE, 5)
        for change in ({"sample_rate_hz": 0}, {"residual_bound_samples": -1},
                       {"phase_margin_turns": 0.5}, {"input_advance_samples": math.nan},
                       {"aperture_steps": True}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(base, **change)
        good = TransferSample(0, 1, 0)
        for bins, mask in (((good, good), (True,)),
                           ((good, TransferSample(25_000, 1, 0)), (True,)),
                           ((good, TransferSample(1, 1, 0)), (1,)), ((good, good), ())):
            with self.subTest(bins=bins, mask=mask), self.assertRaises(ValueError):
                sampled_group_delay(bins, base, supported_edges=mask)
        with self.assertRaises(ValueError):
            TransferSample(0, 1, math.inf)


class PairedWelchTransfer(unittest.TestCase):
    def setUp(self):
        self.epoch = ScopeEpoch("run-a", 0, F(RATE), "aligned-clock", "paired-inputs", "FS", ("X", "Y"))

    def analyze(self, x, y, size, reference="X", measurement="Y"):
        capture = CaptureWindow(self.epoch, 7, (x, y))
        return analyze_phase_coherence(capture, WelchProfile((1,) * size, size, size),
                                       reference_channel=reference, measurement_channel=measurement)

    def test_paired_impulses_keep_clock_support_and_both_delay_signs(self):
        x, y = [0] * 768, [0] * 768
        for j in range(6):
            at = 128*j + 21 + 7*j
            x[at], y[at + 12] = 1 + j/8, -2 * (1 + j/8)
        for first, last, expected in (("X", "Y", 12), ("Y", "X", -12)):
            with self.subTest(reference=first):
                data = self.analyze(x, y, 128, first, last)
                provenance = TransferProvenance(first, last, "aligned-clock", "run-a", (7, 775), (7, 775))
                result = welch_group_delay(data, SlopeProfile(RATE, 12),
                                           supported_edges=(True,) * 64, provenance=provenance)
                self.assertIs(result.welch, data)
                self.assertIs(result.provenance, provenance)
                self.assertEqual(result.welch.used_end_sample_exclusive, 775)
                self.assertEqual(len(result.points), 64)
                for point in result.points:
                    self.assertEqual(point.status, "valid")
                    self.assertAlmostEqual(float(point.delay_samples), expected, delta=2e-13)

    def test_single_excited_bin_has_unity_coherence_and_no_usable_slope(self):
        data = self.analyze([1, 0, -1, 0] * 16, [0, 1, 0, -1] * 16, 32)
        result = welch_group_delay(data, SlopeProfile(RATE, 2), supported_edges=(True,) * 16,
                                   quality=WelchQuality(minimum_coherence=1))
        self.assertEqual([s.frequency_hz for s in result.samples if s.usable], [12_000])
        self.assertEqual(data.bins[8].magnitude_squared_coherence, 1)
        self.assertTrue(all(p.status == "rejected_bin" for p in result.points))

    def test_independent_welch_density_floors_reject_qualifying_coherence(self):
        data = self.analyze([1, 0] * 2, [2, 0] * 2, 2)
        for quality in (WelchQuality(reference_density_floor=1), WelchQuality(measurement_density_floor=1)):
            result = welch_group_delay(data, SlopeProfile(RATE, 0), supported_edges=(True,), quality=quality)
            self.assertIs(result.quality, quality)
            self.assertEqual(result.points[0].status, "rejected_bin")

    def test_welch_coherence_gate_rejects_an_energized_transfer(self):
        data = self.analyze([1, 0, 1, 0], [1, 0, 3, 0], 2)
        self.assertTrue(all(row.magnitude_squared_coherence == F(4, 5) for row in data.bins))
        result = welch_group_delay(data, SlopeProfile(RATE, 0), supported_edges=(True,),
                                   quality=WelchQuality(minimum_coherence=F(9, 10)))
        self.assertTrue(all(s.real > 0 and not s.usable for s in result.samples))
        self.assertEqual(result.points[0].status, "rejected_bin")

    def test_warmup_and_provenance_mismatch_remain_explicit(self):
        warm = self.analyze([1, 0], [1, 0], 2)
        result = welch_group_delay(warm, SlopeProfile(RATE, 0), supported_edges=())
        self.assertTrue(result.welch.warming_up)
        self.assertEqual(result.points, ())
        with self.assertRaisesRegex(ValueError, "sample rate"):
            welch_group_delay(warm, SlopeProfile(44_100, 0), supported_edges=())
        other = TransferProvenance("a", "b", "another-clock", "run-a", (7, 9), (7, 9))
        with self.assertRaisesRegex(ValueError, "clock domain"):
            welch_group_delay(warm, SlopeProfile(RATE, 0), supported_edges=(), provenance=other)


if __name__ == "__main__":
    unittest.main()
