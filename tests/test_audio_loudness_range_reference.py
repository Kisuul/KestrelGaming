"""Check LRA arithmetic, PCM timing and the official checker independently."""
from contextlib import redirect_stderr, redirect_stdout
from decimal import Decimal, localcontext, ROUND_HALF_UP
from fractions import Fraction
import hashlib
import io
import math
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       "skills/audio-loudness-range/scripts"))

import check_ebu_lra as checker
import check_ebu_loudness as archive_reader
from reference_loudness_range import LoudnessConfig, LoudnessRangeStream, calculate_lra
from reference_program_loudness import ProgramLoudnessStream


def decimal_oracle(levels, precision):
    """Use unscaled powers and independently rounded ranks for bounded vectors."""
    with localcontext() as context:
        context.prec = precision
        absolute = [Decimal.from_float(level) for level in levels if level >= -70.0]
        ten = Decimal(10)
        powers = [ten ** (level / ten) for level in absolute]
        threshold = sum(powers) / len(absolute) / 100
        retained = sorted(level for level, power in zip(absolute, powers) if power >= threshold)
        count = len(retained)
        low = (Decimal("0.10") * (count - 1)).to_integral_value(rounding=ROUND_HALF_UP)
        high = (Decimal("0.95") * (count - 1)).to_integral_value(rounding=ROUND_HALF_UP)
        return len(absolute), count, float(retained[int(low)]), float(retained[int(high)])


class LoudnessRangeMathTests(unittest.TestCase):
    def assert_distribution(self, result, absolute, final, low, high):
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.absolute_survivor_count, absolute)
        self.assertEqual(result.final_survivor_count, final)
        self.assertEqual(result.p10_lufs, low)
        self.assertEqual(result.p95_lufs, high)
        self.assertEqual(result.lra_lu, high - low)

    def test_undefined_results_preserve_reason_and_window_count(self):
        for levels, status in (
            ([], "insufficient_data"),
            ([-math.inf] * 3, "silence"),
            ([-71.0, -math.inf], "below_absolute_gate"),
        ):
            with self.subTest(status=status):
                result = calculate_lra(levels)
                self.assertEqual(result.status, status)
                self.assertEqual(result.window_count, len(levels))
                self.assertEqual(result.absolute_survivor_count, 0)
                self.assertEqual(result.final_survivor_count, 0)
                for value in (result.p10_lufs, result.p95_lufs,
                              result.lra_lu, result.relative_gate_lufs):
                    self.assertIsNone(value)

    def test_exact_absolute_gate_and_adjacent_binary64_values(self):
        below = math.nextafter(-70.0, -math.inf)
        above = math.nextafter(-70.0, math.inf)
        self.assert_distribution(calculate_lra([below, -70.0, above]), 2, 2, -70.0, above)

    def test_relative_equality_with_integer_powers(self):
        powers = [1] * 10 + [10] * 9 + [1000] * 2
        self.assertEqual(Fraction(sum(powers), len(powers)), 100)
        self.assert_distribution(calculate_lra([0.0] * 10 + [10.0] * 9 + [30.0] * 2),
                                 21, 21, 0.0, 30.0)

    def test_relative_equality_with_negative_power_exponents(self):
        # These decimal powers are exact rationals. The -10 readings still fail.
        powers = [Fraction("0.1")] * 10 + [1] * 9 + [10] * 9 + [1000] * 3
        self.assertEqual(sum(powers) / len(powers), 100)
        levels = [-10.0] * 10 + [0.0] * 9 + [10.0] * 9 + [30.0] * 3
        self.assert_distribution(calculate_lra(levels), 31, 21, 0.0, 30.0)

    def test_relative_boundary_neighbors_at_normal_and_subnormal_values(self):
        for origin in (-40.0, 0.0):
            for direction, final in ((-math.inf, 11), (math.inf, 21)):
                with self.subTest(origin=origin, direction=direction):
                    neighbor = math.nextafter(origin, direction)
                    levels = [neighbor] * 10 + [origin + 10] * 9 + [origin + 30] * 2
                    low = origin + 10 if final == 11 else neighbor
                    expected = (21, final, low, origin + 30)
                    self.assertEqual(decimal_oracle(levels, 420), expected)
                    self.assertEqual(decimal_oracle(levels, 480), expected)
                    self.assert_distribution(calculate_lra(levels), *expected)

    def test_percentile_low_half_tie_rounds_up_without_interpolation(self):
        self.assert_distribution(calculate_lra([-26, -23, -25, -22, -24, -21]),
                                 6, 6, -25.0, -21.0)

    def test_percentile_high_half_tie_rounds_up_without_interpolation(self):
        levels = [-40 + index / 4 for index in range(31)]
        self.assert_distribution(calculate_lra(levels), 31, 31, -39.25, -32.75)

    def test_one_loud_event_and_duplicate_percentiles(self):
        self.assert_distribution(calculate_lra([-20.0] * 100 + [-10.0]),
                                 101, 101, -20.0, -20.0)

    def test_constant_and_single_window_produce_defined_zero(self):
        for levels in ([-23.0], [-23.0] * 20, [0.0, -0.0, 0.0, -0.0]):
            with self.subTest(count=len(levels)):
                result = calculate_lra(levels)
                self.assert_distribution(result, len(levels), len(levels), levels[0], levels[0])
                self.assertEqual(math.copysign(1.0, result.lra_lu), 1.0)

    def test_gain_shift_preserves_range_when_absolute_membership_is_unchanged(self):
        levels = [-64.0] + [-27.0] * 6 + [-15.0] * 8
        original = calculate_lra(levels)
        shifted = calculate_lra([level + 6.0 for level in levels])
        self.assertEqual(original.absolute_survivor_count, shifted.absolute_survivor_count)
        self.assertEqual(original.final_survivor_count, shifted.final_survivor_count)
        self.assertEqual(original.lra_lu, shifted.lra_lu)
        self.assertAlmostEqual(shifted.relative_gate_lufs - original.relative_gate_lufs, 6.0)
        self.assertEqual(shifted.p10_lufs - original.p10_lufs, 6.0)
        self.assertEqual(shifted.p95_lufs - original.p95_lufs, 6.0)

    def test_new_readings_can_gate_out_previously_admitted_values(self):
        quiet = [-50.0] * 10
        self.assert_distribution(calculate_lra(quiet), 10, 10, -50.0, -50.0)
        self.assert_distribution(calculate_lra(quiet + [-15.0] * 100), 110, 100, -15.0, -15.0)

    def test_large_level_stays_finite_without_materializing_absolute_powers(self):
        level = sys.float_info.max
        self.assert_distribution(calculate_lra([level, -70.0]), 2, 1, level, level)

    def test_small_power_can_break_an_apparent_relative_tie(self):
        # The 22 tall readings have normalized power 3100 at 6000 LUFS.
        # 9 additional positive powers make the sum strictly exceed 100 * 31.
        levels = [-70.0] * 9 + [6000.0] * 10 + [6010.0] * 9 + [6030.0] * 3
        self.assert_distribution(calculate_lra(levels), 31, 12, 6010.0, 6030.0)

    def test_unresolved_precision_limit_does_not_guess_gate_membership(self):
        levels = [-69.5] * 9 + [12000.0] * 10 + [12010.0] * 9 + [12030.0] * 3
        with self.assertRaisesRegex(ArithmeticError, "relative gate could not be resolved"):
            calculate_lra(levels)

    def test_seeded_histories_match_independent_decimal_oracle(self):
        rng = random.Random(3342)
        for case in range(100):
            levels = [-30.0, -math.inf] + [rng.uniform(-85, -10) for _ in range(rng.randrange(1, 60))]
            with self.subTest(case=case):
                self.assert_distribution(calculate_lra(levels), *decimal_oracle(levels, 80))

    def test_invalid_history_fails_even_when_an_earlier_value_was_valid(self):
        for levels in (None, "", b"LUFS", {-20: 1}, [-23.0, True], [-23.0, "−24"],
                       [math.nan], [math.inf], [10 ** 400]):
            with self.subTest(level_type=type(levels)):
                with self.assertRaises(ValueError):
                    calculate_lra(levels)


class LoudnessRangeStreamTests(unittest.TestCase):
    def setUp(self):
        self.config = LoudnessConfig(48_000, ("MONO",), "post-gain", readout_hop_samples=960)
        self.origin = 2 ** 53 + 17

    def meter(self):
        return LoudnessRangeStream(self.config, epoch_id="original", start_sample=self.origin)

    def test_partition_invariance_and_clock_beyond_binary64_integer_precision(self):
        cycle = [0.05 * math.sin(math.tau * index / 48) for index in range(48)]
        audio = cycle * 2500 + [value / 2 for value in cycle] * 750
        one, split = self.meter(), self.meter()
        expected = one.push(self.origin, [audio], epoch_id="original")
        actual = []
        bounds = [0, 17, 2222, 141_010, 145_331, len(audio)]
        for start, end in zip(bounds, bounds[1:]):
            actual.extend(split.push(self.origin + start, [audio[start:end]], epoch_id="original"))
        self.assertEqual(tuple(actual), expected)
        self.assertEqual([window.end_sample_exclusive - self.origin for window in expected],
                         [144_000, 148_800, 153_600])
        self.assertEqual([window.start_sample - self.origin for window in expected],
                         [0, 4800, 9600])
        self.assertEqual(one.finish(), split.finish())
        report = one.measure()
        self.assertEqual(report.config.readout_hop_samples, 4800)
        self.assertEqual(report.config.channel_labels, ("MONO",))
        self.assertEqual(report.config.source_tap, "post-gain")
        self.assertEqual(report.epoch_id, "original")
        self.assertTrue(report.provisional)
        self.assertEqual(report.result.status, "ok")

    def test_finish_padding_matches_explicit_contiguous_short_term_input(self):
        adapter = self.meter()
        upstream = ProgramLoudnessStream(
            LoudnessConfig(48_000, ("MONO",), "post-gain", readout_hop_samples=4800),
            epoch_id="explicit", start_sample=self.origin,
        )
        samples = [0.1, 0.0, -0.1, 0.0] * 36_001
        adapter.push(self.origin, [samples], epoch_id="original")
        report = adapter.finish()
        expected = upstream.push(
            self.origin, [samples + [0.0] * 72_000], epoch_id="explicit",
        )["short_term"]
        self.assertEqual(report.result, calculate_lra([window.lufs for window in expected]))
        self.assertEqual(report.result.window_count, 16)
        self.assertEqual(report.programme_end_sample_exclusive, self.origin + 144_004)
        self.assertEqual(report.analysis_end_sample_exclusive, self.origin + 216_004)
        self.assertEqual(report.last_window_end_sample_exclusive, self.origin + 216_000)
        self.assertTrue(report.finalized)
        self.assertEqual(adapter.finish(), report)
        with self.assertRaisesRegex(ValueError, "measurement is finalized"):
            adapter.push(adapter.next_sample, [[0.0]], epoch_id="original")

    def test_short_file_observation_can_complete_during_padding(self):
        for frames, status, windows in ((71_999, "insufficient_data", 0), (72_000, "silence", 1)):
            with self.subTest(source_frames=frames):
                meter = self.meter()
                meter.push(self.origin, [[0.0] * frames], epoch_id="original")
                self.assertEqual(meter.measure().result.status, "insufficient_data")
                padded = meter.finish()
                self.assertEqual(padded.result.status, status)
                self.assertEqual(padded.result.window_count, windows)
                self.assertTrue(padded.provisional)

    def test_empty_file_has_no_padding_or_observation(self):
        report = self.meter().finish()
        self.assertTrue(report.finalized)
        self.assertEqual(report.programme_end_sample_exclusive, self.origin)
        self.assertEqual(report.analysis_end_sample_exclusive, self.origin)
        self.assertIsNone(report.last_window_end_sample_exclusive)
        self.assertEqual(report.result.status, "insufficient_data")

    def test_60_second_indication_uses_actual_source_frames(self):
        for source_frames, provisional in ((2_879_999, True), (2_880_000, False)):
            with self.subTest(source_frames=source_frames):
                meter = self.meter()
                zeros = [0.0] * 48_000
                for offset in range(0, source_frames, len(zeros)):
                    meter.push(meter.next_sample, [zeros[:source_frames - offset]], epoch_id="original")
                self.assertEqual(meter.measure().provisional, provisional)
                self.assertEqual(meter.finish().provisional, provisional)

    def test_rejected_push_and_reset_leave_prior_state_intact(self):
        meter = self.meter()
        meter.push(self.origin, [[0.0] * 144_000], epoch_id="original")
        prior = meter.measure()
        for offset, epoch, tail in ((1, "original", 0.0), (0, "new", 0.0),
                                    (0, "original", math.nan)):
            with self.subTest(offset=offset, epoch=epoch, tail=tail):
                with self.assertRaises(ValueError):
                    meter.push(meter.next_sample + offset, [[0.0] * 4800 + [tail]], epoch_id=epoch)
                self.assertEqual(meter.measure(), prior)
        with self.assertRaises(ValueError):
            meter.reset_epoch("original", 0)
        self.assertEqual(meter.measure(), prior)
        complete = meter.push(meter.next_sample, [[0.0] * 4800], epoch_id="original")
        self.assertEqual(len(complete), 1)

    def test_reset_after_eof_clears_history_and_preserves_new_tap(self):
        meter = self.meter()
        meter.push(self.origin, [[0.0] * 144_000], epoch_id="original")
        meter.finish()
        meter.reset_epoch("new", 101, LoudnessConfig(48_000, ("L", "R"), "premix"))
        report = meter.measure()
        self.assertEqual(report.result.status, "insufficient_data")
        self.assertEqual(report.config.source_tap, "premix")
        self.assertEqual(report.config.channel_labels, ("L", "R"))
        self.assertEqual(report.epoch_id, "new")
        self.assertEqual(report.start_sample, 101)
        self.assertFalse(report.finalized)
        self.assertTrue(report.provisional)
        meter.push(101, [[0.0], [0.0]], epoch_id="new")
        self.assertEqual(meter.next_sample, 102)


class LoudnessRangeFixtureTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.archive_path = Path(temp.name) / "synthetic.zip"

    def write_archive(self, *, omit=None):
        with zipfile.ZipFile(self.archive_path, "w") as archive:
            for name, _ in checker._CASES:
                if name != omit:
                    archive.writestr(name, b"synthetic, no audio")
        return hashlib.sha256(self.archive_path.read_bytes()).hexdigest()

    def test_wrong_hash_never_parses_or_measures(self):
        read_hash = self.write_archive()
        output, errors = io.StringIO(), io.StringIO()
        with (patch.object(archive_reader.zipfile, "ZipFile") as zip_open,
              patch.object(checker, "_measure") as measure,
              redirect_stdout(output), redirect_stderr(errors)):
            self.assertEqual(checker.main([str(self.archive_path)]), 2)
        zip_open.assert_not_called()
        measure.assert_not_called()
        self.assertIn(read_hash, output.getvalue())
        self.assertIn("SHA-256 mismatch", errors.getvalue())

    def test_required_entries_checked_after_matching_digest(self):
        name = checker._CASES[-1][0]
        test_hash = self.write_archive(omit=name)
        errors = io.StringIO()
        with (patch.object(archive_reader, "_OFFICIAL_SHA256", test_hash),
              patch.object(checker, "_measure") as measure,
              redirect_stdout(io.StringIO()), redirect_stderr(errors)):
            self.assertEqual(checker.main([str(self.archive_path)]), 2)
        measure.assert_not_called()
        self.assertIn(f"missing fixture entry: {name}", errors.getvalue())

    def test_six_cases_are_checked_once_and_repeated_with_inclusive_tolerance(self):
        test_hash = self.write_archive()
        targets = dict(checker._CASES)
        output = io.StringIO()
        with (patch.object(archive_reader, "_OFFICIAL_SHA256", test_hash),
              patch.object(checker, "_measure",
                           side_effect=lambda archive, name, copies: targets[name] + 1) as measure,
              redirect_stdout(output)):
            self.assertEqual(checker.main([str(self.archive_path)]), 0)
        expected = [(name, copies) for name, _ in checker._CASES for copies in (1, 2)]
        self.assertEqual([call.args[1:] for call in measure.call_args_list], expected)
        self.assertIn("12/12 measurements passed", output.getvalue())


if __name__ == "__main__":
    unittest.main()
