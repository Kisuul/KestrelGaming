"""Portable verification of tempo evidence, phase, beat paths, and clock support."""

from dataclasses import replace
from fractions import Fraction as F
from itertools import combinations
import math
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in (
    "audio-oscilloscope", "audio-stereo-correlation", "audio-spectrogram-waterfall",
    "audio-onset-detection", "audio-beat-tracking",
):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_beat_tracking import (
    MAX_FEATURE_FRAMES, BeatProfile, TempoPrior, TempoSearch, align_beats, estimate_tempo,
    phase_scores, track_beats,
)
from reference_onset_detection import (
    NoveltyPoint, OnsetDetector, OnsetFrame, OnsetGrid, OnsetProfile, match_onsets,
)
from reference_oscilloscope import ScopeEpoch


ORIGIN = 2**60 + 37
HOP = 480


def pulses(length, positions):
    values = [0] * length
    for position in positions:
        values[position] = 1
    return values


def selected_phase(values, period):
    return max(phase_scores(values, period), key=lambda item: item.score).offset_frames


def epoch(epoch_id="fixture-A"):
    return ScopeEpoch(epoch_id, ORIGIN, F(48000), "sample clock", "analysis tap", "FS", ("mono",))


def injected_points(values):
    """Inject controlled novelty values after one frame of comparison support."""
    grid = OnsetGrid(epoch(), (1.0,) * HOP, HOP, HOP)
    onset_profile = OnsetProfile()
    points = []
    for i, value in enumerate(values, 1):
        start = ORIGIN + i * HOP
        frame = OnsetFrame(grid, start, start + HOP, (0.0,) * grid.bin_count, 0.0)
        if value is None:
            points.append(NoveltyPoint(frame, onset_profile, None, None, None, ()))
        else:
            points.append(NoveltyPoint(frame, onset_profile, start - HOP, F(value), F(0), ()))
    return points


def matched(ref, estimates, length):
    first = 2 * ORIGIN + HOP - 1
    to_ticks = lambda frames: [first + 2 * HOP * i for i in frames]
    return match_onsets(
        to_ticks(ref), to_ticks(estimates), tolerance_sample_twice=6720,
        eligible_interval_twice=(first, first + 2 * HOP * length),
    )


class TempoEvidenceTests(unittest.TestCase):
    def test_same_tempo_distinct_phase(self):
        left = pulses(800, range(7, 800, 50))
        right = pulses(800, range(31, 800, 50))
        search = TempoSearch(minimum_bpm=F(6000, 129), maximum_bpm=6000, aggregation="sum")
        evidence = [estimate_tempo(v, 100, search) for v in (left, right)]
        self.assertEqual(evidence[0], evidence[1])
        self.assertEqual(len(evidence[0].lags), 129)
        self.assertEqual(evidence[0].selected.lag.bpm, 120)
        self.assertEqual([selected_phase(v, 50) for v in (left, right)], [7, 31])

    def test_phase_sums_use_equal_support(self):
        values = [1, 2, 0, 1, 2, 0, 30]
        self.assertEqual([(v.offset_frames, v.count, v.score) for v in phase_scores(values, 3)],
                         [(0, 2, 2), (1, 2, 4), (2, 2, 0)])
        self.assertEqual(phase_scores(values[:2], 3), ())

    def test_harmonic_tie_retained_and_prior_disclosed(self):
        values = pulses(800, range(7, 800, 25))
        estimate = estimate_tempo(values, 100)
        self.assertEqual(estimate.status, "ambiguous")
        self.assertIsNone(estimate.selected)
        self.assertEqual(estimate.evidence_best_lags, (25, 50, 75, 100))
        self.assertEqual([c.lag.raw_sum for c in estimate.candidates], [31, 30, 29, 28])
        self.assertEqual([c.lag.pairs for c in estimate.candidates], [775, 750, 725, 700])
        self.assertTrue(all(c.lag.mean_product == F(1, 25) for c in estimate.candidates))
        for bpm in (240, 120, 60):
            with self.subTest(center=bpm):
                search = TempoSearch(prior=TempoPrior(bpm, F(1, 2)))
                result = estimate_tempo(values, 100, search)
                self.assertEqual(result.status, "prior_selected")
                self.assertEqual(result.selected.lag.bpm, bpm)
                self.assertEqual(result.evidence_best_lags, (25, 50, 75, 100))

    def test_prior_can_change_a_unique_evidence_winner(self):
        values = pulses(800, range(7, 800, 25))
        search = TempoSearch(aggregation="sum")
        self.assertEqual(estimate_tempo(values, 100, search).selected.lag.bpm, 240)
        changed = estimate_tempo(values, 100, replace(search, prior=TempoPrior(60, F(1, 2))))
        self.assertEqual(changed.status, "prior_selected")
        self.assertEqual(changed.evidence_best_lags, (25,))
        self.assertEqual(changed.selected.lag.bpm, 60)

    def test_prior_cannot_select_a_flat_floor_or_a_nonpeak_plateau(self):
        flat = estimate_tempo([2] * 80, 100, TempoSearch(prior=TempoPrior(120, 1)))
        self.assertEqual(flat.status, "flat_input")
        self.assertIsNone(flat.selected)
        self.assertTrue(all(lag.mean_product == 4 for lag in flat.lags))
        # Raw sums at lags 1 through 8 are [2,1,1,1,2,1,1,1].
        values = [1, 0, 1, 1, 0, 0, 0, 1, 1]
        search = TempoSearch(F(6000, 8), 6000, 1, 1, False, "sum", TempoPrior(2000, F(1, 8)))
        estimate = estimate_tempo(values, 100, search)
        self.assertEqual([c.lag.lag_frames for c in estimate.candidates], [5, 1])

    def test_flat_positive_lag_curve_cannot_become_a_prior_driven_period(self):
        search = TempoSearch(3000, 6000, 1, 1, False, "mean", TempoPrior(6000, 1))
        estimate = estimate_tempo([1, 0, 3, 2], 100, search)
        self.assertEqual([row.mean_product for row in estimate.lags], [2, F(3, 2)])
        estimate = estimate_tempo([1, 0, 2, F(3, 2)], 100, search)
        self.assertEqual([row.mean_product for row in estimate.lags], [1, 1])
        self.assertEqual(estimate.status, "flat_scores")
        self.assertIsNone(estimate.selected)

    def test_alternating_accents_favor_slower_level(self):
        values = [0] * 1600
        for i, t in enumerate(range(20, 1600, 50)):
            values[t] = 1 if i % 2 == 0 else F(1, 4)
        estimate = estimate_tempo(values, 100)
        lags = {r.lag_frames: r for r in estimate.lags}
        self.assertEqual(lags[50].mean_product, F(1, 200))
        self.assertEqual(lags[100].mean_product, F(17, 1600))
        self.assertEqual(estimate.selected.lag.bpm, 60)

    def test_linear_correlation_edge_contributions_and_overlap(self):
        values = pulses(64, [0, 63])
        search = TempoSearch(90, 6000, minimum_pairs=2, minimum_intervals=1)
        result = estimate_tempo(values, 100, search)
        rows = {lag.lag_frames: lag for lag in result.lags}
        self.assertEqual(rows[1].raw_sum, 0)
        self.assertEqual((rows[63].pairs, rows[63].mean_product), (1, 1))
        self.assertFalse(rows[63].eligible)
        self.assertEqual(result.status, "no_positive_peak")

    def test_mean_removal_uses_the_declared_run(self):
        search = TempoSearch(1200, 6000, 1, 1, remove_mean=True)
        a = estimate_tempo([0, 2, 0, 2, 0, 2], 100, search)
        b = estimate_tempo([10, 12, 10, 12, 10, 12], 100, search)
        self.assertEqual(a, b)
        self.assertEqual([lag.raw_sum for lag in a.lags[:2]], [-5, 4])

    def test_exact_bpm_limits_and_minimum_intervals(self):
        values = [1, 0, 1, 0, 1]
        rate = F(101, 2)
        search = TempoSearch(F(3030, 3), F(3030, 2), 1, 2)
        evidence = estimate_tempo(values, rate, search)
        self.assertEqual([r.lag_frames for r in evidence.lags], [2, 3])
        self.assertEqual([r.complete_intervals for r in evidence.lags], [2, 1])
        self.assertEqual(evidence.selected.lag.bpm, 1515)
        self.assertEqual(estimate_tempo([1, 0, 1], rate, search).status, "insufficient_support")
        self.assertEqual(estimate_tempo(values, rate, replace(search, minimum_bpm=1011)).lags[-1].lag_frames, 2)

    def test_ranking_extreme_rational_strengths_stays_finite(self):
        values = [F(10)**400 * v for v in pulses(800, range(7, 800, 25))]
        estimate = estimate_tempo(values, 100, TempoSearch(prior=TempoPrior(F(1, 10**400), F(1, 10**400))))
        self.assertEqual(estimate.status, "prior_selected")
        self.assertEqual(estimate.selected.lag.bpm, 60)
        self.assertGreater(estimate.selected.evidence, F(10)**790)

    def test_reject_invalid_period_search_inputs(self):
        cases = (
            lambda: estimate_tempo([0, math.nan], 100),
            lambda: estimate_tempo([0, -1], 100),
            lambda: estimate_tempo([0, True], 100),
            lambda: estimate_tempo([1], 0),
            lambda: estimate_tempo([0] * (MAX_FEATURE_FRAMES + 1), 100),
            lambda: TempoSearch(150, 100),
            lambda: TempoSearch(minimum_pairs=0),
            lambda: TempoSearch(minimum_intervals=True),
            lambda: TempoSearch(aggregation="median"),
            lambda: TempoPrior(120, math.inf),
            lambda: TempoPrior(120, 0),
            lambda: phase_scores([1, 0], True),
        )
        for i, case in enumerate(cases):
            with self.subTest(case=i), self.assertRaises(ValueError):
                case()


class SequenceTests(unittest.TestCase):
    def test_missing_beat_syncopation_and_gain_scale(self):
        ideal = tuple(range(20, 400, 50))
        values = pulses(400, ideal)
        values[170], values[145], values[245] = 0, F(4, 5), F(7, 10)
        path = align_beats(values, 50)
        self.assertEqual((path.indices, path.score), (ideal, 7))
        boosted = [10 * v for v in values]
        changed = align_beats(boosted, 50)
        self.assertEqual(set(changed.indices) - set(ideal), {145})
        self.assertEqual(set(ideal) - set(changed.indices), {170})
        restored = align_beats(boosted, 50, interval_penalty=80)
        self.assertEqual((restored.indices, restored.score), (ideal, 70))

    def test_earliest_ties_and_strictly_positive_continuation(self):
        self.assertEqual(align_beats([1, 1, 1, 1], 2).indices, (0, 2))
        self.assertEqual(align_beats([1, 1, 0, 1], 3, interval_penalty=0).indices, (0, 3))
        self.assertEqual(align_beats([0, 1], 1, interval_penalty=0).indices, (1,))
        self.assertEqual(align_beats([0] * 10, 2).indices, ())

    def test_fractional_period_bounds_are_inclusive_and_use_arriving_node(self):
        self.assertEqual(align_beats([5, 0, 4], [9, 9, F(3, 2)], interval_penalty=0).indices, (0, 2))
        prior_bound = align_beats([5, 0, 4], [F(3, 2), F(3, 2), 9], interval_penalty=0)
        self.assertEqual(prior_bound.indices, (0,))
        self.assertEqual(align_beats([2, 0, 3], 4, interval_penalty=0).indices, (0, 2))
        self.assertEqual(align_beats([2, 0, 3], 1, interval_penalty=0).indices, (0, 2))
        # The direct long edge has the earliest predecessor on a score tie.
        values = [4] + [0] * 4 + [4]
        self.assertEqual(align_beats(values, F(5, 2), interval_penalty=0).indices, (0, 5))
        self.assertEqual(align_beats([4, 10, 4], F(5, 2), interval_penalty=0).indices, (1,))

    def test_path_total_depends_on_tempo_level(self):
        values = pulses(800, range(7, 800, 25))
        scores = [float(align_beats(values, period).score) for period in (25, 50, 100)]
        self.assertEqual(scores[:2], [32, 16])
        self.assertAlmostEqual(scores[2], 9 - 8 * math.log(0.75)**2, delta=4e-15)

    def test_supplied_tempo_change_is_a_path_test(self):
        first = list(range(20, 600, 60))
        second = list(range(600, 1200, 40))
        labels = first + second
        values = pulses(1200, labels)
        mild = TempoSearch(60, 200, aggregation="sum")
        self.assertEqual([estimate_tempo(v, 100, mild).selected.lag.bpm
                          for v in (values[:600], values[600:])], [100, 150])
        adapted = align_beats(values, [60] * 600 + [40] * 600)
        self.assertEqual(adapted.indices, tuple(labels))
        held = matched(labels, align_beats(values, 60).indices, 1200)
        self.assertEqual((held.true_positives, held.false_positives, held.false_negatives), (15, 5, 10))
        self.assertEqual(held.f1, F(2, 3))

    def test_prefix_cannot_determine_which_offline_phase_will_win(self):
        leading = list(range(10, 200, 25))
        a = pulses(300, leading + [210, 260])
        b = pulses(300, leading + [235, 285])
        self.assertEqual(phase_scores(a[:200], 50), phase_scores(b[:200], 50))
        self.assertEqual([selected_phase(v, 50) for v in (a, b)], [10, 35])

    def test_path_agrees_with_exhaustive_objective(self):
        def score(indices, values, periods, weight):
            edges = [(t - s, periods[t]) for s, t in zip(indices, indices[1:])]
            if any(not period <= 2 * delta <= 4 * period for delta, period in edges):
                return -math.inf
            return math.fsum(values[i] for i in indices) - weight * math.fsum(
                math.log(delta / period)**2 for delta, period in edges
            )

        rng = random.Random(370037)
        subsets = [indices for n in range(10) for indices in combinations(range(9), n)]
        for case in range(176):
            values = [F(rng.randrange(8), 4) for _ in range(9)]
            periods = [F(rng.randint(3, 8), 2) for _ in range(9)]
            weight = (0, 3, 8)[case % 3]
            actual = align_beats(values, periods, interval_penalty=weight)
            expected = max(score(path, values, periods, weight) for path in subsets)
            self.assertAlmostEqual(float(actual.score), expected, delta=3e-15)
            self.assertAlmostEqual(float(actual.score), score(actual.indices, values, periods, weight),
                                   delta=3e-15)

    def test_invalid_period_inputs_are_rejected(self):
        for p, penalty in ((0, 8), (math.inf, 8), (True, 8), ([1], 8), (F(1, 2), 8),
                           (MAX_FEATURE_FRAMES + 1, 8), (2, -1)):
            with self.subTest(period=p, penalty=penalty), self.assertRaises(ValueError):
                align_beats([1, 2], p, interval_penalty=penalty)


class ClockAndSupportTests(unittest.TestCase):
    def test_elapsed_support_cap_prevents_long_quiet_bridge(self):
        sources = [20, 70, 120, 320, 370]
        values = pulses(400, sources)
        self.assertEqual(align_beats(values, 50).indices, tuple(range(20, 400, 50)))
        result = track_beats(injected_points(values), BeatProfile(100 * HOP), period_frames=50)
        self.assertEqual([(s.first_frame_index, s.last_frame_index) for s in result.segments],
                         [(21, 121), (321, 371)])
        self.assertEqual([b.frame_index - 1 for s in result.segments for b in s.beats], sources)

    def test_elapsed_limit_is_inclusive_and_splits_true_gaps(self):
        sources = [20, 70, 120, 220, 270, 320, 370]
        values = pulses(400, sources)
        points = injected_points(values)
        profile = BeatProfile(100 * HOP)
        same = track_beats(points, profile, period_frames=50)
        self.assertEqual(len(same.segments), 1)
        self.assertEqual([b.frame_index for b in same.segments[0].beats if not b.supported], [171])
        lower = replace(profile, maximum_support_gap_samples=100 * HOP - 1)
        unavailable = injected_points(values[:170] + [None] + values[171:])
        for run in (
            track_beats(points, lower, period_frames=50),
            track_beats(unavailable, profile, period_frames=50),
            track_beats(points[:170] + points[171:], profile, period_frames=50),
        ):
            self.assertEqual([(s.first_frame_index, s.last_frame_index) for s in run.segments],
                             [(21, 121), (221, 371)])
            self.assertTrue(all(b.supported for s in run.segments for b in s.beats))

    def test_a_strong_to_strong_transition_can_skip_the_entire_gap(self):
        values = [4] + [0] * 99 + [4]
        # The direct edge is admissible and worth more than a restart.
        direct = 8 - 8 * math.log(2)**2
        self.assertGreater(direct, 4)
        result = track_beats(injected_points(values), BeatProfile(90 * HOP), period_frames=50)
        self.assertEqual([s.status for s in result.segments], ["isolated", "isolated"])
        self.assertEqual([s.first_frame_index for s in result.segments], [1, 101])
        self.assertTrue(all(not s.beats for s in result.segments))

    def test_supported_floor_and_insufficient_alignment_status(self):
        points = injected_points([F(1, 2), 1, F(1, 2), 1, F(1, 2)])
        profile = BeatProfile(10 * HOP, support_floor=F(1, 2))
        anchored = track_beats(points, profile, period_frames=2)
        segment, = anchored.segments
        self.assertEqual((segment.first_frame_index, segment.last_frame_index), (2, 4))
        self.assertEqual([b.frame_index for b in segment.beats], [2, 4])
        far = track_beats(points, profile, period_frames=10)
        self.assertEqual(far.segments[0].status, "insufficient_alignment")
        self.assertEqual(far.segments[0].path.indices, (0,))
        self.assertEqual(far.segments[0].beats, ())
        silence = track_beats(injected_points([None, 0, 0]), profile, period_frames=2)
        self.assertEqual(silence.segments, ())

    def test_automatic_tracking_records_a_prior_driven_choice(self):
        # Raw sums at lags 25 and 50 are three and two.
        values = pulses(76, [0, 25, 50, 75])
        points = injected_points(values)
        search = TempoSearch(minimum_intervals=1, aggregation="sum")
        profile = BeatProfile(50 * HOP, tempo_search=search)
        ordinary = track_beats(points, profile)
        self.assertEqual(ordinary.segments[0].tempo.selected.lag.bpm, 240)
        biased = replace(profile, tempo_search=replace(search, prior=TempoPrior(120, F(1, 8))))
        result = track_beats(points, biased)
        self.assertEqual(result.segments[0].tempo.status, "prior_selected")
        self.assertEqual(result.segments[0].tempo.selected.lag.bpm, 120)
        self.assertEqual([b.frame_index for b in result.segments[0].beats], [1, 51])

    def test_unavailable_tempo_preserves_observations(self):
        points = injected_points([0, 1, 0, 1, 0])
        run = track_beats(points, BeatProfile(3 * HOP))
        self.assertEqual(run.novelty, tuple(points))
        self.assertEqual(run.segments[0].status, "tempo_unavailable")
        self.assertEqual(run.segments[0].tempo.status, "insufficient_support")
        self.assertEqual(run.segments[0].beats, ())

    def test_varied_period_tracks_use_original_record_indices(self):
        # A missing feature divides the runs. The tempo sequence still
        # has its original length and indexing.
        values = [None, 1, 0, 1, None, 1, 0, 0, 1, None]
        periods = [9, 2, 2, 2, 9, 3, 3, 3, 3, 9]
        result = track_beats(injected_points(values), BeatProfile(6 * HOP), period_frames=periods)
        self.assertEqual([[b.frame_index for b in s.beats] for s in result.segments], [[2, 4], [6, 9]])
        self.assertEqual([[b.target_bpm for b in s.beats] for s in result.segments], [[3000, 3000], [2000, 2000]])
        for segment in result.segments:
            for beat in segment.beats:
                self.assertEqual(beat.center_sample_twice, 2 * (ORIGIN + beat.frame_index * HOP) + HOP - 1)

    def test_offline_readiness_includes_trailing_records(self):
        points = injected_points([1, 0, 1, 0, 0, 0, None])
        profile = BeatProfile(3 * HOP)
        boundary = ORIGIN + 8 * HOP
        run = track_beats(points, profile, period_frames=2, observed_release_sample_exclusive=boundary+37)
        self.assertEqual([b.frame_index for b in run.segments[0].beats], [1, 3])
        self.assertEqual(run.ready_sample_exclusive, boundary)
        self.assertEqual(run.observed_release_sample_exclusive, boundary + 37)
        with self.assertRaises(ValueError):
            track_beats(points, profile, period_frames=2, observed_release_sample_exclusive=boundary-1)
        empty = track_beats([], profile, period_frames=2)
        self.assertIsNone(empty.ready_sample_exclusive)

    def test_reject_grid_changes_reverse_spacing_and_invalid_comparison(self):
        points = injected_points([1, 0, 1])
        a, b, c = points
        g = b.frame.grid
        foreign_grid = replace(g, epoch=replace(g.epoch, clock_domain="different clock"))
        g2 = replace(g, epoch=replace(g.epoch, epoch_id="after seek"))
        profile = BeatProfile(3 * HOP)
        malformed = (
            [a, a, c], [c, b, a],
            [a, replace(b, frame=replace(b.frame, grid=foreign_grid)), c],
            [a, replace(b, frame=replace(b.frame, grid=g2)), c],
            [a, replace(b, profile=replace(b.profile, amplitude_reference=0.5)), c],
            [a, replace(b, reference_start_sample=b.frame.start_sample), c],
            [a, replace(b, flux=None), c],
            [a, replace(b, flux=math.inf), c],
            [a, replace(b, frame=replace(b.frame, start_sample=b.frame.start_sample + 1,
                                          end_sample_exclusive=b.frame.end_sample_exclusive + 1)), c],
        )
        for i, series in enumerate(malformed):
            with self.subTest(case=i), self.assertRaises(ValueError):
                track_beats(series, profile, period_frames=2)
        with self.assertRaisesRegex(ValueError, "one period"):
            track_beats(points, profile, period_frames=[2, 2])

    def test_merged_onset_curve_retains_missing_beat_and_time_origin(self):
        m = 960
        w = tuple((1 - math.cos(math.tau * i / m)) / 2 for i in range(m))
        grid = OnsetGrid(epoch(), w, m, HOP)
        detector = OnsetDetector(grid, OnsetProfile(right=2, background=4, margin=0.01))
        normalizer = math.fsum(w)
        energy = math.sqrt(math.fsum(v*v for v in w))
        intended = list(range(7, 340, 50))
        samples = [i * HOP + 480 for i in intended if i != 157]
        points, onsets = [], []
        for t in range(350):
            start = t * HOP
            weight = sum(w[i-start] for i in samples if start <= i < start + m)
            amplitude = weight / normalizer
            bins = (amplitude,) + (2 * amplitude,) * (m//2-1) + (amplitude,)
            frame = OnsetFrame(grid, ORIGIN + start, ORIGIN + start + m, bins, weight / energy)
            point, onset = detector.push(frame)
            points.append(point)
            if onset:
                onsets.append(onset)
        self.assertEqual(len(onsets), 6)
        self.assertIsNone(points[0].flux)
        self.assertEqual(points[157].flux, 0)
        profile = BeatProfile(100 * HOP)
        result = track_beats(points, profile)
        segment, = result.segments
        self.assertEqual(segment.tempo.selected.lag.bpm, 120)
        self.assertEqual([b.frame_index for b in segment.beats], intended)
        self.assertEqual([b.frame_index for b in segment.beats if not b.supported], [157])
        self.assertEqual([b.center_sample_twice for b in segment.beats],
                         [2 * (ORIGIN + t * HOP) + m - 1 for t in intended])
        self.assertEqual(points[7].frame.end_sample_exclusive - ORIGIN, 4320)
        self.assertEqual(onsets[0].ready_sample_exclusive - ORIGIN, 5280)
        self.assertEqual(result.ready_sample_exclusive - ORIGIN, 168480)


class EvaluationTests(unittest.TestCase):
    def test_beat_matching_depends_on_the_target_pulse_level_and_phase(self):
        ref = list(range(25, 825, 50))
        doubled = list(range(25, 825, 25))
        offbeat = [t + 25 for t in ref]
        scores = [matched(ref, found, 850).f1 for found in (ref, ref[::2], doubled, offbeat)]
        self.assertEqual(scores, [1, F(2, 3), F(2, 3), 0])
