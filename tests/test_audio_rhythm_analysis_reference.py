"""Timing, support, and ambiguity fixtures for exact rhythm measurements."""

from dataclasses import replace
from fractions import Fraction as F
import cmath
import math
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in (
    "audio-oscilloscope", "audio-stereo-correlation", "audio-spectrogram-waterfall",
    "audio-onset-detection", "audio-beat-tracking", "audio-rhythm-analysis",
):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_rhythm_analysis import (
    MAX_ANCHORS, MAX_EVENTS, Availability, BeatAnchor, BeatGridSegment, RhythmCapture,
    RhythmEvent, RhythmProfile, analyze_rhythm, beat_segments_from_track, event_from_onset,
)
from reference_beat_tracking import BeatProfile, estimate_tempo, track_beats
from reference_onset_detection import OnsetDetector, OnsetFrame, OnsetGrid, OnsetProfile
from reference_oscilloscope import MAX_SAMPLE_INDEX, ScopeEpoch


ORIGIN = 2**60 + 37
EPOCH = ScopeEpoch("fixture", ORIGIN, F(48000), "sample clock", "analysis tap", "FS", ("mono",))


def capture(end=72000, *, start=0, epoch=EPOCH):
    return RhythmCapture(epoch, epoch.origin_sample + start, epoch.origin_sample + end)


def position(sample, epoch):
    twice = 2 * F(sample)
    assert twice.denominator == 1
    return 2 * epoch.origin_sample + twice.numerator


def event(cap, offset, event_id="onset", voice="ride", *, offbeat=False, timing=Availability()):
    return RhythmEvent(event_id, voice, cap, position(offset, cap.epoch), timing, offbeat)


def grid(cap, offsets, *, prefix="anchor"):
    return BeatGridSegment(cap, tuple(
        BeatAnchor(f"{prefix}-{i}", position(v, cap.epoch)) for i, v in enumerate(offsets)
    ))


def ready(t=None, observed=None):
    return Availability(None if t is None else ORIGIN + t, None if observed is None else ORIGIN + observed)


class PhaseTests(unittest.TestCase):
    def test_local_phase_calibrates_straight_and_swung_events_at_changing_tempo(self):
        cap = capture()
        beats = grid(cap, (0, 24000, 45600, 69600))
        straight = (12000, 34800, 57600)
        swung = (16000, 38400, 61600)
        for offsets, phase, ratio in ((straight, F(1, 2), 1), (swung, F(2, 3), 2)):
            events = [event(cap, t, str(i), offbeat=True) for i, t in enumerate(offsets)]
            result = analyze_rhythm(events, [beats])
            self.assertEqual([r.phase for r in result.positions], [phase] * 3)
            self.assertEqual([r.bracket.beat_index for r in result.positions], [0, 1, 2])
            self.assertEqual([r.bracket.length_samples for r in result.positions], [24000, 21600, 24000])
            self.assertEqual([r.ratio for r in result.offbeats], [ratio] * 3)
            self.assertTrue(all(r.status == "mapped" for r in result.positions))

    def test_constant_grid_changes_the_ratio_at_the_same_events(self):
        cap = capture()
        steady = grid(cap, (0, 23200, 46400, 69600))
        for offsets, ratios in (
            ((12000, 34800, 57600), (F(15, 14), F(1), F(14, 15))),
            ((16000, 38400, 61600), (F(20, 9), F(19, 10), F(19, 10))),
        ):
            events = [event(cap, t, str(i), offbeat=True) for i, t in enumerate(offsets)]
            self.assertEqual(tuple(r.ratio for r in analyze_rhythm(events, [steady]).offbeats), ratios)

    def test_anchor_bias_changes_phase_and_signed_grid_residual(self):
        cap = capture()
        p = RhythmProfile((3,))
        result = analyze_rhythm([event(cap, 16000, offbeat=True)], [grid(cap, (0, 24240))], p)
        hit, = result.positions
        slot, = hit.fits[0].slots
        self.assertEqual(hit.phase, F(200, 303))
        self.assertEqual(result.offbeats[0].ratio, F(200, 103))
        self.assertEqual((slot.slot, slot.residual_samples), (2, -160))

    def test_half_open_ownership_at_shared_and_final_anchors(self):
        cap = capture()
        anchors = grid(cap, (5, 24000, 45600, 69600))
        times = (0, 24000, 69600, 69601)
        result = analyze_rhythm([event(cap, t, str(i)) for i, t in enumerate(times)], [anchors])
        self.assertEqual([r.status for r in result.positions],
                         ["outside_grid", "mapped", "no_right_anchor", "outside_grid"])
        exact = result.positions[1]
        self.assertEqual(exact.phase, 0)
        self.assertEqual(exact.bracket.left, anchors.anchors[1])
        self.assertEqual(exact.bracket.right, anchors.anchors[2])
        self.assertEqual(result.grids[0].eligible_events, 1)

    def test_touching_segments_can_share_the_boundary_anchor(self):
        cap = capture()
        full = grid(cap, (0, 100, 200))
        left = BeatGridSegment(cap, full.anchors[:2])
        right = BeatGridSegment(cap, full.anchors[1:])
        actual = analyze_rhythm([event(cap, 100)], [right, left]).positions[0]
        self.assertEqual(actual.phase, 0)
        self.assertEqual((actual.bracket.left, actual.bracket.right), full.anchors[1:])

    def test_anchors_can_close_a_capture_at_its_exclusive_end(self):
        cap = capture(100)
        segment = grid(cap, (0, 100))
        result = analyze_rhythm([event(cap, F(199, 2))], [segment], RhythmProfile((2,), F(1, 2)))
        mapped, = result.positions
        self.assertEqual(mapped.phase, F(199, 200))
        self.assertEqual(mapped.fits[0].slots[0].residual_samples, F(-1, 2))
        with self.assertRaises(ValueError):
            event(cap, 100)

    def test_gap_between_segments_is_unavailable_even_in_one_epoch(self):
        cap = capture()
        a = grid(cap, (0, 100), prefix="a")
        b = grid(cap, (300, 400), prefix="b")
        positions = analyze_rhythm(
            [event(cap, 100, "last"), event(cap, 200, "gap"), event(cap, 300, "resume")], [a, b],
        ).positions
        self.assertEqual([r.status for r in positions], ["no_right_anchor", "beat_gap", "mapped"])
        self.assertEqual(positions[-1].phase, 0)

    def test_same_coordinates_in_two_epochs_do_not_share_anchors(self):
        old = capture()
        new = capture(epoch=replace(EPOCH, epoch_id="after seek"))
        events = [event(old, 50, "old"), event(new, 50, "new")]
        result = analyze_rhythm(events, [grid(old, (0, 100))])
        self.assertEqual([r.status for r in result.positions], ["mapped", "no_grid"])
        self.assertEqual(result.intervals, ())

    def test_inferred_and_predicted_anchor_policy_preserves_provenance(self):
        cap = capture()
        full = grid(cap, (0, 100))
        later = full.anchors[1]
        events = [event(cap, 50, offbeat=True)]
        inferred = BeatGridSegment(cap, (full.anchors[0], replace(later, kind="inferred")))
        accepted = analyze_rhythm(events, [inferred])
        self.assertEqual(accepted.positions[0].phase, F(1, 2))
        strict = analyze_rhythm(events, [inferred], RhythmProfile(allow_inferred_anchors=False))
        self.assertEqual(strict.positions[0].status, "inferred_anchor")
        self.assertEqual(strict.positions[0].bracket.right.kind, "inferred")
        self.assertIsNone(strict.positions[0].phase)
        self.assertEqual(strict.offbeats[0].status, "phase_unavailable")
        predicted = BeatGridSegment(cap, (full.anchors[0], replace(later, kind="predicted")))
        pending = analyze_rhythm(events, [predicted]).positions[0]
        self.assertEqual(pending.status, "predicted_anchor")
        self.assertEqual(pending.bracket.right.kind, "predicted")
        self.assertEqual((pending.fits, pending.timing), ((), Availability()))

    def test_timing_uses_all_three_inputs_and_keeps_observed_boundary(self):
        cap = capture()
        beats = BeatGridSegment(cap, (
            BeatAnchor("left", position(100, EPOCH), timing=ready(170, 300)),
            BeatAnchor("right", position(200, EPOCH), timing=ready(250, 350)),
        ))
        supplied = [event(cap, 150, "one", timing=ready(210, 340)),
                    event(cap, 180, "two", timing=ready(280, 360))]
        result = analyze_rhythm(supplied, [beats])
        self.assertEqual([p.timing for p in result.positions], [ready(250, 350), ready(280, 360)])
        self.assertEqual(result.intervals[0].timing, ready(280, 360))
        partial = replace(beats, anchors=(beats.anchors[0], replace(beats.anchors[1], timing=ready(None, 355))))
        result = analyze_rhythm(supplied, [partial])
        self.assertEqual([p.timing for p in result.positions], [ready(None, 355), ready(None, 360)])
        no_actual = replace(supplied[0], timing=ready(210))
        self.assertEqual(analyze_rhythm([no_actual], [beats]).positions[0].timing, ready(250))

    def test_swing_requires_one_labelled_interior_event_per_voice_and_beat(self):
        cap = capture()
        given = [
            event(cap, 50, "drum-a", offbeat=True), event(cap, 65, "drum-b", offbeat=True),
            event(cap, 60, "bass", "bass", offbeat=True), event(cap, 100, "edge", offbeat=True),
            event(cap, 205, "unavailable", offbeat=True), event(cap, 150, "unlabelled", "bass"),
        ]
        result = analyze_rhythm(given, [grid(cap, (0, 100, 200))])
        self.assertEqual([(x.event.event_id, x.status, x.ratio) for x in result.offbeats], [
            ("drum-a", "ambiguous_offbeat", None), ("drum-b", "ambiguous_offbeat", None),
            ("bass", "measured", F(3, 2)), ("edge", "endpoint", None),
            ("unavailable", "phase_unavailable", None),
        ])


class GridTests(unittest.TestCase):
    def test_near_right_endpoint_keeps_phase_and_uses_next_anchor_slot_zero(self):
        cap = capture()
        items = [event(cap, 24000-F(1, 2), "early"), event(cap, 24000, "exact")]
        segment = grid(cap, (0, 24000, 45600))
        result = analyze_rhythm(items, [segment], RhythmProfile((4,), F(1, 2)))
        early, exact = result.positions
        self.assertEqual(float(items[0].sample_twice), float(items[1].sample_twice))
        self.assertEqual(early.phase, F(47999, 48000))
        slot, = early.fits[0].slots
        self.assertEqual((slot.anchor, slot.slot), (exact.bracket.left, 0))
        self.assertEqual(slot.position_sample_twice, exact.event.sample_twice)
        self.assertEqual((slot.residual_samples, slot.residual_beats), (F(-1, 2), F(-1, 48000)))
        self.assertTrue(early.fits[0].matched)
        evidence, = result.grids
        self.assertEqual(evidence.hits_by_slot, (2, 0, 0, 0))
        self.assertEqual(evidence.distinct_beats_by_slot, (1, 0, 0, 0))

    def test_equal_distance_retains_two_residuals_and_counts_one_match(self):
        cap = capture()
        result = analyze_rhythm(
            [event(cap, 6000)], [grid(cap, (0, 24000))], RhythmProfile((2,), 6000)
        )
        fit, = result.positions[0].fits
        self.assertEqual([(s.slot, s.residual_samples) for s in fit.slots], [(0, 6000), (1, -6000)])
        self.assertTrue(fit.matched)
        evidence, = result.grids
        self.assertEqual((evidence.eligible_events, evidence.matched_events, evidence.tied_matches), (1, 1, 1))
        self.assertEqual(evidence.hits_by_slot, (0, 0))
        self.assertEqual(evidence.distinct_beats_by_slot, (0, 0))
        self.assertEqual(evidence.absolute_residual_samples, (6000,))

    def test_fractional_slots_remain_unrounded(self):
        cap = capture()
        segment = grid(cap, (50, F(105, 2)))
        output = analyze_rhythm([event(cap, F(101, 2))], [segment], RhythmProfile((3,), F(1, 3)))
        fit, = output.positions[0].fits
        slot, = fit.slots
        self.assertEqual(slot.position_sample_twice, 2*ORIGIN + F(305, 3))
        self.assertEqual(slot.residual_samples, F(-1, 3))
        self.assertEqual(slot.residual_beats, F(-2, 15))
        self.assertTrue(fit.matched)

    def test_tolerance_units_are_inclusive_and_track_distinct_lengths(self):
        cap = capture()
        specified = [event(cap, 11760, "a"), event(cap, 34584, "b")]
        segment = grid(cap, (0, 24000, 45600))
        result = analyze_rhythm(specified, [segment], RhythmProfile((2,), F(1, 100), "beats"))
        evidence, = result.grids
        self.assertEqual(evidence.absolute_residual_beats, (F(1, 100), F(1, 100)))
        self.assertEqual(evidence.absolute_residual_samples, (240, 216))
        self.assertEqual(evidence.matched_events, 2)
        samples = analyze_rhythm(specified, [segment], RhythmProfile((2,), 216, "samples"))
        self.assertEqual([r.fits[0].matched for r in samples.positions], [False, True])

    def test_denser_grid_fit_keeps_coverage_and_slot_support(self):
        cap = capture(410000)
        segment = grid(cap, tuple(i * 24000 for i in range(17)))
        items = [event(cap, 12000 + i * 24000, str(i)) for i in range(16)]
        items.append(event(cap, 3 * 24000 + 6000, "quarter"))
        comparison = analyze_rhythm(items, [segment], RhythmProfile((2, 4)))
        coarse, fine = comparison.grids
        self.assertEqual((coarse.eligible_events, fine.eligible_events), (17, 17))
        self.assertEqual((coarse.matched_events, fine.matched_events), (16, 17))
        self.assertEqual(coarse.distinct_beats_by_slot, (0, 16))
        self.assertEqual(fine.distinct_beats_by_slot, (0, 1, 16, 0))

    def test_grid_assignments_agree_with_exhaustive_integer_distances(self):
        rng = random.Random(381126)
        cap = capture(100000)
        for _ in range(176):
            start = F(rng.randrange(0, 19000), 2)
            width = rng.randrange(1, 72000)
            ticks = rng.randrange(width)
            q = rng.randrange(1, 65)
            segment = grid(cap, (start, start + F(width, 2)))
            actual = analyze_rhythm(
                [event(cap, start + F(ticks, 2))], [segment], RhythmProfile((q,))
            ).positions[0]
            distances = [q*ticks - k*width for k in range(q+1)]
            closest = min(map(abs, distances))
            expected = [(k % q, F(v, 2*q)) for k, v in enumerate(distances) if abs(v) == closest]
            self.assertEqual([(x.slot, x.residual_samples) for x in actual.fits[0].slots], expected)
            self.assertEqual(actual.phase, F(ticks, width))

    def test_directed_ties_include_next_beat_at_a_large_origin(self):
        cap = capture()
        for q in range(1, 33):
            for k in (0, q-1):
                segment = grid(cap, (50, 50+11*q))
                t = 50 + F((2*k+1)*11, 2)
                result = analyze_rhythm([event(cap, t)], [segment], RhythmProfile((q,), F(11, 2)))
                slots = result.positions[0].fits[0].slots
                self.assertEqual([s.residual_samples for s in slots], [F(11, 2), F(-11, 2)])
                self.assertEqual(slots[-1].anchor, segment.anchors[int(k+1==q)])

    def test_duration_and_residual_units_scale_on_the_sample_clock(self):
        pair = []
        for factor in (1, 2):
            ep = replace(EPOCH, rate_hz=EPOCH.rate_hz * factor)
            cap = capture(72000 * factor, epoch=ep)
            segment = grid(cap, (0, 24000 * factor, 45600 * factor))
            events = [event(cap, t*factor, str(i)) for i, t in enumerate((11760, 34584))]
            pair.append(analyze_rhythm(events, [segment], RhythmProfile((2,), F(1, 100), "beats")))
        a, b = pair
        self.assertEqual(a.intervals[0].seconds, b.intervals[0].seconds)
        self.assertEqual(b.intervals[0].samples, 2*a.intervals[0].samples)
        self.assertEqual([p.phase for p in a.positions], [p.phase for p in b.positions])
        self.assertEqual(a.grids[0].absolute_residual_beats, b.grids[0].absolute_residual_beats)
        self.assertEqual(tuple(2*v for v in a.grids[0].absolute_residual_samples),
                         b.grids[0].absolute_residual_samples)


class IntervalAndInputTests(unittest.TestCase):
    def test_voice_scoped_stable_zero_interval_and_capture_break(self):
        cap = capture(350)
        after_gap = capture(900, start=500)
        events = [
            event(cap, 150, "late", timing=ready(200, 201)),
            event(cap, 50, "r0", timing=ready(100, 130)),
            event(cap, 60, "k0", "kick"), event(cap, 50, "r1", timing=ready(120, 150)),
            event(after_gap, 700, "r2"),
        ]
        result = analyze_rhythm(events, [])
        self.assertEqual([p.event for p in result.positions], events)
        self.assertEqual([(x.earlier.event_id, x.later.event_id, x.samples) for x in result.intervals],
                         [("r0", "r1", 0), ("r1", "late", 100)])
        self.assertEqual([x.timing for x in result.intervals], [ready(120, 150), ready(200, 201)])
        self.assertEqual(result.intervals[1].seconds, F(1, 480))

    def test_empty_inputs_keep_declared_grid_counts(self):
        result = analyze_rhythm([], [], RhythmProfile((2, 3)))
        self.assertEqual(result.positions, ())
        self.assertEqual(result.intervals, ())
        self.assertEqual([r.eligible_events for r in result.grids], [0, 0])

    def test_reject_conflicting_clock_and_overlapping_captures(self):
        a = capture(250)
        for other in (
            capture(300, start=100),
            capture(500, start=300, epoch=replace(EPOCH, tap_id="other tap")),
            capture(500, start=300, epoch=replace(EPOCH, rate_hz=F(44100))),
        ):
            with self.subTest(other=other), self.assertRaises(ValueError):
                analyze_rhythm([event(a, 110, "one"), event(other, other.start_sample-ORIGIN, "two")], [])

    def test_reject_grid_overlap_duplicate_start_and_conflicting_anchor_identity(self):
        cap = capture()
        left = grid(cap, (0, 100), prefix="L")
        for second in (
            grid(cap, (99, 200), prefix="R"), grid(cap, (0,), prefix="R"), grid(cap, (200, 300), prefix="L"),
        ):
            for segments in ([left, second], [second, left]):
                with self.subTest(segments=segments), self.assertRaises(ValueError):
                    analyze_rhythm([], segments)

    def test_reject_invalid_times_records_and_profile(self):
        cap = capture(200)
        valid = event(cap, 100)
        cases = (
            lambda: Availability(True), lambda: ready(100, 99), lambda: Availability(None, MAX_SAMPLE_INDEX+1),
            lambda: replace(valid, sample_twice=1.0), lambda: replace(valid, offbeat=1),
            lambda: replace(valid, voice=" "), lambda: replace(valid, timing=Availability(ORIGIN-1)),
            lambda: grid(cap, (5, 5)), lambda: grid(cap, (6, 5)), lambda: grid(cap, (0, 201)),
            lambda: BeatGridSegment(cap, []), lambda: BeatAnchor("x", 0, "unknown"),
            lambda: RhythmProfile((2, 2)), lambda: RhythmProfile((0,)), lambda: RhythmProfile((True,)),
            lambda: RhythmProfile((65,)), lambda: RhythmProfile(tolerance=-1),
            lambda: RhythmProfile(tolerance=math.nan), lambda: RhythmProfile(tolerance_units="ms"),
            lambda: RhythmProfile(allow_inferred_anchors=1),
            lambda: analyze_rhythm([valid, valid], []),
            lambda: analyze_rhythm([valid] * (MAX_EVENTS+1), []),
            lambda: analyze_rhythm([], [grid(cap, (0, 100))] * (MAX_ANCHORS//2+1)),
        )
        for i, case in enumerate(cases):
            with self.subTest(case=i), self.assertRaises(ValueError):
                case()


class IntegrationTests(unittest.TestCase):
    @staticmethod
    def impulse_run(count, pulse_frames):
        m, hop = 960, 480
        window = tuple((1-math.cos(math.tau*j/m))/2 for j in range(m))
        grid = OnsetGrid(EPOCH, window, m, hop)
        detector = OnsetDetector(grid, OnsetProfile(right=2, background=4, margin=.01))
        mass = math.fsum(window)
        norm = math.sqrt(math.fsum(w*w for w in window))
        samples = [frame*hop+480 for frame in pulse_frames]
        end = (count-1)*hop+m
        cap = capture(end+480)
        events, points = [], []
        for j in range(count):
            start = j*hop
            w = sum(window[i-start] for i in samples if start <= i < start+m)
            a = w/mass
            bins = (a,) + (2*a,) * (m//2-1) + (a,)
            frame = OnsetFrame(grid, ORIGIN+start, ORIGIN+start+m, bins, w/norm)
            novelty, onset = detector.push(frame, observed_release_sample_exclusive=ORIGIN+start+m+120)
            points.append(novelty)
            if onset:
                events.append(onset)
        run = track_beats(points, BeatProfile(100*hop), period_frames=50,
                          observed_release_sample_exclusive=ORIGIN+end+480)
        return cap, points, events, run

    def test_merged_beat_segments_preserve_the_long_ioi_without_a_beat_phase(self):
        cap, points, onsets, track = self.impulse_run(400, (20, 70, 120, 320, 370))
        grids = beat_segments_from_track(track, cap)
        events = [event_from_onset(onset, cap, str(i), "ride") for i, onset in enumerate(onsets)]
        probe = RhythmEvent("quiet-probe", "second voice", cap, points[170].center_sample_twice)
        self.assertEqual([(s.first_frame_index, s.last_frame_index) for s in track.segments], [(20, 120), (320, 370)])
        self.assertEqual([len(x.anchors) for x in grids], [3, 2])
        result = analyze_rhythm(events+[probe], grids)
        self.assertEqual([x.samples for x in result.intervals], [24000, 24000, 96000, 24000])
        self.assertEqual(result.intervals[2].seconds, 2)
        self.assertEqual(result.positions[-1].status, "beat_gap")
        self.assertEqual(points[170].flux, 0)

    def test_merged_onset_and_beat_adapters_keep_whole_run_boundary_and_inference(self):
        cap, _, onsets, track = self.impulse_run(350, (7, 57, 107, 207, 257, 307))
        segment, = beat_segments_from_track(track, cap)
        self.assertEqual((len(onsets), len(segment.anchors)), (6, 7))
        first = event_from_onset(onsets[0], cap, "first", "ride")
        middle = RhythmEvent("between", "ride", cap,
                             (segment.anchors[2].sample_twice + segment.anchors[3].sample_twice)//2,
                             ready(90000, 90001), True)
        result = analyze_rhythm([first, middle], [segment])
        self.assertEqual(first.timing, ready(5280, 5400))
        self.assertEqual(result.positions[0].timing, ready(168480, 168960))
        self.assertEqual((result.positions[0].event.sample_twice, result.positions[0].phase), (2*ORIGIN+7679, 0))
        self.assertEqual(result.positions[1].phase, F(1, 2))
        self.assertEqual(result.positions[1].bracket.right.kind, "inferred")
        self.assertEqual(result.offbeats[0].ratio, 1)
        strict = analyze_rhythm([middle], [segment], RhythmProfile(allow_inferred_anchors=False))
        self.assertEqual(strict.positions[0].status, "inferred_anchor")

    def test_timing_adapters_require_the_mapped_source_clock(self):
        _, _, onsets, track = self.impulse_run(120, (7, 57, 107))
        other = capture(70000, epoch=replace(EPOCH, tap_id="unmapped"))
        with self.assertRaises(ValueError):
            event_from_onset(onsets[0], other, "first", "ride")
        with self.assertRaises(ValueError):
            beat_segments_from_track(track, other)

    def test_periodicity_fixture_has_multiple_valid_rate_hypotheses(self):
        values = [int((j-7) % 50 == 0) for j in range(800)]
        evidence = estimate_tempo(values, 100)
        by_lag = {row.lag_frames: row for row in evidence.lags}
        self.assertEqual([by_lag[p].raw_sum for p in (25, 50, 100)], [0, 15, 14])
        self.assertEqual(by_lag[50].mean_product, by_lag[100].mean_product)
        self.assertEqual(evidence.evidence_best_lags, (50, 100))
        for magnitude, window in ((16, [1.0]*800), (8, [.5-.5*math.cos(math.tau*j/800) for j in range(800)])):
            for hz in (2, 4):
                coeff = sum(v*w*cmath.exp(-1j*math.tau*hz*j/100)
                            for j, (v, w) in enumerate(zip(values, window)))
                self.assertAlmostEqual(abs(coeff), magnitude, delta=1e-12)
