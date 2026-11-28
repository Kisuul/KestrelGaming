"""Source coverage, presentation provenance, and sample-clocked quiet candidates."""

from dataclasses import replace
from fractions import Fraction as F
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in (
    "audio-dropout-detection", "audio-oscilloscope", "audio-rms-crest-factor",
    "audio-stream-buffering", "audio-timebase-sync",
):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_dropout_detection import (
    FrameInterval, PlayoutSegment, QuietDetector, QuietProfile, SourceCoverage, summarize_playout,
)
from reference_oscilloscope import MAX_BLOCK_FRAMES, MAX_SAMPLE_INDEX, ScopeEpoch
from reference_stream_buffer import FrameRing
from reference_timebase import DiscontinuityError


ORIGIN = 1000
SOURCE = ScopeEpoch("capture", ORIGIN, F(48000), "device-clock", "input", "FS", ("L", "R"))
PLAYOUT = replace(SOURCE, epoch_id="playout", tap_id="output")
PROFILE = QuietProfile(4, 4, 1/16, 1/4, 1/16)
QUIET_LEFT = (0.5,) * 4 + (0.0,) * 4 + (0.5,) * 4
ACTIVE_RIGHT = (0.5,) * 12
UNDERFLOW_KINDS = {"input": "original", "underrun_silence": "zero_fill", "overrun_gap": "zero_fill"}


def offer(ledger, start, frames, *, epoch=SOURCE):
    return ledger.ingest(epoch=epoch, start_sample=start, frame_count=frames)


def playout_from_pull(pull, *, epoch=PLAYOUT):
    segments = tuple(
        PlayoutSegment(FrameInterval(span.start_sample, span.start_sample + span.frames), UNDERFLOW_KINDS[span.kind])
        for span in pull["spans"]
    )
    return summarize_playout(
        epoch=epoch, start_sample=pull["start_sample"], frame_count=pull["frames"], segments=segments,
    )


def feed(detector, planes, *, epoch=SOURCE, start=None, usable=None):
    return detector.ingest(
        epoch=epoch, start_sample=detector.next_sample if start is None else start,
        planes=planes, usable=usable,
    )


def replay(planes, partitions, *, epoch=SOURCE, profile=PROFILE, usable=None):
    detector = QuietDetector(epoch, profile)
    offset = 0
    candidates, incomplete = [], []
    for count in partitions:
        end = offset + count
        update = feed(detector, tuple(plane[offset:end] for plane in planes), epoch=epoch,
                      usable=None if usable is None else usable[offset:end])
        candidates.extend(update.candidates)
        incomplete.extend(update.incomplete)
        offset = end
    incomplete.extend(detector.finish().incomplete)
    return tuple(candidates), tuple(incomplete)


class SourceCoverageTests(unittest.TestCase):
    def test_gap_is_provisional_until_explicitly_confirmed(self):
        for origin in (ORIGIN, 2**60 + ORIGIN):
            with self.subTest(origin=origin):
                epoch = replace(SOURCE, origin_sample=origin)
                ledger = SourceCoverage(epoch)
                self.assertEqual(offer(ledger, origin, 4, epoch=epoch).status, "accepted")
                update = offer(ledger, origin + 8, 4, epoch=epoch)
                self.assertEqual(update.status, "forward_gap")
                self.assertEqual(update.provisional_gap, FrameInterval(origin + 4, origin + 8))
                self.assertEqual(update.start_delta_frames, 4)
                self.assertEqual(ledger.next_sample, origin + 4)

                resumed = replace(epoch, epoch_id="resumed", origin_sample=origin + 8)
                confirmed = ledger.reset_epoch(resumed, confirm_gap=True)
                self.assertEqual((confirmed.before, confirmed.after), (epoch, resumed))
                self.assertEqual(confirmed.missing, update.provisional_gap)
                self.assertEqual((confirmed.missing.frames, confirmed.duration_seconds), (4, F(1, 12000)))
                self.assertEqual(offer(ledger, origin + 8, 4, epoch=resumed).status, "accepted")

    def test_reordered_arrival_can_recover_without_declared_loss(self):
        ledger = SourceCoverage(SOURCE)
        offer(ledger, ORIGIN, 4)
        self.assertEqual(offer(ledger, ORIGIN + 8, 4).status, "forward_gap")
        self.assertEqual(offer(ledger, ORIGIN + 4, 4).status, "accepted")
        self.assertEqual(offer(ledger, ORIGIN + 8, 4).status, "accepted")
        self.assertEqual(ledger.next_sample, ORIGIN + 12)

    def test_early_start_and_overlap_membership_are_distinct(self):
        ledger = SourceCoverage(SOURCE)
        offer(ledger, ORIGIN, 4)
        update = offer(ledger, ORIGIN + 1, 1)
        self.assertEqual((update.status, update.start_delta_frames), ("early_start", -3))
        self.assertEqual(update.overlap, FrameInterval(ORIGIN + 1, ORIGIN + 2))
        self.assertIsNone(update.provisional_gap)
        self.assertEqual(ledger.next_sample, ORIGIN + 4)

    def test_partial_overlap_does_not_accept_an_unseen_suffix(self):
        ledger = SourceCoverage(SOURCE)
        offer(ledger, ORIGIN, 4)
        update = offer(ledger, ORIGIN + 2, 4)
        self.assertEqual(update.offered, FrameInterval(ORIGIN + 2, ORIGIN + 6))
        self.assertEqual(update.overlap, FrameInterval(ORIGIN + 2, ORIGIN + 4))
        self.assertEqual(ledger.next_sample, ORIGIN + 4)
        self.assertEqual(offer(ledger, ORIGIN + 4, 2).status, "accepted")

    def test_overlap_is_clipped_to_the_observation_epoch(self):
        ledger = SourceCoverage(SOURCE)
        offer(ledger, ORIGIN, 4)
        update = offer(ledger, ORIGIN - 2, 3)
        self.assertEqual(update.start_delta_frames, -6)
        self.assertEqual(update.overlap, FrameInterval(ORIGIN, ORIGIN + 1))
        self.assertIsNone(offer(ledger, ORIGIN - 2, 2).overlap)
        self.assertEqual(ledger.next_sample, ORIGIN + 4)

    def test_known_expected_origin_can_bound_a_prefix_gap(self):
        ledger = SourceCoverage(SOURCE)
        update = offer(ledger, ORIGIN + 4, 4)
        self.assertEqual(update.provisional_gap, FrameInterval(ORIGIN, ORIGIN + 4))
        self.assertEqual(ledger.next_sample, ORIGIN)

    def test_seek_and_rate_change_use_the_new_origin(self):
        ledger = SourceCoverage(SOURCE)
        offer(ledger, ORIGIN, 4)
        seek = replace(SOURCE, epoch_id="seek", origin_sample=10, rate_hz=F(44100), channel_ids=("M",))
        self.assertIsNone(ledger.reset_epoch(seek))
        self.assertEqual(ledger.next_sample, 10)
        with self.assertRaisesRegex(ValueError, "current epoch"):
            offer(ledger, 10, 2)
        self.assertEqual(offer(ledger, 10, 2, epoch=seek).status, "accepted")

    def test_confirmation_requires_the_same_source_geometry_and_a_fresh_epoch(self):
        ledger = SourceCoverage(SOURCE)
        offer(ledger, ORIGIN, 4)
        forward = replace(SOURCE, epoch_id="other", origin_sample=ORIGIN + 8)
        invalid = (
            replace(forward, clock_domain="other"), replace(forward, rate_hz=F(44100)),
            replace(forward, tap_id="other"), replace(forward, units="volts"),
            replace(forward, channel_ids=("R", "L")), replace(forward, origin_sample=ORIGIN + 4),
            replace(forward, epoch_id=SOURCE.epoch_id),
        )
        for epoch in invalid:
            with self.subTest(epoch=epoch), self.assertRaises(ValueError):
                ledger.reset_epoch(epoch, confirm_gap=True)
            self.assertEqual(ledger.next_sample, ORIGIN + 4)
        self.assertEqual(offer(ledger, ORIGIN + 4, 4).status, "accepted")

    def test_invalid_geometry_is_atomic_and_exclusive_limit_is_exact(self):
        epoch = replace(SOURCE, origin_sample=MAX_SAMPLE_INDEX - 2)
        ledger = SourceCoverage(epoch)
        for frames in (False, 0, MAX_BLOCK_FRAMES + 1, 3):
            with self.subTest(frames=frames), self.assertRaises(ValueError):
                offer(ledger, epoch.origin_sample, frames, epoch=epoch)
            self.assertEqual(ledger.next_sample, epoch.origin_sample)
        self.assertEqual(offer(ledger, epoch.origin_sample, 2, epoch=epoch).status, "accepted")
        self.assertEqual(ledger.next_sample, MAX_SAMPLE_INDEX)


class PlayoutTests(unittest.TestCase):
    def test_acquired_zero_and_underrun_fill_have_identical_samples(self):
        options = dict(capacity_frames=12, channels=2, rate_hz=F(48000), origin_sample=ORIGIN,
                       underflow_policy="silence")
        captured = FrameRing(epoch_id="captured", **options)
        underrun = FrameRing(epoch_id="underrun", **options)
        active = ((.5,) * 4, (-.5,) * 4)
        captured.push(ORIGIN, active)
        captured.push(ORIGIN + 4, ((0.,) * 4, (0.,) * 4))
        captured.push(ORIGIN + 8, active)
        underrun.push(ORIGIN, active)
        fill = underrun.pull(ORIGIN, 8)
        presented = playout_from_pull(fill)
        before = underrun.snapshot()
        with self.assertRaises(ValueError):
            underrun.push(ORIGIN + 4, active)
        self.assertEqual(underrun.snapshot(), before)
        underrun.push(ORIGIN + 8, active)
        tail = underrun.pull(ORIGIN + 8, 4)
        actual = captured.pull(ORIGIN, 12)
        self.assertEqual(actual["planar_samples"], [a + b for a, b in zip(fill["planar_samples"], tail["planar_samples"])])
        self.assertEqual((playout_from_pull(actual).original_frames, playout_from_pull(actual).replacement_frames), (12, 0))
        self.assertEqual((presented.original_frames, presented.replacement_frames), (4, 4))
        self.assertEqual(playout_from_pull(tail).original_frames, 4)
        self.assertEqual(presented.segments[-1], PlayoutSegment(FrameInterval(1004, 1008), "zero_fill"))

    def test_repeat_concealment_matches_a_periodic_original(self):
        period = (0.25, -0.5, 0.5, -0.25)
        original = period * 3
        replayed = tuple(period[index % len(period)] for index in range(4))
        concealed = period + replayed + period
        self.assertEqual(original, concealed)
        self.assertTrue(all(concealed))
        first, mid, last = (FrameInterval(ORIGIN + i, ORIGIN + i + 4) for i in (0, 4, 8))
        ledger = SourceCoverage(SOURCE)
        offer(ledger, first.start_sample, first.frames)
        pending = offer(ledger, last.start_sample, last.frames)
        resumed = replace(SOURCE, epoch_id="resumed", origin_sample=last.start_sample)
        confirmed = ledger.reset_epoch(resumed, confirm_gap=True)
        segments = (PlayoutSegment(first, "original"), PlayoutSegment(mid, "repeat"), PlayoutSegment(last, "original"))
        report = summarize_playout(epoch=PLAYOUT, start_sample=ORIGIN, frame_count=12, segments=segments)
        self.assertEqual((report.original_frames, report.replacement_frames), (8, 4))
        self.assertEqual(report.segments[1].interval, pending.provisional_gap)
        self.assertEqual(report.segments[1].interval, confirmed.missing)
        self.assertEqual(replay((concealed, original), (12,)), ((), ()))

    def test_discard_and_overrun_fill_refer_to_one_interval(self):
        fifo = FrameRing(capacity_frames=4, channels=2, rate_hz=F(48000), epoch_id="fifo", origin_sample=ORIGIN,
                         overflow_policy="drop_oldest", underflow_policy="silence")
        fifo.push(ORIGIN, ((.5,) * 4, (-.5,) * 4))
        discarded = fifo.push(ORIGIN + 4, ((.25, .25), (-.25, -.25)))
        rendered = playout_from_pull(fifo.pull(ORIGIN, 6))
        self.assertEqual(discarded["dropped_span"], (ORIGIN, ORIGIN + 2))
        self.assertEqual(rendered.segments[0].interval, FrameInterval(*discarded["dropped_span"]))
        self.assertEqual((rendered.original_frames, rendered.replacement_frames), (4, 2))

    def test_frame_totals_retain_unrendered_and_unknown_provenance(self):
        kinds = ("original", "zero_fill", "repeat", "other_concealment", "unrendered", "unknown")
        segments = [PlayoutSegment(FrameInterval(ORIGIN + i, ORIGIN + i + 1), kind) for i, kind in enumerate(kinds)]
        summary = summarize_playout(epoch=PLAYOUT, start_sample=ORIGIN, frame_count=6, segments=segments)
        self.assertEqual((summary.original_frames, summary.replacement_frames,
                          summary.unrendered_frames, summary.unknown_frames), (1, 3, 1, 1))
        segments.clear()
        self.assertEqual(tuple(segment.kind for segment in summary.segments), kinds)

    def test_playout_requires_an_explicit_partition_of_the_request(self):
        first = PlayoutSegment(FrameInterval(ORIGIN, ORIGIN + 1), "original")
        fixtures = (
            (),
            (first,),
            (first, first),
            (first, PlayoutSegment(FrameInterval(ORIGIN + 2, ORIGIN + 3), "unrendered")),
            (PlayoutSegment(FrameInterval(ORIGIN + 1, ORIGIN + 2), "unrendered"),),
            (PlayoutSegment(FrameInterval(ORIGIN, ORIGIN + 2), "original"),
             PlayoutSegment(FrameInterval(ORIGIN + 1, ORIGIN + 2), "repeat")),
            (PlayoutSegment(FrameInterval(ORIGIN, ORIGIN + 3), "original"),),
        )
        for segments in fixtures:
            with self.subTest(segments=segments), self.assertRaises(ValueError):
                summarize_playout(epoch=PLAYOUT, start_sample=ORIGIN, frame_count=2, segments=segments)


class QuietWindowTests(unittest.TestCase):
    def test_candidate_requires_the_complete_following_window(self):
        detector = QuietDetector(SOURCE, PROFILE)
        first = feed(detector, (QUIET_LEFT[:11], ACTIVE_RIGHT[:11]))
        self.assertEqual(first.observed_end_sample_exclusive, 1011)
        self.assertEqual(first.candidates, ())
        update = feed(detector, (QUIET_LEFT[11:], ACTIVE_RIGHT[11:]))
        (event,) = update.candidates
        self.assertEqual(event.channel_id, "L")
        self.assertEqual(event.quiet, FrameInterval(1004, 1008))
        self.assertEqual(event.support, FrameInterval(1000, 1012))
        self.assertEqual(event.ready_sample_exclusive, 1012)
        self.assertEqual((event.quiet_rms_max, event.before_rms, event.after_rms, event.ratio), (0., .5, .5, F(0)))
        self.assertEqual(detector.finish().incomplete, ())

    def test_all_callback_partitions_match_at_two_exact_origins(self):
        for origin in (ORIGIN, 2**60 + ORIGIN):
            epoch = replace(SOURCE, origin_sample=origin)
            baseline = replay((QUIET_LEFT, ACTIVE_RIGHT), (12,), epoch=epoch)
            event, = baseline[0]
            self.assertEqual(event.quiet, FrameInterval(origin + 4, origin + 8))
            self.assertEqual(event.ready_sample_exclusive, origin + 12)
            for bits in range(2**11):
                edges = [0] + [i for i in range(1, 12) if bits & (1 << (i - 1))] + [12]
                partitions = tuple(b - a for a, b in zip(edges, edges[1:]))
                self.assertEqual(replay((QUIET_LEFT, ACTIVE_RIGHT), partitions, epoch=epoch), baseline)

    def test_inclusive_thresholds_and_a_nonredundant_ratio_gate(self):
        boundary = (.25,) * 4 + (1/64,) * 4 + (.25,) * 4
        (event,), _ = replay((boundary, ACTIVE_RIGHT), (3, 2, 7))
        self.assertEqual(event.ratio, F(1, 16))
        self.assertEqual(event.before_rms, PROFILE.active_rms_min)
        absolute = (1.,) * 4 + (1/16,) * 4 + (1.,) * 4
        (event,), _ = replay((absolute, ACTIVE_RIGHT), (12,))
        self.assertEqual(event.quiet_rms_max, PROFILE.quiet_rms_max)
        excessive = (.25,) * 4 + (1/32,) * 4 + (.25,) * 4
        self.assertEqual(replay((excessive, ACTIVE_RIGHT), (12,)), ((), ()))

    def test_run_uses_loudest_quiet_window_and_weaker_active_context(self):
        admitted = replace(PROFILE, relative_quiet_max=1/8)
        for first, last in ((1/32, 1/128), (1/128, 1/32)):
            with self.subTest(first=first, last=last):
                plane = (.5,) * 4 + (first,) * 4 + (last,) * 4 + (.25,) * 4
                stereo = (plane, (.5,) * len(plane))
                self.assertEqual(replay(stereo, (5, 7, 4)), ((), ()))
                (event,), _ = replay(stereo, (5, 7, 4), profile=admitted)
                self.assertEqual(event.quiet, FrameInterval(1004, 1012))
                self.assertEqual((event.quiet_rms_max, event.ratio, event.ready_sample_exclusive),
                                 (1/32, F(1, 8), 1016))

    def test_short_runs_and_inactive_neighbors_do_not_qualify(self):
        self.assertEqual(replay((QUIET_LEFT, ACTIVE_RIGHT), (12,),
                                profile=replace(PROFILE, minimum_quiet_frames=5)), ((), ()))
        initial_quiet = (0.,) * 4 + (.5,) * 4
        self.assertEqual(replay((initial_quiet, (.5,) * 8), (8,)), ((), ()))
        weak_post = QUIET_LEFT[:8] + (.125,) * 4 + (.5,) * 4
        self.assertEqual(replay((weak_post, (.5,) * 16), (16,)), ((), ()))

    def test_explicit_synthetic_samples_break_the_window_grid(self):
        for bad_index in (3, 4, 11):
            usable = tuple(index != bad_index for index in range(12))
            with self.subTest(bad_index=bad_index):
                candidates, incomplete = replay((QUIET_LEFT, ACTIVE_RIGHT), (2, 3, 7), usable=usable)
                self.assertEqual(candidates, ())
                if bad_index == 11:
                    (record,) = incomplete
                    self.assertEqual((record.quiet, record.reason), (FrameInterval(1004, 1008), "unusable_window"))

    def test_finish_retains_an_incomplete_run_once(self):
        detector = QuietDetector(SOURCE, PROFILE)
        feed(detector, (QUIET_LEFT[:11], ACTIVE_RIGHT[:11]))
        finish = detector.finish()
        (record,) = finish.incomplete
        self.assertEqual((record.channel_id, record.quiet, record.before_rms, record.reason),
                         ("L", FrameInterval(1004, 1008), 0.5, "end_of_input"))
        self.assertTrue(finish.finalized)
        self.assertEqual(finish.observed_end_sample_exclusive, 1011)
        self.assertEqual(detector.finish().incomplete, ())
        with self.assertRaisesRegex(ValueError, "after finalizing"):
            feed(detector, ((.5,), (.5,)))

    def test_gap_ends_the_old_context_and_resets_the_window_anchor(self):
        detector = QuietDetector(SOURCE, PROFILE)
        feed(detector, (QUIET_LEFT[:8], ACTIVE_RIGHT[:8]))
        with self.assertRaises(DiscontinuityError):
            feed(detector, ((.5,) * 4, (.5,) * 4), start=1011)
        self.assertEqual(detector.next_sample, 1008)
        resumed = replace(SOURCE, epoch_id="resumed", origin_sample=1011)
        old = detector.reset_epoch(resumed, reason="gap")
        self.assertEqual(old.observed_end_sample_exclusive, 1008)
        self.assertEqual(old.incomplete[0].reason, "gap")
        new = feed(detector, (QUIET_LEFT, ACTIVE_RIGHT), epoch=resumed)
        (event,) = new.candidates
        self.assertEqual(event.quiet, FrameInterval(1015, 1019))
        self.assertEqual(event.ready_sample_exclusive, 1023)

    def test_reconfigured_epoch_can_change_channel_count_and_sample_rate(self):
        detector = QuietDetector(SOURCE, PROFILE)
        feed(detector, (QUIET_LEFT[:8], ACTIVE_RIGHT[:8]))
        seek = replace(SOURCE, epoch_id="seek", origin_sample=10, rate_hz=F(44100), channel_ids=("M",))
        with self.assertRaises(ValueError):
            detector.reset_epoch(seek, reason="gap")
        self.assertEqual(detector.next_sample, 1008)
        old = detector.reset_epoch(seek)
        self.assertEqual(old.incomplete[0].reason, "epoch_change")
        (event,) = feed(detector, (QUIET_LEFT,), epoch=seek).candidates
        self.assertEqual((event.channel_id, event.quiet, event.ready_sample_exclusive),
                         ("M", FrameInterval(14, 18), 22))

    def test_invalid_second_plane_or_mask_leaves_the_pending_state_intact(self):
        detector = QuietDetector(SOURCE, PROFILE)
        feed(detector, (QUIET_LEFT[:6], ACTIVE_RIGHT[:6]))
        with self.assertRaisesRegex(ValueError, "finite"):
            feed(detector, (QUIET_LEFT[6:], (math.nan,) + ACTIVE_RIGHT[7:]))
        for usable in ((True,), (True,) * 5 + (1,)):
            with self.subTest(usable=usable), self.assertRaises(ValueError):
                feed(detector, (QUIET_LEFT[6:], ACTIVE_RIGHT[6:]), usable=usable)
        self.assertEqual(detector.next_sample, 1006)
        (event,) = feed(detector, (QUIET_LEFT[6:], ACTIVE_RIGHT[6:])).candidates
        self.assertEqual((event.quiet, event.ready_sample_exclusive), (FrameInterval(1004, 1008), 1012))

    def test_simultaneous_candidates_keep_declared_channel_order(self):
        epoch = replace(SOURCE, channel_ids=("Z", "A"))
        candidates, _ = replay((QUIET_LEFT, QUIET_LEFT), (7, 2, 3), epoch=epoch)
        self.assertEqual(tuple(event.channel_id for event in candidates), ("Z", "A"))

    def test_measurable_large_rms_and_nonzero_ratio_do_not_overflow_or_round_to_zero(self):
        tiny = math.ulp(0.0)
        plane = (1e308,) * 4 + (tiny,) * 4 + (1e308,) * 4
        stereo = (plane, ACTIVE_RIGHT)
        (event,), _ = replay(stereo, (12,))
        self.assertEqual((event.before_rms, event.after_rms), (1e308, 1e308))
        self.assertGreater(event.ratio, 0)
        self.assertEqual(replay(stereo, (12,), profile=replace(PROFILE, relative_quiet_max=0)), ((), ()))

    def test_unrepresentable_nonzero_rms_is_unusable_at_a_zero_quiet_floor(self):
        plane = (.5,) * 8 + (math.ulp(0.0),) + (0.,) * 7 + (.5,) * 8
        profile = QuietProfile(8, 8, 0, 1/4, 1/16)
        self.assertEqual(replay((plane, (.5,) * 24), (24,), profile=profile), ((), ()))

    def test_invalid_profile_values(self):
        for change in (
            {"window_frames": 0}, {"window_frames": 257}, {"minimum_quiet_frames": True},
            {"active_rms_min": 0}, {"active_rms_min": math.inf}, {"quiet_rms_max": math.nan},
            {"quiet_rms_max": 1/4}, {"relative_quiet_max": 1.001}, {"relative_quiet_max": 2**2048},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(PROFILE, **change)


if __name__ == "__main__":
    unittest.main()
