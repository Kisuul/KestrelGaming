"""Analytic trigger timelines, exact arithmetic, and split-block checks."""

from dataclasses import replace
from fractions import Fraction
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-oscilloscope/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-scope-triggering/scripts"))
from reference_oscilloscope import (
    CaptureWindow, MAX_BLOCK_FRAMES, MAX_HISTORY_FRAMES, MAX_SAMPLE_INDEX,
    ScopeEpoch, project_waveform,
)
from reference_scope_triggering import (
    CaptureAborted, CaptureComplete, CrossingDecision, ScopeTrigger, TriggerSettings,
)


STEREO = ScopeEpoch("take-a", 0, Fraction(48_000), "input-clock", "pre-gain", "FS", ("L", "R"))
MONO = replace(STEREO, channel_ids=("L",))
RISING = TriggerSettings("L", hysteresis=0.5)


def ingest(scope, start, *planes):
    return scope.ingest(epoch=scope.epoch, start_sample=start, planes=planes)


def dispositions(events):
    return [
        (event.detection_sample, event.disposition)
        for event in events if type(event) is CrossingDecision
    ]


class EdgeTests(unittest.TestCase):
    def test_split_crossing_retains_trigger_pair_and_independent_display_plane(self):
        epoch = replace(STEREO, origin_sample=100)
        scope = ScopeTrigger(epoch, replace(RISING, channel_id="R", pre_frames=2, post_frames=1))
        self.assertEqual(ingest(scope, 100, [9, 8], [-1, -0.25]), ())
        (decision,) = ingest(scope, 102, [7], [0.75])
        self.assertEqual((decision.epoch, decision.settings.channel_id), (epoch, "R"))
        self.assertEqual((decision.left_sample, decision.detection_sample), (101, 102))
        self.assertEqual((decision.left_value, decision.right_value), (-0.25, 0.75))
        self.assertEqual(decision.fraction, Fraction(1, 4))
        self.assertEqual(decision.disposition, "accepted")
        self.assertEqual((decision.requested_start_sample, decision.requested_end_sample_exclusive),
                         (100, 104))
        self.assertIs(scope.pending, decision)

        (ready,) = ingest(scope, 103, [6], [0.5])
        self.assertIs(ready.trigger, decision)
        self.assertEqual(ready.window, CaptureWindow(epoch, 100, ((9, 8, 7, 6), (-1, -0.25, 0.75, 0.5))))
        self.assertIsNone(scope.pending)
        points = project_waveform(ready.window, width=5).points
        self.assertEqual([(p.sample_index, p.values[0]) for p in points], [(100, 9), (101, 8), (102, 7), (103, 6)])

    def test_threshold_plateau_and_hysteresis_band_in_both_directions(self):
        signal = (-1, 0, 0, -0.25, 0, -1, 0)
        for direction, values in (("rising", signal), ("falling", tuple(-x for x in signal))):
            with self.subTest(direction=direction):
                scope = ScopeTrigger(MONO, replace(RISING, direction=direction))
                out = ingest(scope, 0, values)
                self.assertEqual(dispositions(out), [(1, "accepted"), (4, "unarmed"), (6, "accepted")])
                edges = [x for x in out if type(x) is CrossingDecision]
                self.assertEqual([x.fraction for x in edges], [1, 1, 1])

    def test_zero_hysteresis_arms_only_from_the_source_side(self):
        scope = ScopeTrigger(MONO, replace(RISING, hysteresis=0))
        self.assertEqual(dispositions(ingest(scope, 0, [0, 1, 0, -1, 0, 0])), [(4, "accepted")])

    def test_hysteresis_arm_boundary_includes_equality(self):
        for direction, values in (("rising", [-0.5, 0]), ("falling", [0.5, 0])):
            with self.subTest(direction=direction):
                scope = ScopeTrigger(MONO, replace(RISING, direction=direction))
                self.assertEqual(dispositions(ingest(scope, 0, values)), [(1, "accepted")])

    def test_rounding_the_hysteresis_boundary_would_arm_a_false_edge(self):
        h = 5 * 2**-55
        first = math.nextafter(1.0, 0.0)
        second = math.nextafter(first, 0.0)
        self.assertEqual(1.0 - h, first)
        self.assertGreater(Fraction(first), 1 - Fraction(h))
        for direction, sign in (("rising", 1), ("falling", -1)):
            with self.subTest(direction=direction):
                scope = ScopeTrigger(MONO, replace(RISING, level=sign, direction=direction, hysteresis=h))
                out = ingest(scope, 0, tuple(sign * x for x in (first, 1, second, 1)))
                self.assertEqual(dispositions(out), [(1, "unarmed"), (3, "accepted")])

    def test_interpolation_of_opposite_binary64_extremes(self):
        high = sys.float_info.max
        for direction, signal in (("rising", (-high, high)), ("falling", (high, -high))):
            with self.subTest(direction=direction):
                scope = ScopeTrigger(MONO, replace(RISING, direction=direction))
                edge, ready = ingest(scope, 0, signal)
                self.assertEqual(edge.fraction, Fraction(1, 2))
                self.assertEqual(ready.window.planes, ((signal[1],),))
        self.assertEqual(high / (high - (-high)), 0.0)

    def test_fraction_can_be_smaller_than_the_smallest_binary64(self):
        tiny = float.fromhex("0x0.0000000000001p-1022")
        high = sys.float_info.max
        scope = ScopeTrigger(MONO, TriggerSettings("L", level=tiny))
        edge, _ = ingest(scope, 0, [0, high])
        self.assertGreater(edge.fraction, 0)
        self.assertLess(edge.fraction, Fraction(tiny))
        self.assertEqual(edge.fraction, Fraction(tiny) / Fraction(high))
        self.assertEqual(float(edge.fraction), 0.0)

    def test_interpolated_position_stays_split_above_binary64_integer_range(self):
        origin = 2**53 + 1
        scope = ScopeTrigger(replace(MONO, origin_sample=origin), TriggerSettings("L"))
        self.assertEqual(ingest(scope, origin, [-0.25]), ())
        edge, _ = ingest(scope, origin + 1, [0.75])
        self.assertEqual((edge.left_sample, edge.fraction, edge.detection_sample),
                         (origin, Fraction(1, 4), origin + 1))
        self.assertEqual(float(edge.left_sample + edge.fraction), 2**53 + 2)


class AcquisitionTests(unittest.TestCase):
    def test_holdoff_rejects_before_release_and_admits_equality(self):
        for signal, expected in (
            ([-1, 1, -1, -1, 1, -1], [(1, "accepted"), (4, "holdoff")]),
            ([-1, 1, -1, -1, -1, 1], [(1, "accepted"), (5, "accepted")]),
        ):
            with self.subTest(signal=signal):
                scope = ScopeTrigger(MONO, replace(RISING, holdoff_frames=4))
                out = ingest(scope, 0, signal)
                self.assertEqual(dispositions(out), expected)
                self.assertEqual(out[0].holdoff_release_sample, 5)
                self.assertEqual(out[2].holdoff_release_sample, 5 if expected[1][1] == "holdoff" else 9)

    def test_holdoff_suppression_consumes_arm(self):
        scope = ScopeTrigger(MONO, replace(RISING, holdoff_frames=4))
        out = ingest(scope, 0, [-1, 1, -1, 1, -0.25, 1, -1, 1])
        self.assertEqual(dispositions(out), [(1, "accepted"), (3, "holdoff"), (5, "unarmed"), (7, "accepted")])
        releases = [x.holdoff_release_sample for x in out if type(x) is CrossingDecision]
        self.assertEqual(releases, [5, 5, 5, 11])

    def test_last_sample_remains_busy_and_reports_old_completion_after_crossing(self):
        scope = ScopeTrigger(MONO, replace(RISING, post_frames=2))
        out = ingest(scope, 0, [-1, 1, -1, 1, -1, 1, -1, -1])
        self.assertEqual(dispositions(out), [(1, "accepted"), (3, "busy"), (5, "accepted")])
        self.assertEqual([type(x) for x in out], [
            CrossingDecision, CrossingDecision, CaptureComplete, CrossingDecision, CaptureComplete,
        ])
        self.assertEqual((out[2].window.start_sample, out[2].window.end_sample_exclusive), (1, 4))
        self.assertEqual((out[4].window.start_sample, out[4].window.end_sample_exclusive), (5, 8))
        self.assertEqual(out[1].holdoff_release_sample, 1)

    def test_sample_at_exclusive_end_can_start_another_capture(self):
        scope = ScopeTrigger(MONO, replace(RISING, post_frames=1))
        out = ingest(scope, 0, [-1, 1, -1, 1])
        self.assertEqual(dispositions(out), [(1, "accepted"), (3, "accepted")])
        self.assertEqual(out[1].window.end_sample_exclusive, 3)
        self.assertIs(scope.pending, out[2])
        self.assertEqual(out[2].requested_end_sample_exclusive, 5)

    def test_holdoff_takes_precedence_when_pending_is_also_busy(self):
        scope = ScopeTrigger(MONO, replace(RISING, post_frames=2, holdoff_frames=4))
        out = ingest(scope, 0, [-1, 1, -1, 1, -1, 1])
        self.assertEqual(dispositions(out), [(1, "accepted"), (3, "holdoff"), (5, "accepted")])
        self.assertEqual((type(out[2]), out[2].window.end_sample_exclusive), (CaptureComplete, 4))

    def test_missing_prehistory_does_not_start_holdoff(self):
        scope = ScopeTrigger(MONO, replace(RISING, pre_frames=2, holdoff_frames=10))
        out = ingest(scope, 0, [-1, 1, -1, 1])
        self.assertEqual(dispositions(out), [(1, "missing_prehistory"), (3, "accepted")])
        self.assertIsNone(out[0].holdoff_release_sample)
        self.assertEqual((out[2].window.start_sample, out[2].window.planes), (1, ((1, -1, 1),)))

    def test_unsupported_capture_end_preserves_valid_input_and_reports_suppression(self):
        epoch = replace(MONO, origin_sample=MAX_SAMPLE_INDEX - 2)
        scope = ScopeTrigger(epoch, replace(RISING, post_frames=1))
        (edge,) = ingest(scope, epoch.origin_sample, [-1, 1])
        self.assertEqual((edge.detection_sample, edge.disposition), (MAX_SAMPLE_INDEX - 1, "span_out_of_range"))
        self.assertEqual(edge.requested_end_sample_exclusive, MAX_SAMPLE_INDEX + 1)
        self.assertIsNone(edge.holdoff_release_sample)
        self.assertIsNone(scope.pending)
        self.assertEqual(scope.next_sample, MAX_SAMPLE_INDEX)

    def test_supported_capture_can_end_at_limit_and_holdoff_can_extend_past_it(self):
        epoch = replace(MONO, origin_sample=MAX_SAMPLE_INDEX - 2)
        scope = ScopeTrigger(epoch, replace(RISING, holdoff_frames=MAX_SAMPLE_INDEX))
        edge, ready = ingest(scope, epoch.origin_sample, [-1, 1])
        self.assertEqual(edge.holdoff_release_sample, 2 * MAX_SAMPLE_INDEX - 1)
        self.assertEqual(ready.window.end_sample_exclusive, MAX_SAMPLE_INDEX)

    def test_long_block_can_complete_many_short_spans(self):
        scope = ScopeTrigger(MONO, replace(RISING, post_frames=1))
        out = ingest(scope, 0, [-1, 1] * (MAX_BLOCK_FRAMES // 2))
        complete = [x for x in out if type(x) is CaptureComplete]
        self.assertEqual([x.trigger.detection_sample for x in complete], list(range(1, MAX_BLOCK_FRAMES - 1, 2)))
        self.assertTrue(all(x.window.planes == ((1, -1),) for x in complete))
        self.assertEqual(scope.pending.detection_sample, MAX_BLOCK_FRAMES - 1)

    def test_maximum_pre_and_post_capture_crosses_several_callbacks(self):
        before = MAX_HISTORY_FRAMES // 2
        after = MAX_HISTORY_FRAMES - before - 1
        scope = ScopeTrigger(STEREO, replace(RISING, pre_frames=before, post_frames=after))
        pcm = ([-1] * before + [1] * (after + 1), list(range(MAX_HISTORY_FRAMES)))
        out = []
        for i in range(0, MAX_HISTORY_FRAMES, MAX_BLOCK_FRAMES):
            out.extend(ingest(scope, i, *(plane[i:i + MAX_BLOCK_FRAMES] for plane in pcm)))
        decision, complete = out
        self.assertEqual(decision.detection_sample, before)
        self.assertEqual(complete.window.planes, tuple(tuple(x) for x in pcm))
        pcm[0][0] = 9
        self.assertEqual(complete.window.planes[0][0], -1)
        self.assertEqual(complete.window.frame_count, MAX_HISTORY_FRAMES)

    def test_invalid_block_keeps_pending_and_allows_identical_clean_retry(self):
        options = replace(RISING, post_frames=2, holdoff_frames=4)
        scope = ScopeTrigger(STEREO, options)
        (pending,) = ingest(scope, 0, [-1, 1], [9, 8])
        valid = [[-1, 1, -1, 1, -1, -1], [7, 6, 5, 4, 3, 2]]
        invalid = (
            [], [[], []], [valid[0]], [valid[0], [7]], [valid[0], [7, 6, 5, 4, 3, math.nan]],
            [valid[0], [7, 6, 5, 4, 3, math.inf]], [valid[0], [7, 6, 5, 4, 3, True]],
            [[-1] * (MAX_BLOCK_FRAMES + 1)] * 2,
        )
        for number, planes in enumerate(invalid):
            with self.subTest(case=number), self.assertRaises(ValueError):
                ingest(scope, 2, *planes)
            self.assertEqual(scope.next_sample, 2)
            self.assertIs(scope.pending, pending)

        clean = ScopeTrigger(STEREO, options)
        expected = ingest(clean, 0, [-1, 1] + valid[0], [9, 8] + valid[1])
        self.assertEqual((pending,) + ingest(scope, 2, *valid), expected)

    def test_invalid_block_does_not_replace_the_arming_sample(self):
        scope = ScopeTrigger(STEREO, RISING)
        ingest(scope, 0, [-1], [5])
        with self.assertRaises(ValueError):
            ingest(scope, 1, [1, -0.25], [4, math.nan])
        edge, ready = ingest(scope, 1, [0], [4])
        self.assertEqual((edge.left_value, edge.fraction, edge.disposition), (-1, 1, "accepted"))
        self.assertEqual(ready.window.planes, ((0,), (4,)))

    def test_gap_overlap_and_mismatched_channel_metadata_leave_state_intact(self):
        scope = ScopeTrigger(STEREO, RISING)
        ingest(scope, 0, [-1], [1])
        for kind, start in (("gap", 2), ("overlap", 0)):
            with self.subTest(kind=kind), self.assertRaisesRegex(
                ValueError, f"{kind}: expected start=1, observed={start}"
            ):
                ingest(scope, start, [1], [0])
        swapped = replace(STEREO, channel_ids=("R", "L"))
        with self.assertRaisesRegex(ValueError, "active epoch"):
            scope.ingest(epoch=swapped, start_sample=1, planes=([1], [0]))
        with self.assertRaisesRegex(ValueError, "sample index range"):
            ingest(scope, True, [1], [0])
        self.assertEqual(dispositions(ingest(scope, 1, [1], [0])), [(1, "accepted")])

    def test_invalid_settings_and_trigger_channel(self):
        for change in (
            {"direction": "both"}, {"mode": "auto"}, {"channel_id": ""},
            {"level": math.inf}, {"hysteresis": math.nan}, {"level": True}, {"hysteresis": -1},
            {"pre_frames": -1}, {"post_frames": 0.5}, {"holdoff_frames": False},
            {"holdoff_frames": MAX_SAMPLE_INDEX + 1},
            {"pre_frames": MAX_HISTORY_FRAMES - 1, "post_frames": 1},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(RISING, **change)
        with self.assertRaisesRegex(ValueError, "trigger channel"):
            ScopeTrigger(MONO, replace(RISING, channel_id="R"))

    def test_reset_aborts_one_pending_span_and_restarts_on_the_named_channel(self):
        scope = ScopeTrigger(STEREO, replace(RISING, post_frames=2, holdoff_frames=99))
        (old,) = ingest(scope, 0, [-1, 1], [3, 4])
        fresh = replace(STEREO, epoch_id="take-b", channel_ids=("R", "L"), rate_hz=Fraction(44_100))
        self.assertEqual(scope.reset_epoch(fresh), CaptureAborted(old, "take-b"))
        self.assertEqual((scope.next_sample, scope.epoch, scope.pending), (0, fresh, None))
        with self.assertRaisesRegex(ValueError, "active epoch"):
            scope.ingest(epoch=STEREO, start_sample=0, planes=([-1], [5]))
        self.assertEqual(ingest(scope, 0, [4], [1]), ())
        decision, ready = ingest(scope, 1, [5, 6, 7, 8], [-1, 1, 0, 0])
        self.assertEqual((decision.epoch, decision.left_sample, decision.detection_sample), (fresh, 1, 2))
        self.assertEqual(ready.window.planes, ((6, 7, 8), (1, 0, 0)))
        self.assertIsNone(scope.reset_epoch(replace(fresh, epoch_id="take-c")))

    def test_failed_epoch_reset_keeps_the_pending_capture_and_the_new_id_available(self):
        scope = ScopeTrigger(STEREO, replace(RISING, post_frames=1))
        (old,) = ingest(scope, 0, [-1, 1], [5, 6])
        with self.assertRaisesRegex(ValueError, "already been used"):
            scope.reset_epoch(replace(STEREO, origin_sample=100))
        candidate = replace(STEREO, epoch_id="take-b", channel_ids=("R",))
        with self.assertRaisesRegex(ValueError, "trigger channel"):
            scope.reset_epoch(candidate)
        self.assertIs(scope.pending, old)
        (ready,) = ingest(scope, 2, [0], [7])
        self.assertEqual(ready.window.planes, ((1, 0), (6, 7)))
        self.assertIsNone(scope.reset_epoch(replace(candidate, channel_ids=("L",))))


class SingleShotTests(unittest.TestCase):
    def test_one_acceptance_per_arm(self):
        scope = ScopeTrigger(MONO, replace(RISING, mode="single"))
        first = ingest(scope, 0, [-1, 1])
        scope.arm_single()
        second = ingest(scope, 2, [-1, 1, -1, 1])
        scope.arm_single()
        third = ingest(scope, 6, [-1, 1])
        self.assertEqual(dispositions(first + second + third), [
            (1, "single_disarmed"), (3, "accepted"), (5, "single_disarmed"), (7, "accepted"),
        ])

    def test_first_arm_needs_a_fresh_source_sample_but_repeated_arm_is_idempotent(self):
        scope = ScopeTrigger(MONO, replace(RISING, mode="single", pre_frames=1))
        ingest(scope, 0, [-1])
        scope.arm_single()
        self.assertEqual(dispositions(ingest(scope, 1, [1])), [(1, "unarmed")])
        ingest(scope, 2, [-1])
        scope.arm_single()
        edge, ready = ingest(scope, 3, [1])
        self.assertEqual(edge.disposition, "accepted")
        self.assertEqual(ready.window.planes, ((-1, 1),))

    def test_pending_rejects_arm_and_later_arm_preserves_holdoff(self):
        scope = ScopeTrigger(MONO, replace(RISING, mode="single", post_frames=1, holdoff_frames=5))
        scope.arm_single()
        (first,) = ingest(scope, 0, [-1, 1])
        with self.assertRaisesRegex(ValueError, "pending"):
            scope.arm_single()
        (ready,) = ingest(scope, 2, [-1])
        self.assertIs(ready.trigger, first)
        scope.arm_single()
        out = ingest(scope, 3, [-1, 1, -1, 1, -1])
        self.assertEqual(dispositions(out), [(4, "holdoff"), (6, "accepted")])
        self.assertEqual(out[0].holdoff_release_sample, 6)

    def test_missing_prehistory_leaves_shot_permission_available(self):
        scope = ScopeTrigger(MONO, replace(RISING, mode="single", pre_frames=2))
        scope.arm_single()
        out = ingest(scope, 0, [-1, 1, -1, 1])
        self.assertEqual(dispositions(out), [(1, "missing_prehistory"), (3, "accepted")])

    def test_reset_clears_single_permission(self):
        scope = ScopeTrigger(MONO, replace(RISING, mode="single"))
        scope.arm_single()
        scope.reset_epoch(replace(MONO, epoch_id="take-b"))
        self.assertEqual(dispositions(ingest(scope, 0, [-1, 1])), [(1, "single_disarmed")])

    def test_normal_mode_has_no_arm_command(self):
        with self.assertRaisesRegex(ValueError, "single-shot"):
            ScopeTrigger(MONO, RISING).arm_single()


def tape_oracle(tape, epoch, settings):
    """Recompute arming from the original tape since its last crossing."""
    trigger = tuple(Fraction(x) for x in tape[epoch.channel_ids.index(settings.channel_id)])
    direction = settings.direction
    threshold = Fraction(settings.level)
    h = Fraction(settings.hysteresis)
    o = epoch.origin_sample
    previous_edge = 0
    last_accepted = None
    timeline = []
    for i, (left, right) in enumerate(zip(trigger, trigger[1:]), 1):
        if direction == "rising":
            if not left < threshold <= right:
                continue
            source_extreme = min(trigger[previous_edge:i])
            armed = source_extreme <= threshold - h if h else source_extreme < threshold
        else:
            if not left > threshold >= right:
                continue
            source_extreme = max(trigger[previous_edge:i])
            armed = source_extreme >= threshold + h if h else source_extreme > threshold
        previous_edge = i
        start = i - settings.pre_frames
        end = i + settings.post_frames + 1
        if not armed:
            reason = "unarmed"
        elif last_accepted is not None and i - last_accepted < settings.holdoff_frames:
            reason = "holdoff"
        elif last_accepted is not None and i - last_accepted <= settings.post_frames:
            reason = "busy"
        elif start < 0:
            reason = "missing_prehistory"
        else:
            reason = "accepted"
            last_accepted = i
            if end <= len(trigger):
                samples = tuple(plane[start:end] for plane in tape)
                timeline.append((end - 1, 1, ("ready", o + i, o + start, o + end, samples)))
        release = None if last_accepted is None else o + last_accepted + settings.holdoff_frames
        edge = ("edge", o + i, o + i - 1, (threshold - left) / (right - left), reason,
                o + start, o + end, release)
        timeline.append((i, 0, edge))
    return [event for _, _, event in sorted(timeline)]


def flatten(events):
    timeline = []
    for event in events:
        if type(event) is CrossingDecision:
            timeline.append((
                "edge", event.detection_sample, event.left_sample, event.fraction, event.disposition,
                event.requested_start_sample, event.requested_end_sample_exclusive, event.holdoff_release_sample,
            ))
        else:
            window = event.window
            timeline.append(("ready", event.trigger.detection_sample, window.start_sample,
                             window.end_sample_exclusive, window.planes))
    return timeline


class IndependentOracleTests(unittest.TestCase):
    def test_all_short_callback_partitions_match_direct_tape_oracle(self):
        a = (-1, -0.25, 0.75, 0.5, -1, 1, -1, 1, -0.25, 1, -1, 1)
        b = (0, 1, 0, -1, 0, 0, -1, 1, 0, -0.25, 0, 0)
        c = (-1, 1) * 6
        scenarios = (
            (a, replace(RISING, pre_frames=2, post_frames=1, holdoff_frames=3)),
            (tuple(-x for x in a), replace(RISING, direction="falling", pre_frames=2, post_frames=1, holdoff_frames=4)),
            (c, replace(RISING, post_frames=2)),
            (c, replace(RISING, pre_frames=2, holdoff_frames=10)),
            (b, replace(RISING, hysteresis=0)),
            (tuple(-x for x in c), replace(RISING, direction="falling", pre_frames=4, post_frames=3, holdoff_frames=5)),
        )
        origin = 2**53 + 1
        epoch = replace(STEREO, origin_sample=origin)
        for scenario, (signal, settings) in enumerate(scenarios):
            tape = (signal, tuple(range(12)))
            expected = tape_oracle(tape, epoch, settings)
            for mask in range(2**11):
                boundaries = [0] + [i for i in range(1, 12) if mask & (1 << (i - 1))] + [12]
                scope = ScopeTrigger(epoch, settings)
                events = []
                for lo, hi in zip(boundaries, boundaries[1:]):
                    events.extend(ingest(scope, origin + lo, *(plane[lo:hi] for plane in tape)))
                self.assertEqual(flatten(events), expected, f"scenario={scenario}, breaks={mask}")
                self.assertEqual(scope.next_sample, origin + 12)


if __name__ == "__main__":
    unittest.main()
