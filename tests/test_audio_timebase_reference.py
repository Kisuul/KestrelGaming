"""Independent rational, epoch, gap, and clock-domain acceptance fixtures."""
from fractions import Fraction
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-timebase-sync/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-dsp-test-fixtures/scripts"))

from reference_timebase import (
    SampleRate, SampleTimeline, DiscontinuityError, ExternalClockAnchor,
    sample_count_to_seconds, convert_rate_offset, estimate_external_time
)
from fixture_bank import make_fixture, partition_contiguous


class AudioTimebaseTests(unittest.TestCase):
    def test_duration_is_not_first_to_last_sample_span(self):
        rate = SampleRate(48000)
        self.assertEqual(sample_count_to_seconds(1000, rate), Fraction(1, 48))
        self.assertEqual(sample_count_to_seconds(999, rate), Fraction(999, 48000))
        self.assertNotEqual(sample_count_to_seconds(1000, rate),
                            sample_count_to_seconds(999, rate))

    def test_four_frame_even_center_is_exact_at_large_origin(self):
        origin = 2**54 + 17
        timeline = SampleTimeline("epoch-a", origin, SampleRate(48000), 2)
        frame = timeline.ingest(origin, 4, 2)
        self.assertEqual(frame.center_sample_twice, 2*origin + 3)
        self.assertEqual(frame.start_seconds, Fraction(0))
        self.assertEqual(frame.duration_seconds, Fraction(1, 12000))
        self.assertEqual(frame.center_seconds, Fraction(3, 96000))
        self.assertEqual(frame.end_seconds_exclusive, Fraction(1, 12000))
        self.assertNotEqual(frame.center_sample_twice, 2*origin + 4)

    def test_odd_center_is_exact_integer_coordinate(self):
        timeline = SampleTimeline("epoch-o", 40, SampleRate(44100), 1)
        frame = timeline.ingest(40, 5, 1)
        self.assertEqual(frame.center_sample_twice, 84)
        self.assertEqual(frame.center_seconds, Fraction(2, 44100))
        self.assertEqual(frame.end_sample_exclusive, 45)

    def test_contiguous_chunk_partitions_give_same_time_and_end(self):
        origin = 2**54 + 7
        fixture = make_fixture("seeded_noise", sample_count=73, origin_sample=origin)
        whole = SampleTimeline("e1", origin, SampleRate(48000), 1)
        expected = whole.ingest(origin, 73, 1)
        for chunks in ([73], [1], [3, 7, 11, 2], [128]):
            t = SampleTimeline("e1", origin, SampleRate(48000), 1)
            for piece in partition_contiguous(fixture["planar_samples"], origin, chunks):
                span = t.ingest(piece["start_sample"], len(piece["planar_samples"][0]), 1)
            self.assertEqual(t.next_sample, expected.end_sample_exclusive)
            self.assertEqual(span.end_seconds_exclusive, expected.end_seconds_exclusive)
            self.assertEqual(t.sample_rate.hz, Fraction(48000))

    def test_gap_is_rejected_without_state_mutation(self):
        t = SampleTimeline("a", 0, SampleRate(48000), 1)
        t.ingest(0, 10, 1)
        with self.assertRaises(DiscontinuityError) as ctx:
            t.ingest(13, 2, 1)
        err = ctx.exception
        self.assertEqual((err.kind, err.delta_samples), ("gap", 3))
        self.assertEqual((err.expected_start, err.observed_start), (10, 13))
        self.assertEqual((t.next_sample, t.accepted_blocks), (10, 1))
        t.ingest(10, 3, 1)
        self.assertEqual(t.next_sample, 13)

    def test_overlap_and_out_of_order_rejected_atomically(self):
        t = SampleTimeline("a", 100, SampleRate(48000), 1)
        t.ingest(100, 10, 1)
        for start, amount in [(108, -2), (100, -10)]:
            with self.subTest(start=start):
                with self.assertRaises(DiscontinuityError) as ctx:
                    t.ingest(start, 2, 1)
                self.assertEqual(ctx.exception.kind, "overlap")
                self.assertEqual(ctx.exception.delta_samples, amount)
                self.assertEqual((t.next_sample, t.accepted_blocks), (110, 1))

    def test_seek_or_gap_requires_new_epoch(self):
        t = SampleTimeline("old", 500, SampleRate(48000), 2)
        t.ingest(500, 12, 2)
        with self.assertRaises(DiscontinuityError):
            t.ingest(900, 4, 2)
        t.reset_epoch("after-seek", 900)
        span = t.ingest(900, 4, 2)
        self.assertEqual(span.epoch_id, "after-seek")
        self.assertEqual(span.start_seconds, 0)
        self.assertEqual(t.next_sample, 904)

    def test_rate_and_channel_changes_are_explicit_new_epochs(self):
        t = SampleTimeline("a", 0, SampleRate(48000), 2)
        t.ingest(0, 100, 2)
        with self.assertRaises(ValueError):
            t.ingest(100, 4, 1)
        self.assertEqual(t.next_sample, 100)
        t.reset_epoch("b", 0, SampleRate(44100), 1)
        span = t.ingest(0, 441, 1)
        self.assertEqual(span.duration_seconds, Fraction(1, 100))
        self.assertEqual(t.channel_count, 1)

    def test_pause_with_no_data_does_not_create_samples(self):
        t = SampleTimeline("a", 0, SampleRate(48000), 1)
        t.ingest(0, 4, 1)
        self.assertEqual(t.next_sample, 4)
        self.assertEqual(t.accepted_blocks, 1)
        # No call to ingest => no assertion about device clock or silence.
        self.assertEqual(t.next_sample, 4)
        t.ingest(4, 4, 1)
        self.assertEqual(t.next_sample, 8)

    def test_resampler_rate_ratio_is_fractional_coordinate(self):
        a = SampleRate(48000)
        b = SampleRate(44100)
        self.assertEqual(convert_rate_offset(1, a, b), Fraction(147, 160))
        self.assertEqual(convert_rate_offset(160, a, b), Fraction(147))
        self.assertEqual(convert_rate_offset(0, a, b), Fraction(0))
        self.assertEqual(convert_rate_offset(441, b, a), Fraction(480))
        self.assertNotIsInstance(convert_rate_offset(1, a, b), float)

    def test_noninteger_rational_rate_is_supported(self):
        rate = SampleRate(48000 * 1000, 1001)
        self.assertEqual(rate.hz, Fraction(48000000, 1001))
        self.assertEqual(sample_count_to_seconds(48000, rate), Fraction(1001, 1000))

    def test_external_clock_anchor_has_explicit_domain(self):
        anchor = ExternalClockAnchor("e", 1000, "dac-output", "playback", Fraction(2))
        mapped = estimate_external_time(1480, "e", SampleRate(48000),
                                        anchor, expected_domain="dac-output")
        self.assertEqual(mapped, Fraction(201, 100))
        self.assertEqual(estimate_external_time(520, "e", SampleRate(48000),
                                                anchor, expected_domain="dac-output"),
                         Fraction(199, 100))

    def test_external_clock_epoch_or_domain_mismatch_rejected(self):
        anchor = ExternalClockAnchor("e", 1000, "dac-output", "playback", Fraction(2))
        with self.assertRaises(ValueError):
            estimate_external_time(1480, "different", SampleRate(48000),
                                   anchor, expected_domain="dac-output")
        with self.assertRaises(ValueError):
            estimate_external_time(1480, "e", SampleRate(48000),
                                   anchor, expected_domain="callback-clock")

    def test_reset_identifier_cannot_be_reused_or_leave_partial_state(self):
        t = SampleTimeline("a", 0, SampleRate(48000), 1)
        t.ingest(0, 10, 1)
        for args in [("a", 99, None, None), ("b", -1, None, None),
                     ("b", 10, SampleRate(44100), 0)]:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    t.reset_epoch(*args)
        self.assertEqual((t.epoch_id, t.next_sample, t.channel_count), ("a", 10, 1))

    def test_bad_inputs_fail_closed_without_advancing(self):
        invalid_rates = [(0, 1), (48000, 0), (True, 1), (48000, False), (-1, 1)]
        for n, d in invalid_rates:
            with self.subTest(n=n, d=d):
                with self.assertRaises(ValueError):
                    SampleRate(n, d)
        t = SampleTimeline("a", 0, SampleRate(48000), 1)
        for inputs in [(0, 0, 1), (0, True, 1), (-1, 1, 1),
                       (0, 1, 0), (0, 1, 2)]:
            with self.subTest(inputs=inputs):
                with self.assertRaises(ValueError):
                    t.ingest(*inputs)
        self.assertEqual((t.next_sample, t.accepted_blocks), (0, 0))
        with self.assertRaises(ValueError):
            SampleTimeline("", 0, SampleRate(48000), 1)
        with self.assertRaises(ValueError):
            sample_count_to_seconds(-1, SampleRate(48000))
        with self.assertRaises(ValueError):
            convert_rate_offset(1, SampleRate(48000), 48000)
        for kind in ("unlabeled", "", "network"):
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    ExternalClockAnchor("a", 0, "device", kind, Fraction(1))
        with self.assertRaises(ValueError):
            ExternalClockAnchor("a", 0, "device", "capture", 1.0)

    def test_external_clock_anchor_is_nominal_not_latency_claim(self):
        a = ExternalClockAnchor("s", 0, "capture-adc", "capture", Fraction(1, 2))
        b = ExternalClockAnchor("s", 0, "callback", "callback", Fraction(9, 10))
        self.assertNotEqual(estimate_external_time(48000, "s", SampleRate(48000),
                                                   a, "capture-adc"),
                            estimate_external_time(48000, "s", SampleRate(48000),
                                                   b, "callback"))


if __name__ == "__main__":
    unittest.main()
