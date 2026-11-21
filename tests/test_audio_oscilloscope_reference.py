"""Sample-clock capture and pixel ownership fixtures for the offline scope."""

from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-oscilloscope/scripts"))
from reference_oscilloscope import (
    CaptureWindow,
    ChannelExtrema,
    MAX_BLOCK_FRAMES,
    MAX_CHANNELS,
    MAX_HISTORY_FRAMES,
    MAX_SAMPLE_INDEX,
    ScopeAcquisition,
    ScopeEpoch,
    ScopePoint,
    project_waveform,
)


STEREO = ScopeEpoch("first", 100, Fraction(48_000), "decode", "pre-gain", "FS", ("L", "R"))
MONO = replace(STEREO, channel_ids=("M",))


def ingest(scope, start, planes):
    return scope.ingest(epoch=scope.epoch, start_sample=start, planes=planes)


def spans(captures):
    return [(item.start_sample, item.end_sample_exclusive, item.planes) for item in captures]


class AcquisitionTests(unittest.TestCase):
    def test_startup_waits_for_complete_aligned_window(self):
        scope = ScopeAcquisition(STEREO, window_frames=4, hop_frames=2, history_frames=4)
        self.assertEqual(ingest(scope, 100, [[1, 2, 3], [11, 12, 13]]), ())
        self.assertEqual((scope.next_sample, scope.next_capture_end), (103, 104))
        (frame,) = ingest(scope, 103, [[4], [14]])
        self.assertEqual(spans((frame,)), [(100, 104, ((1, 2, 3, 4), (11, 12, 13, 14)))])
        self.assertEqual(frame.center_sample_twice, 203)
        self.assertEqual(frame.frame_count, 4)
        self.assertEqual(frame.epoch, STEREO)

    def test_block_larger_than_history_returns_every_due_window(self):
        scope = ScopeAcquisition(STEREO, window_frames=4, hop_frames=2, history_frames=4)
        left = tuple(range(9))
        right = tuple(-x for x in left)
        actual = ingest(scope, 100, (left, right))
        self.assertEqual(spans(actual), [
            (100, 104, ((0, 1, 2, 3), (0, -1, -2, -3))),
            (102, 106, ((2, 3, 4, 5), (-2, -3, -4, -5))),
            (104, 108, ((4, 5, 6, 7), (-4, -5, -6, -7))),
        ])
        self.assertEqual((scope.next_sample, scope.next_capture_end), (109, 110))

    def test_nonoverlapping_adjacent_windows(self):
        scope = ScopeAcquisition(MONO, window_frames=3, hop_frames=3, history_frames=5)
        actual = ingest(scope, 100, [list(range(8))])
        self.assertEqual(spans(actual), [(100, 103, ((0, 1, 2),)), (103, 106, ((3, 4, 5),))])

    def test_hop_can_exceed_retained_history(self):
        scope = ScopeAcquisition(MONO, window_frames=3, hop_frames=7, history_frames=3)
        actual = ingest(scope, 100, [list(range(14))])
        self.assertEqual(spans(actual), [(100, 103, ((0, 1, 2),)), (107, 110, ((7, 8, 9),))])
        self.assertEqual(scope.next_capture_end, 117)

    def test_one_frame_window_at_maximum_block_length(self):
        scope = ScopeAcquisition(MONO, window_frames=1, hop_frames=1, history_frames=1)
        actual = ingest(scope, 100, [list(range(MAX_BLOCK_FRAMES))])
        self.assertEqual(spans(actual), [
            (100 + i, 101 + i, ((i,),)) for i in range(MAX_BLOCK_FRAMES)
        ])

    def test_snapshot_survives_source_edits_and_history_wrap(self):
        scope = ScopeAcquisition(STEREO, window_frames=3, hop_frames=3, history_frames=4)
        source = [[1, 2, 3], [4, 5, 6]]
        (old,) = ingest(scope, 100, source)
        source[0][0] = 99
        source[1].clear()
        ingest(scope, 103, [[0] * 9, [0] * 9])
        self.assertEqual(old.planes, ((1, 2, 3), (4, 5, 6)))
        with self.assertRaises(FrozenInstanceError):
            old.start_sample = 101

    def test_large_origin_and_rational_clock_stay_exact(self):
        origin = 2**53 + 1
        epoch = replace(MONO, origin_sample=origin, rate_hz=Fraction(48_000_000, 1001))
        scope = ScopeAcquisition(epoch, window_frames=4, hop_frames=2, history_frames=5)
        self.assertEqual(ingest(scope, origin, [[1, 2]]), ())
        (frame,) = ingest(scope, origin + 2, [[3, 4]])
        self.assertEqual((frame.start_sample, frame.end_sample_exclusive), (origin, origin + 4))
        self.assertEqual(frame.center_sample_twice, 18014398509481989)
        self.assertEqual(frame.epoch.rate_hz, Fraction(48_000_000, 1001))
        self.assertEqual(float(origin), float(origin - 1))

    def test_maximum_history_and_channel_count(self):
        epoch = replace(STEREO, channel_ids=tuple(f"ch{i}" for i in range(MAX_CHANNELS)))
        scope = ScopeAcquisition(
            epoch, window_frames=MAX_HISTORY_FRAMES, hop_frames=MAX_HISTORY_FRAMES,
            history_frames=MAX_HISTORY_FRAMES,
        )
        stride = MAX_BLOCK_FRAMES
        tape = tuple(tuple(i + 1000 * ch for i in range(MAX_HISTORY_FRAMES)) for ch in range(MAX_CHANNELS))
        for offset in range(0, MAX_HISTORY_FRAMES, stride):
            block = tuple(plane[offset:offset + stride] for plane in tape)
            windows = ingest(scope, epoch.origin_sample + offset, block)
            if offset + len(block[0]) < MAX_HISTORY_FRAMES:
                self.assertEqual(windows, ())
        self.assertEqual(spans(windows), [(100, 100 + MAX_HISTORY_FRAMES, tape)])

    def test_invalid_configuration(self):
        cases = [
            (0, 1, 4), (5, 2, 4), (1, 0, 4), (1, 1.0, 4),
            (1, 1, 0), (1, 1, MAX_HISTORY_FRAMES + 1), (1, True, 4),
        ]
        for length, hop, history in cases:
            with self.subTest(length=length, hop=hop, history=history):
                with self.assertRaises(ValueError):
                    ScopeAcquisition(MONO, window_frames=length, hop_frames=hop, history_frames=history)

    def test_epoch_labels_rate_channels_and_origin_are_validated(self):
        for change in (
            {"epoch_id": ""}, {"clock_domain": ""}, {"tap_id": " "}, {"units": None},
            {"origin_sample": -1}, {"origin_sample": True}, {"origin_sample": MAX_SAMPLE_INDEX + 1},
            {"rate_hz": Fraction(0)}, {"rate_hz": 48_000.0}, {"channel_ids": ("L", "L")},
            {"channel_ids": ()}, {"channel_ids": ["L", "R"]}, {"channel_ids": ("L", " ")},
            {"channel_ids": tuple(str(i) for i in range(MAX_CHANNELS + 1))},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(STEREO, **change)

    def test_invalid_block_is_atomic_even_when_it_would_complete_several_windows(self):
        scope = ScopeAcquisition(STEREO, window_frames=4, hop_frames=2, history_frames=4)
        prefix = [[1, 2, 3], [-1, -2, -3]]
        ingest(scope, 100, prefix)
        valid = [list(range(4, 12)), list(range(-4, -12, -1))]
        invalid = [
            [], [[], []], [valid[0]], [valid[0], valid[1][:-1]],
            [valid[0], object()], [[0] * (MAX_BLOCK_FRAMES + 1)] * 2,
        ]
        invalid.extend(
            [valid[0], valid[1][:-1] + [bad]]
            for bad in (math.nan, math.inf, -math.inf, True, 1j, 2**31, -2**31 - 1)
        )
        for number, block in enumerate(invalid):
            with self.subTest(block=number):
                with self.assertRaises(ValueError):
                    ingest(scope, 103, block)
                self.assertEqual((scope.next_sample, scope.next_capture_end), (103, 104))

        clean = ScopeAcquisition(STEREO, window_frames=4, hop_frames=2, history_frames=4)
        expected = ingest(clean, 100, [prefix[i] + valid[i] for i in range(2)])
        self.assertEqual(len(expected), 4)
        self.assertEqual(ingest(scope, 103, valid), expected)

    def test_gap_and_overlap_report_positions_and_allow_contiguous_retry(self):
        scope = ScopeAcquisition(MONO, window_frames=4, hop_frames=2, history_frames=4)
        ingest(scope, 100, [[1, 2, 3]])
        for kind, observed in (("gap", 104), ("overlap", 102)):
            with self.subTest(kind=kind), self.assertRaisesRegex(
                ValueError, f"{kind}: expected start=103, observed={observed}"
            ):
                ingest(scope, observed, [[9, 8, 7, 6]])
        self.assertEqual((scope.next_sample, scope.next_capture_end), (103, 104))
        (frame,) = ingest(scope, 103, [[4]])
        self.assertEqual(frame.planes, ((1, 2, 3, 4),))

    def test_block_metadata_must_match_even_when_coordinates_match(self):
        scope = ScopeAcquisition(STEREO, window_frames=2, hop_frames=1, history_frames=3)
        ingest(scope, 100, [[1], [-1]])
        for change in (
            {"epoch_id": "wrong"}, {"origin_sample": 101}, {"rate_hz": Fraction(44_100)},
            {"clock_domain": "output"}, {"tap_id": "post-gain"}, {"units": "volts"},
            {"channel_ids": ("R", "L")},
        ):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "active epoch"):
                scope.ingest(epoch=replace(STEREO, **change), start_sample=101, planes=[[8], [9]])
        self.assertEqual((scope.next_sample, scope.next_capture_end), (101, 102))
        (frame,) = ingest(scope, 101, [[2], [-2]])
        self.assertEqual(frame.planes, ((1, 2), (-1, -2)))

    def test_reset_discards_partial_history_and_changes_layout(self):
        scope = ScopeAcquisition(STEREO, window_frames=2, hop_frames=2, history_frames=3)
        (old,) = ingest(scope, 100, [[1, 2, 3], [4, 5, 6]])
        new = replace(MONO, epoch_id="seek", origin_sample=7, rate_hz=Fraction(44_100), tap_id="post-gain")
        scope.reset_epoch(new)
        self.assertEqual((scope.epoch, scope.next_sample, scope.next_capture_end), (new, 7, 9))
        self.assertEqual(ingest(scope, 7, [[7]]), ())
        (capture,) = ingest(scope, 8, [[8]])
        self.assertEqual(spans((capture,)), [(7, 9, ((7, 8),))])
        self.assertEqual(capture.epoch, new)
        self.assertEqual(old.epoch, STEREO)
        self.assertEqual(old.planes, ((1, 2), (4, 5)))

    def test_reset_rejects_stale_blocks_and_reused_ids(self):
        scope = ScopeAcquisition(MONO, window_frames=3, hop_frames=2, history_frames=3)
        scope.reset_epoch(replace(MONO, epoch_id="second"))
        with self.assertRaisesRegex(ValueError, "active epoch"):
            scope.ingest(epoch=MONO, start_sample=100, planes=[[9, 9, 9]])
        ingest(scope, 100, [[1, 2]])
        with self.assertRaisesRegex(ValueError, "already been used"):
            scope.reset_epoch(replace(MONO, origin_sample=0))
        (frame,) = ingest(scope, 102, [[3]])
        self.assertEqual(frame.planes, ((1, 2, 3),))
        self.assertEqual(frame.epoch.epoch_id, "second")

    def test_invalid_reset_does_not_reserve_new_epoch_id_or_discard_history(self):
        scope = ScopeAcquisition(MONO, window_frames=2, hop_frames=2, history_frames=2)
        ingest(scope, 100, [[1]])
        new = replace(MONO, epoch_id="later", origin_sample=MAX_SAMPLE_INDEX)
        with self.assertRaisesRegex(ValueError, "first capture exclusive end"):
            scope.reset_epoch(new)
        (frame,) = ingest(scope, 101, [[2]])
        self.assertEqual(frame.planes, ((1, 2),))
        scope.reset_epoch(replace(new, origin_sample=7))
        self.assertEqual(scope.next_sample, 7)

    def test_exclusive_end_bound_is_checked_before_ingest(self):
        origin = MAX_SAMPLE_INDEX - 4
        scope = ScopeAcquisition(
            replace(MONO, origin_sample=origin), window_frames=4, hop_frames=2, history_frames=4
        )
        ingest(scope, origin, [[1, 2, 3]])
        with self.assertRaisesRegex(ValueError, "block exclusive end"):
            ingest(scope, origin + 3, [[9, 8]])
        self.assertEqual(scope.next_sample, origin + 3)
        (frame,) = ingest(scope, origin + 3, [[4]])
        self.assertEqual(frame.end_sample_exclusive, MAX_SAMPLE_INDEX)
        self.assertEqual(frame.planes, ((1, 2, 3, 4),))


class ProjectionTests(unittest.TestCase):
    def test_two_off_stride_impulses_survive_in_the_same_bucket(self):
        epoch = replace(MONO, origin_sample=0)
        scope = ScopeAcquisition(epoch, window_frames=256, hop_frames=256, history_frames=256)
        plane = [0.0] * 256
        plane[119], plane[123] = 1.0, -0.75
        (capture,) = ingest(scope, 0, [plane])
        projection = project_waveform(capture, width=16)
        bucket = projection.buckets[7]
        self.assertEqual(projection.mode, "min_max")
        self.assertEqual((bucket.start_sample, bucket.end_sample_exclusive), (112, 128))
        self.assertEqual(bucket.extrema, (ChannelExtrema(-0.75, 1.0, 123, 119),))
        self.assertEqual(plane[::16], [0.0] * 16)

    def test_nondivisible_partition_uses_exact_edges_and_includes_endpoints(self):
        frame = CaptureWindow(MONO, 100, ((10, 0, 0, -6, 0, 0, 0, 4, 0, 0, 12),))
        result = project_waveform(frame, width=3)
        self.assertEqual([(b.start_sample, b.end_sample_exclusive) for b in result.buckets],
                         [(100, 103), (103, 107), (107, 111)])
        self.assertEqual([b.extrema[0] for b in result.buckets], [
            ChannelExtrema(0, 10, 101, 100),
            ChannelExtrema(-6, 0, 103, 104),
            ChannelExtrema(0, 12, 108, 110),
        ])

    def test_ties_prefer_the_first_measured_sample(self):
        frame = CaptureWindow(MONO, 100, ((-1.0, 2.0, -1.0, 2.0),))
        (bucket,) = project_waveform(frame, width=1).buckets
        self.assertEqual(bucket.extrema, (ChannelExtrema(-1.0, 2.0, 100, 101),))

    def test_signed_zero_uses_the_first_sample_value(self):
        frame = CaptureWindow(MONO, 100, ((-0.0, 0.0),))
        (bucket,) = project_waveform(frame, width=1).buckets
        (extrema,) = bucket.extrema
        self.assertEqual((extrema.minimum_sample, extrema.maximum_sample), (100, 100))
        self.assertEqual(math.copysign(1.0, extrema.minimum), -1.0)
        self.assertEqual(math.copysign(1.0, extrema.maximum), -1.0)

    def test_singleton_buckets_and_wide_view_use_measured_values(self):
        start = 2**53 + 1
        frame = CaptureWindow(STEREO, start, ((5, 7, 1), (-3, -2, -8)))
        full = project_waveform(frame, width=3)
        self.assertEqual(full.points, ())
        self.assertEqual([b.extrema[0] for b in full.buckets], [
            ChannelExtrema(5, 5, start, start), ChannelExtrema(7, 7, start + 1, start + 1),
            ChannelExtrema(1, 1, start + 2, start + 2),
        ])
        wide = project_waveform(frame, width=4)
        self.assertEqual((wide.mode, wide.width, wide.buckets), ("points", 4, ()))
        self.assertEqual((wide.epoch, wide.start_sample, wide.end_sample_exclusive),
                         (STEREO, start, start + 3))
        self.assertEqual(wide.points, (
            ScopePoint(start, (5, -3)), ScopePoint(start + 1, (7, -2)), ScopePoint(start + 2, (1, -8))
        ))

    def test_different_raw_traces_can_have_identical_bucket_results(self):
        a = CaptureWindow(MONO, 100, ((-1, 0.25, 0.75, 1),))
        b = CaptureWindow(MONO, 100, ((-1, 0.75, 0.25, 1),))
        self.assertNotEqual(a, b)
        self.assertEqual(project_waveform(a, width=1), project_waveform(b, width=1))

    def test_antiphase_and_over_full_scale_are_preserved_per_channel(self):
        left = (0.75, 0.0, 1.25, -1.5)
        right = tuple(-value for value in left)
        scope = ScopeAcquisition(STEREO, window_frames=4, hop_frames=4, history_frames=4)
        (frame,) = ingest(scope, 100, (left, right))
        projected = project_waveform(frame, width=1)
        self.assertEqual(frame.planes, (left, right))
        self.assertEqual(projected.epoch.channel_ids, ("L", "R"))
        self.assertEqual(projected.buckets[0].extrema, (
            ChannelExtrema(-1.5, 1.25, 103, 102), ChannelExtrema(-1.25, 1.5, 102, 103)
        ))
        self.assertEqual(tuple((a + b) / 2 for a, b in zip(left, right)), (0, 0, 0, 0))

    def test_binary64_and_pcm_extremes_need_no_gain_or_clipping(self):
        tiny = float.fromhex("0x0.0000000000001p-1022")
        maximum = sys.float_info.max
        scope = ScopeAcquisition(STEREO, window_frames=3, hop_frames=3, history_frames=3)
        planes = ((tiny, -maximum, maximum), (-2**31, 0, 2**31 - 1))
        (frame,) = ingest(scope, 100, planes)
        self.assertEqual(frame.planes, planes)
        self.assertEqual(project_waveform(frame, width=1).buckets[0].extrema, (
            ChannelExtrema(-maximum, maximum, 101, 102),
            ChannelExtrema(-2**31, 2**31 - 1, 100, 102),
        ))

    def test_capture_and_width_guards(self):
        for start, planes in (
            (99, ((1,),)), (100, ((),)), (100, ((math.nan,),)),
            (100, (tuple(range(MAX_HISTORY_FRAMES + 1)),)), (MAX_SAMPLE_INDEX, ((1,),)),
        ):
            with self.subTest(start=start, size=len(planes[0])), self.assertRaises(ValueError):
                CaptureWindow(MONO, start, planes)
        frame = CaptureWindow(MONO, 100, ((1,),))
        for width in (0, -1, 2.0, True):
            with self.subTest(width=width), self.assertRaises(ValueError):
                project_waveform(frame, width=width)
        with self.assertRaises(ValueError):
            project_waveform(object(), width=1)

    def test_skipped_paints_and_zoom_changes_leave_captures_identical(self):
        tape = ((0, 1, 0, 0, 0, -2, 0, 3, 0), (0, -1, 0, 0, 0, 2, 0, -3, 0))
        plain = ScopeAcquisition(STEREO, window_frames=4, hop_frames=2, history_frames=4)
        expected = ingest(plain, 100, tape)
        viewed = ScopeAcquisition(STEREO, window_frames=4, hop_frames=2, history_frames=4)
        actual = []
        for left, right in ((0, 4), (4, 5), (5, 8), (8, 9)):
            captures = ingest(viewed, 100 + left, tuple(plane[left:right] for plane in tape))
            actual.extend(captures)
            if captures:
                project_waveform(captures[-1], width=2)
                project_waveform(captures[-1], width=5)
        self.assertEqual(tuple(actual), expected)


class IndependentOracleTests(unittest.TestCase):
    def test_every_small_width_matches_inverse_sample_assignment(self):
        start = 2**53 + 1
        for length in range(1, 129):
            plane = tuple((37 * i + 11) % 17 - 8 for i in range(length))
            frame = CaptureWindow(MONO, start, (plane,))
            for width in range(1, length + 1):
                groups = [[] for _ in range(width)]
                for i in range(length):
                    column = ((i + 1) * width - 1) // length
                    groups[column].append(i)

                expected = []
                for group in groups:
                    low = min(group, key=plane.__getitem__)
                    high = max(group, key=plane.__getitem__)
                    expected.append((
                        start + group[0], start + group[-1] + 1,
                        ChannelExtrema(plane[low], plane[high], start + low, start + high),
                    ))
                got = project_waveform(frame, width=width)
                self.assertEqual(
                    [(b.start_sample, b.end_sample_exclusive, b.extrema[0]) for b in got.buckets],
                    expected,
                    f"length={length}, width={width}",
                )

    def test_every_short_callback_partition_matches_direct_slices(self):
        origin = 2**53 + 1
        epoch = replace(STEREO, origin_sample=origin)
        tape = (tuple(range(12)), (7, -3, -5, 0, -4, 8, -3, -2, 3, 4, 5, -6))
        for length, hop, history in ((1, 1, 1), (4, 2, 4), (4, 7, 4), (4, 3, 7)):
            expected = [
                (origin + offset, origin + offset + length,
                 tuple(plane[offset:offset + length] for plane in tape))
                for offset in range(0, 13 - length, hop)
            ]
            for cuts in range(2**11):
                boundaries = [0] + [i for i in range(1, 12) if cuts & (1 << (i - 1))] + [12]
                scope = ScopeAcquisition(epoch, window_frames=length, hop_frames=hop, history_frames=history)
                actual = []
                for left, right in zip(boundaries, boundaries[1:]):
                    block = tuple(plane[left:right] for plane in tape)
                    actual.extend(ingest(scope, origin + left, block))
                self.assertEqual(spans(actual), expected, f"length={length}, hop={hop}, cuts={cuts}")
                self.assertEqual(scope.next_sample, origin + 12)


if __name__ == "__main__":
    unittest.main()
