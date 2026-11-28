"""Paired transfer fixtures for noise models, support, range, and timing."""

from dataclasses import replace
from fractions import Fraction as F
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in ("audio-transfer-response", "audio-phase-coherence", "audio-group-delay", "audio-oscilloscope"):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_group_delay import SlopeProfile, TransferProvenance, TransferSample, sampled_group_delay
from reference_oscilloscope import CaptureWindow, ScopeEpoch
from reference_phase_coherence import WelchProfile, analyze_phase_coherence
from reference_transfer_response import TransferQuality, analyze_transfer_response


RATE = F(48_000)
ORIGIN = 2**60 + 37
EPOCH = ScopeEpoch("pair", ORIGIN, RATE, "sample-clock", "capture", "PCM", ("X", "Y"))


def pulse(frames, *samples):
    values = [0] * frames
    for index, amplitude in samples:
        values[index] = amplitude
    return tuple(values)


def analysis(x, y, frames, *, epoch=EPOCH, reverse=False):
    capture = CaptureWindow(epoch, ORIGIN, (x, y))
    profile = WelchProfile((1,) * frames, frames, frames)
    reference, measurement = ("Y", "X") if reverse else ("X", "Y")
    return analyze_phase_coherence(capture, profile, reference_channel=reference, measurement_channel=measurement)


def values(estimate):
    return estimate.real, estimate.imag


def measure_delay(report, bound):
    grid = tuple(
        TransferSample(point.spectra.frequency_hz, point.h1.real, point.h1.imag,
                       usable=point.h1_status == "qualified")
        for point in report.bins
    )
    slope = SlopeProfile(report.paired.epoch.rate_hz, bound, input_advance_samples=report.output_advance_samples)
    return sampled_group_delay(grid, slope, supported_edges=(True,) * (len(grid)-1),
                               provenance=report.provenance)


def output_noise():
    x = pulse(32, (2, .25))
    y = pulse(32, (2, .75)) + pulse(32, (2, .25))
    return analysis(x+x, y, 32)


def input_noise(*, reverse=False):
    cosine, sine = (1, 0, -1, 0) * 4, (0, 1, 0, -1) * 4
    x = tuple(.375*v for v in cosine) + tuple(.125*v for v in cosine)
    y = tuple(.5*v for v in sine) * 2
    return analysis(x, y, 16, reverse=reverse)


class TransferEstimatorTests(unittest.TestCase):
    def test_output_noise_different_magnitudes(self):
        transfer = analyze_transfer_response(output_noise())
        point = transfer.bins[3]
        self.assertEqual(values(point.h1), (2, 0))
        self.assertEqual(values(point.h2), (F(5, 2), 0))
        self.assertEqual(point.h1.magnitude_squared, 4)
        self.assertEqual(point.h2.magnitude, 2.5)
        self.assertAlmostEqual(point.h1.magnitude_db, 20 * math.log10(2), places=13)
        self.assertEqual(point.spectra.phase_radians, 0)
        self.assertEqual(point.spectra.magnitude_squared_coherence, F(4, 5))
        self.assertEqual((point.h1_status, point.h2_status), ("qualified", "qualified"))

    def test_input_noise_and_h2_conjugate(self):
        transfer = analyze_transfer_response(input_noise())
        point = transfer.bins[4]
        self.assertEqual(values(point.h1), (0, F(-8, 5)))
        self.assertEqual(values(point.h2), (0, -2))
        self.assertEqual(point.spectra.phase_radians, -math.pi / 2)
        self.assertEqual(point.spectra.magnitude_squared_coherence, F(4, 5))

    def test_h1_over_h2_is_coherence(self):
        for paired in (output_noise(), input_noise()):
            for point in analyze_transfer_response(paired).bins:
                if point.h1_status == "qualified":
                    gamma = point.spectra.magnitude_squared_coherence
                    self.assertEqual(values(point.h1), (point.h2.real*gamma, point.h2.imag*gamma))

    def test_reverse_path_conjugates_phase_and_interchanges_reciprocals(self):
        forward = analyze_transfer_response(input_noise()).bins[4]
        reverse = analyze_transfer_response(input_noise(reverse=True)).bins[4]
        self.assertEqual(values(reverse.h1), (0, F(1, 2)))
        self.assertEqual(values(reverse.h2), (0, F(5, 8)))
        self.assertEqual(reverse.spectra.phase_radians, -forward.spectra.phase_radians)
        self.assertEqual(reverse.spectra.magnitude_squared_coherence, forward.spectra.magnitude_squared_coherence)

    def test_true_zero_output_has_zero_h1_and_unavailable_h2(self):
        x = pulse(256, (32, 1)) * 2
        y = pulse(256, (32, .5), (33, .5)) * 2
        report = analyze_transfer_response(analysis(x, y, 256))
        self.assertEqual(values(report.bins[0].h1), (1, 0))
        nyquist = report.bins[-1]
        self.assertEqual(nyquist.spectra.frequency_hz, RATE/2)
        self.assertEqual(nyquist.spectra.measurement_density, 0)
        self.assertEqual(values(nyquist.h1), (0, 0))
        self.assertEqual(nyquist.h1.magnitude, 0)
        self.assertEqual(nyquist.h1.magnitude_db, -math.inf)
        self.assertIsNone(nyquist.h2)
        self.assertIsNone(nyquist.spectra.phase_radians)
        self.assertIsNone(nyquist.spectra.magnitude_squared_coherence)
        self.assertEqual((nyquist.h1_status, nyquist.h2_status), ("zero_output", "zero_output"))
        self.assertEqual(measure_delay(report, 2).points[-1].status, "rejected_bin")

    def test_cross_cancellation_retains_positive_auto_powers(self):
        x = pulse(32, (3, .25))
        y = x + tuple(-v for v in x)
        report = analyze_transfer_response(analysis(x+x, y, 32))
        point = report.bins[3]
        self.assertGreater(point.spectra.reference_density, 0)
        self.assertGreater(point.spectra.measurement_density, 0)
        self.assertEqual(point.spectra.magnitude_squared_coherence, 0)
        self.assertEqual(point.spectra.energized_pairs, 2)
        self.assertEqual(values(point.h1), (0, 0))
        self.assertIsNone(point.h2)
        self.assertIsNone(point.spectra.phase_radians)
        self.assertEqual((point.h1_status, point.h2_status), ("zero_cross", "zero_cross"))

    def test_zero_reference_has_no_estimate(self):
        for y in ((0,) * 64, pulse(32, (2, .25)) * 2):
            with self.subTest(energized=bool(sum(y))):
                report = analyze_transfer_response(analysis((0,)*64, y, 32))
                self.assertGreaterEqual(report.bins[0].spectra.measurement_density, 0)
                self.assertTrue(all(point.h1 is point.h2 is None for point in report.bins))
                self.assertTrue(all(point.h1_status == point.h2_status == "unexcited" for point in report.bins))

    def test_even_endpoint_inversion_retains_pi_phase(self):
        x = pulse(32, (2, .25)) * 2
        y = tuple(-v for v in x)
        transfer = analyze_transfer_response(analysis(x, y, 32))
        for point in (transfer.bins[0], transfer.bins[-1]):
            self.assertEqual(values(point.h1), (-1, 0))
            self.assertEqual(values(point.h2), (-1, 0))
            self.assertEqual(point.spectra.phase_radians, math.pi)


class TransferQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paired = output_noise()
        cls.source = cls.paired.bins[0]

    def test_keeps_the_original_paired_data(self):
        report = analyze_transfer_response(self.paired)
        self.assertIs(report.paired, self.paired)
        self.assertIs(report.bins[0].spectra, self.source)
        self.assertEqual((report.reference_units, report.measurement_units), ("PCM", "PCM"))

    def test_density_and_coherence_floors_include_equality(self):
        quality = TransferQuality(
            minimum_coherence=self.source.magnitude_squared_coherence,
            reference_density_floor=self.source.reference_density,
            measurement_density_floor=self.source.measurement_density,
        )
        report = analyze_transfer_response(self.paired, quality=quality)
        self.assertIs(report.quality, quality)
        self.assertEqual(report.bins[0].h1_status, "qualified")
        self.assertEqual(report.bins[0].h2_status, "qualified")

    def test_common_quality_gates_preserve_raw_values(self):
        for quality, status in (
            (TransferQuality(reference_density_floor=2*self.source.reference_density), "weak_reference"),
            (TransferQuality(measurement_density_floor=2*self.source.measurement_density), "weak_output"),
            (TransferQuality(minimum_coherence=F(9, 10)), "low_coherence"),
            (TransferQuality(minimum_energized_pairs=3), "insufficient_energized_pairs"),
        ):
            with self.subTest(status=status):
                point = analyze_transfer_response(self.paired, quality=quality).bins[0]
                self.assertEqual((point.h1_status, point.h2_status), (status, status))
                self.assertEqual(values(point.h1), (2, 0))
                self.assertEqual(values(point.h2), (F(5, 2), 0))
                self.assertIs(point.spectra, self.source)

    def test_cross_floor_applies_to_h2_only_and_accepts_equality(self):
        paired = input_noise()
        cross = abs(paired.bins[4].cross_density_imag)
        self.assertEqual(paired.bins[4].cross_density_real, 0)
        equal = analyze_transfer_response(paired, quality=TransferQuality(cross_density_floor=cross)).bins[4]
        below = analyze_transfer_response(paired, quality=TransferQuality(cross_density_floor=2*cross)).bins[4]
        self.assertEqual(equal.h2_status, "qualified")
        self.assertEqual(below.h1_status, "qualified")
        self.assertEqual(below.h2_status, "weak_cross")
        self.assertEqual(below.h2, equal.h2)

    def test_one_energized_pair_can_have_unity_coherence(self):
        x = pulse(32, (2, .25)) + (0,) * 32
        paired = analysis(x, x, 32)
        report = analyze_transfer_response(paired)
        point = report.bins[3]
        self.assertFalse(report.warming_up)
        self.assertEqual(report.paired.segment_count, 2)
        self.assertEqual(point.spectra.energized_pairs, 1)
        self.assertEqual(point.spectra.magnitude_squared_coherence, 1)
        self.assertEqual(values(point.h1), (1, 0))
        self.assertEqual(point.h1_status, "insufficient_energized_pairs")
        override = analyze_transfer_response(paired, quality=TransferQuality(minimum_energized_pairs=1))
        self.assertEqual(override.bins[3].h1_status, "qualified")

    def test_zero_or_one_complete_segment_is_warmup(self):
        for length, count in ((16, 0), (32, 1)):
            with self.subTest(length=length):
                x = pulse(length, (2, .25))
                report = analyze_transfer_response(analysis(x, x, 32))
                self.assertTrue(report.warming_up)
                self.assertEqual(report.paired.segment_count, count)
                self.assertEqual(report.bins, ())

    def test_invalid_quality_parameters(self):
        for kwargs in (
            {"minimum_coherence": F(11, 10)}, {"reference_density_floor": -1},
            {"measurement_density_floor": math.nan}, {"cross_density_floor": -1},
            {"cross_density_floor": math.inf}, {"minimum_energized_pairs": True},
            {"minimum_energized_pairs": 0}, {"minimum_energized_pairs": 1.5},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                TransferQuality(**kwargs)

    def test_rejects_nonpaired_input_and_invalid_units(self):
        with self.assertRaisesRegex(ValueError, "paired Welch"):
            analyze_transfer_response(self.source)
        for units in ("", " ", 30):
            with self.subTest(units=units), self.assertRaisesRegex(ValueError, "units"):
                analyze_transfer_response(self.paired, reference_units=units)
        with self.assertRaisesRegex(ValueError, "output advance"):
            analyze_transfer_response(self.paired, output_advance_samples=math.nan)


class TransferTimingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.x = pulse(256, (32, 1)) * 2
        cls.y = pulse(256, (39, .25)) * 2
        cls.paired = analysis(cls.x+(0,)*17, cls.y+(0,)*17, 256)
        cls.report = analyze_transfer_response(cls.paired)

    def test_known_transfer_over_all_nonnegative_bins(self):
        for point in self.report.bins:
            angle = -math.tau * 7 * point.spectra.index / 256
            expected = .25 * complex(math.cos(angle), math.sin(angle))
            actual = complex(float(point.h1.real), float(point.h1.imag))
            self.assertLess(abs(actual-expected), 2e-15)
            self.assertEqual(point.h1, point.h2)
            self.assertEqual(point.spectra.magnitude_squared_coherence, 1)
        self.assertLess(self.report.bins[1].spectra.phase_radians, 0)

    def test_preserves_large_origin_complete_support_and_unused_tail(self):
        self.assertEqual(self.paired.segment_starts, (ORIGIN, ORIGIN+256))
        self.assertEqual(self.paired.used_end_sample_exclusive, ORIGIN+512)
        self.assertEqual(self.paired.end_sample_exclusive, ORIGIN+529)
        self.assertEqual(len(self.report.bins), 129)
        self.assertEqual(self.report.bins[1].spectra.frequency_hz, RATE/256)

    def test_group_delay_uses_the_qualified_complex_response(self):
        delay = measure_delay(self.report, 8)
        self.assertEqual(len(delay.points), 128)
        for p in delay.points:
            self.assertEqual(p.status, "valid")
            self.assertAlmostEqual(float(p.delay_samples), 7, places=12)
            self.assertAlmostEqual(float(p.delay_seconds), 7/48000, places=14)

    def test_output_advance_and_original_tap_provenance(self):
        shifted = pulse(256, (36, .25)) * 2
        paired = analysis(self.x, shifted, 256)
        provenance = TransferProvenance(
            "input", "output", EPOCH.clock_domain, EPOCH.epoch_id,
            (ORIGIN, ORIGIN+512), (ORIGIN+3, ORIGIN+515),
        )
        report = analyze_transfer_response(paired, provenance=provenance, output_advance_samples=3,
                                           reference_units="V", measurement_units="Pa")
        self.assertIs(report.provenance, provenance)
        self.assertEqual((report.reference_units, report.measurement_units), ("V", "Pa"))
        self.assertEqual(report.output_advance_samples, F(3))
        delay = measure_delay(report, 5)
        self.assertIs(delay.provenance, provenance)
        for p in delay.points:
            self.assertAlmostEqual(float(p.residual_delay_samples), 4, places=12)
            self.assertAlmostEqual(float(p.delay_samples), 7, places=12)

    def test_preserves_exact_rate_and_a_signed_fractional_advance(self):
        epoch = replace(EPOCH, rate_hz=F(48_000_000, 1001))
        x = pulse(8, (0, 1)) * 2
        report = analyze_transfer_response(analysis(x, x, 8, epoch=epoch), output_advance_samples=F(-1, 3))
        self.assertEqual(report.bins[1].spectra.frequency_hz, epoch.rate_hz/8)
        self.assertEqual(report.output_advance_samples, F(-1, 3))

    def test_provenance_must_use_the_same_clock_and_epoch(self):
        provenance = TransferProvenance("in", "out", "other-clock", EPOCH.epoch_id,
                                        (ORIGIN, ORIGIN+10), (ORIGIN, ORIGIN+10))
        with self.assertRaisesRegex(ValueError, "clock domain and epoch"):
            analyze_transfer_response(self.paired, provenance=provenance)


class TransferRangeTests(unittest.TestCase):
    def test_keeps_finite_db_for_gains_outside_binary64_magnitude_range(self):
        smallest, largest = math.ulp(0.0), sys.float_info.max
        for a,b,db in ((smallest,largest,12631.21861806065), (largest,smallest,-12631.21861806065)):
            with self.subTest(dB=db):
                x, y = (pulse(8, (0, level))*2 for level in (a,b))
                point = analyze_transfer_response(analysis(x, y, 8)).bins[0]
                self.assertEqual(values(point.h1), (F(b)/F(a), 0))
                self.assertEqual(point.h1, point.h2)
                self.assertIsNone(point.h1.magnitude)
                self.assertEqual(point.h1_status, "qualified")
                self.assertAlmostEqual(point.h1.magnitude_db, db, places=9)

    def test_linear_magnitude_handles_both_finite_range_boundaries(self):
        x = pulse(8, (0, 1)) * 2
        for edge in (math.ulp(0.0), sys.float_info.max):
            with self.subTest(magnitude=edge):
                y = pulse(8, (0, edge)) * 2
                point = analyze_transfer_response(analysis(x, y, 8)).bins[0]
                self.assertEqual(values(point.h1), (F(edge), 0))
                self.assertEqual(point.h1.magnitude, edge)


if __name__ == "__main__":
    unittest.main()
