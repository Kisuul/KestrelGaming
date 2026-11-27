"""Independent fixtures for supported change, peak selection, and coverage clocks."""

from dataclasses import replace
from fractions import Fraction as F
import math
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in (
    "audio-oscilloscope", "audio-stereo-correlation", "audio-pitch-tracking",
    "audio-tuning-analysis", "audio-power-spectral-density", "audio-spectrogram-waterfall",
    "audio-onset-detection", "audio-chroma-harmony", "audio-event-segmentation",
):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_chroma_harmony import analyze_chroma, power_frame_from_psd
from reference_event_segmentation import (
    MAX_FEATURE_FRAMES, FeatureFrame, FeatureGrid, Segment, SegmentationProfile, analyze_segments,
)
from reference_onset_detection import match_onsets
from reference_oscilloscope import MAX_SAMPLE_INDEX, ScopeEpoch
from reference_psd import periodogram
from reference_tuning_analysis import TuningSupport


O = 2**60 + 37
EPOCH = ScopeEpoch("fixture", O, F(48000), "capture clock", "mic", "FS", ("mono",))
GRID = FeatureGrid(EPOCH, 960, 240, "level", ("FS",))


def row(index, values, *, grid=GRID, ready=None, released=None, actual_end=None):
    start = grid.start_sample(index)
    end = start + grid.window_samples
    present = end if actual_end is None else actual_end
    if ready is None and present == end and values is not None:
        ready = end
    if values is not None and type(values) is not tuple:
        values = (values,)
    support = TuningSupport(grid.epoch, start, end, present, ready, released)
    return FeatureFrame(grid, index, support, values)


def analyze(values, *, grid=GRID, profile=SegmentationProfile(), first=0, span=None):
    frames = [row(first+j, v, grid=grid) for j, v in enumerate(values)]
    return analyze_frames(grid, frames, len(values), profile=profile, first=first, span=span)


def analyze_frames(grid, frames, count, *, profile=SegmentationProfile(), first=0, span=None):
    if span is None:
        span = (2 * grid.epoch.origin_sample,
                2 * (grid.start_sample(first + count - 1) + grid.window_samples))
    return analyze_segments(grid, frames, profile, first_index=first, frame_count=count,
                            analysis_span_twice=span)


def cuts(result):
    return {candidate.index: candidate for candidate in result.candidates}


def values_at(result, indices):
    by_index = cuts(result)
    return [by_index[i].score.squared_novelty if by_index[i].score is not None else None for i in indices]


class ScoreTests(unittest.TestCase):
    def test_abrupt_and_gradual_share_the_peak_height(self):
        profile = SegmentationProfile(minimum_score=4)
        abrupt = analyze([0, 0, 0, 0, 2, 2, 2, 2], profile=profile)
        gradual = analyze([0, 0, 0, 1, 2, 3, 3, 3], profile=profile)
        self.assertEqual(values_at(abrupt, range(2, 7)), [0, 1, 4, 1, 0])
        self.assertEqual(values_at(gradual, range(2, 7)), [F(1, 4), F(9, 4), 4, F(9, 4), F(1, 4)])
        self.assertEqual([v.index for v in abrupt.boundaries], [4])
        self.assertEqual([v.index for v in gradual.boundaries], [4])
        self.assertEqual(cuts(abrupt)[4].score.mean_change, (2,))
        reverse = analyze([2, 2, 2, 2, 0, 0, 0, 0], profile=profile)
        self.assertEqual(cuts(reverse)[4].score.mean_change, (-2,))
        self.assertEqual(cuts(reverse)[4].score.squared_novelty, 4)

    def test_signed_components_are_squared_before_combining(self):
        grid = replace(GRID, feature_profile="two bands", units=("FS^2", "FS^2"))
        result = analyze([(1, 0)] * 4 + [(0, 1)] * 4, grid=grid)
        mark = cuts(result)[4]
        self.assertEqual(mark.score.mean_change, (-1, 1))
        self.assertEqual(mark.score.squared_novelty, 2)
        self.assertEqual(result.boundaries, (mark,))

    def test_variance_only_change_requires_another_feature(self):
        signed = analyze([1, -1, 2, -2])
        squared = analyze([1, 1, 4, 4])
        self.assertEqual(values_at(signed, [2]), [0])
        self.assertEqual(values_at(squared, [2]), [9])
        self.assertEqual(cuts(squared)[2].disposition, "flank_unavailable")

    def test_nearby_levels_and_extreme_finite_values_keep_exact_score(self):
        near = analyze([2.0**40, 2.0**40, 2.0**40 + .25, 2.0**40 + .25])
        self.assertEqual(values_at(near, [2]), [F(1, 16)])
        for amplitude in (math.ldexp(1.0, -1074), sys.float_info.max):
            with self.subTest(amplitude=amplitude):
                wide = analyze([-amplitude, -amplitude, amplitude, amplitude])
                self.assertEqual(cuts(wide)[2].score.mean_change, (2 * F(amplitude),))
                self.assertEqual(values_at(wide, [2]), [4 * F(amplitude)**2])

    def test_exact_gram_differential(self):
        grid = replace(GRID, units=("FS",) * 3)
        rng = random.Random(420042)
        for width in (1, 2, 3, 6):
            source = [tuple(F(rng.randrange(-9, 10), 8) for _ in range(3)) for _ in range(17)]
            result = analyze(source, grid=grid, profile=SegmentationProfile(side_frames=width))
            for b in range(width, len(source) - width + 1):
                span = source[b-width:b+width]
                kernel = [F(-1, width)] * width + [F(1, width)] * width
                expected = sum(u*v*sum(a*b for a, b in zip(x, y))
                               for u, x in zip(kernel, span) for v, y in zip(kernel, span))
                self.assertEqual(cuts(result)[b].score.squared_novelty, expected)


class PeakTests(unittest.TestCase):
    def test_plateau_keeps_the_first_eligible_cut(self):
        profile = SegmentationProfile(minimum_score=F(9, 4), side_frames=4)
        result = analyze([0] * 8 + [2] * 3 + [0] * 9, profile=profile)
        self.assertEqual(values_at(result, (7, 8, 11, 12)), [F(9, 4)] * 4)
        self.assertEqual([cut.index for cut in result.boundaries], [7, 11])
        self.assertEqual(cuts(result)[8].disposition, "not_peak")
        self.assertEqual(cuts(result)[12].disposition, "not_peak")

    def test_context_changes_placement_and_threshold_controls_admission(self):
        values = [0] * 8 + [2] * 3 + [0] * 9
        narrow = analyze(values, profile=SegmentationProfile(side_frames=1))
        wider = analyze(values, profile=SegmentationProfile(side_frames=4))
        too_high = analyze(values, profile=SegmentationProfile(side_frames=4, minimum_score=3))
        self.assertEqual([x.index for x in narrow.boundaries], [8, 11])
        self.assertEqual([x.index for x in wider.boundaries], [7, 11])
        self.assertEqual(too_high.boundaries, ())
        self.assertEqual(cuts(too_high)[7].disposition, "below_threshold")

    def test_radius_imposes_a_minimum_separation(self):
        pulse = [0] * 6 + [2] * 2 + [0] * 6
        narrow = analyze(pulse, profile=SegmentationProfile(side_frames=1, peak_radius=1))
        wider = analyze(pulse, profile=SegmentationProfile(side_frames=1, peak_radius=2))
        self.assertEqual([x.index for x in narrow.boundaries], [6, 8])
        self.assertEqual([x.index for x in wider.boundaries], [6])

    def test_pending_right_flank_needs_one_more_feature(self):
        source = [0, 0, 0, 0, 2, 2, 2, 2]
        partial = analyze(source[:6])
        complete = analyze(source[:7])
        self.assertEqual(cuts(partial)[4].disposition, "flank_unavailable")
        self.assertIsNone(cuts(partial)[4].peak_ready_sample_exclusive)
        self.assertEqual(complete.boundaries[0].index, 4)
        self.assertEqual(cuts(complete)[4].score, cuts(partial)[4].score)

    def test_shared_prefix_gives_the_same_confirmed_cut(self):
        early = [0, 0, 0, 0, 2, 2, 2]
        a = analyze(early + [2, 2, 2, 2, 2])
        b = analyze(early + [32, 32, 32, 32, 32])
        self.assertEqual(cuts(a)[4], cuts(b)[4])
        self.assertEqual([x.index for x in a.boundaries], [4])
        self.assertEqual([x.index for x in b.boundaries], [4, 7])

    def test_imposed_edge_is_coverage_when_context_could_find_a_peak(self):
        series = [0, 0, 0, 0, 2, 2, 2, 2]
        boundary = 2 * O + 2639
        result = analyze(series, span=(boundary, 2 * O + 5000))
        self.assertEqual(cuts(result)[4].score.squared_novelty, 4)
        self.assertEqual(cuts(result)[4].disposition, "outside_analysis")
        self.assertEqual(result.boundaries, ())
        self.assertEqual(result.segments[0].start_sample_twice, boundary)


class SupportAndClockTests(unittest.TestCase):
    def test_gap_blocks_the_window_and_zero_fill_creates_a_false_peak(self):
        original = [0, 0, None, 1, 1, 1, 1]
        missing = analyze(original)
        fabricated = analyze([0 if v is None else v for v in original])
        self.assertEqual(values_at(missing, range(2, 6)), [None, None, None, 0])
        self.assertEqual(values_at(fabricated, range(2, 6)), [F(1, 4), 1, F(1, 4), 0])
        self.assertEqual(missing.boundaries, ())
        self.assertEqual([x.index for x in fabricated.boundaries], [3])
        self.assertEqual(cuts(missing)[4].disposition, "feature_gap")
        self.assertEqual(cuts(missing)[5].disposition, "flank_unavailable")

    def test_omitted_slots_match_explicit_gap_and_keep_original_indices(self):
        frames = [row(i, v) for i, v in enumerate([0, 0, None, 1, 1, 1, 1])]
        explicit = analyze_frames(GRID, frames, 7)
        sparse = analyze_frames(GRID, list(reversed(frames[:2] + frames[3:])), 7)
        self.assertEqual(explicit.candidates, sparse.candidates)
        self.assertEqual(explicit.segments, sparse.segments)
        self.assertEqual([x.index for x in sparse.source_frames], [0, 1, 3, 4, 5, 6])
        self.assertEqual(sparse.segments, (
            Segment(2*O, 2*O + 719, False),
            Segment(2*O + 719, 2*O + 1679, True),
            Segment(2*O + 1679, 2*O + 2159, False),
            Segment(2*O + 2159, 2*O + 4079, True),
            Segment(2*O + 4079, 2*O + 4800, False),
        ))

    def test_exact_boundary_score_support_and_peak_support(self):
        result = analyze([0, 0, 0, 0, 2, 2, 2, 2])
        cut, = result.boundaries
        self.assertEqual(cut.index, 4)
        self.assertEqual((cut.left_center_sample_twice, cut.right_center_sample_twice),
                         (2*O + 2399, 2*O + 2879))
        self.assertEqual(cut.position_sample_twice, 2*O + 2639)
        self.assertEqual(cut.score.left_sample_support, (O + 480, O + 1680))
        self.assertEqual(cut.score.right_sample_support, (O + 960, O + 2160))
        self.assertEqual(cut.score.ready_sample_exclusive, O + 2160)
        self.assertEqual(cut.peak_sample_support, (O + 240, O + 2400))
        self.assertEqual(cut.peak_ready_sample_exclusive, O + 2400)
        self.assertEqual(result.peak_eligible_spans_twice, ((2*O + 1919, 2*O + 3359),))
        self.assertEqual(result.segments[1:3], (
            Segment(2*O + 719, cut.position_sample_twice, True),
            Segment(cut.position_sample_twice, 2*O + 4559, True),
        ))

    def test_delayed_left_flank_controls_peak_readiness_and_delivery(self):
        values = [0, 0, 0, 0, 2, 2, 2, 2]
        frames = [row(i, v, released=O + 1024 * math.ceil(F(GRID.start_sample(i)+960-O, 1024)))
                  for i, v in enumerate(values)]
        frames[1] = row(1, 0, ready=O+2800, released=O+3072)
        cut, = analyze_frames(GRID, frames, 8).boundaries
        self.assertEqual(cut.score.ready_sample_exclusive, O + 2160)
        self.assertEqual(cut.peak_ready_sample_exclusive, O + 2800)
        self.assertEqual(cut.peak_evidence_release_sample_exclusive, O + 3072)
        frames[1] = row(1, 0, ready=O+2800)
        missing, = analyze_frames(GRID, frames, 8).boundaries
        self.assertEqual(missing.peak_ready_sample_exclusive, cut.peak_ready_sample_exclusive)
        self.assertEqual(missing.score.evidence_release_sample_exclusive, O + 3072)
        self.assertIsNone(missing.peak_evidence_release_sample_exclusive)

    def test_delivery_partition_preserves_event_and_dependency_indices(self):
        values = [0, 0, 0, 0, 2, 2, 2, 2]
        reports = []
        for block in (240, 1024):
            frames = [row(i, v, released=O + block * math.ceil(F(GRID.start_sample(i)+960-O, block)))
                      for i, v in enumerate(values)]
            reports.append(analyze_frames(GRID, frames, len(values)).boundaries[0])
        a, b = reports
        self.assertEqual((a.position_sample_twice, a.peak_ready_sample_exclusive, a.peak_sample_support),
                         (b.position_sample_twice, b.peak_ready_sample_exclusive, b.peak_sample_support))
        self.assertEqual((a.peak_evidence_release_sample_exclusive, b.peak_evidence_release_sample_exclusive),
                         (O + 2400, O + 3072))

    def test_disjoint_peak_eligible_spans_exclude_a_feature_gap(self):
        series = [0] * 8 + [None] + [0] * 8
        result = analyze(series)
        self.assertEqual(result.peak_eligible_spans_twice, (
            (2*O + 1919, 2*O + 3359), (2*O + 6239, 2*O + 7679),
        ))
        self.assertTrue(all(x.disposition == "below_threshold" for x in result.candidates
                            if x.peak_ready_sample_exclusive is not None))

    def test_partial_feature_support_retained_without_providing_a_score(self):
        frames = [row(i, 1) for i in range(8)]
        frames[3] = row(3, None, actual_end=O+750, released=O+800)
        result = analyze_frames(GRID, frames, 8)
        self.assertEqual(cuts(result)[4].disposition, "feature_gap")
        self.assertIsNone(cuts(result)[4].score)
        self.assertEqual(result.source_frames[3].support.available_end_sample_exclusive, O+750)

    def test_late_crop_preserves_original_frame_indices(self):
        result = analyze([0, 0, 0, 0, 2, 2, 2, 2], first=200)
        selected, = result.boundaries
        self.assertEqual(result.frame_index_span, (200, 208))
        self.assertEqual(selected.index, 204)
        self.assertEqual(selected.position_sample_twice, 2*O + 2639 + 400*240)
        self.assertEqual(result.segments[0].start_sample_twice, 2*O)
        self.assertFalse(result.segments[0].feature_available)

    def test_empty_grid_retains_unknown_coverage(self):
        span = (2*O + 10, 2*O + 110)
        result = analyze_frames(GRID, [], 0, span=span)
        self.assertEqual(result.candidates, ())
        self.assertEqual(result.peak_eligible_spans_twice, ())
        self.assertEqual(result.segments, (Segment(*span, False),))

    def test_analysis_clip_can_keep_partial_cells_exactly(self):
        # Clip a known cell to two fractional sample positions.
        span = (2*O + 800, 2*O + 801)
        result = analyze([0] * 8, span=span)
        self.assertEqual(result.peak_eligible_spans_twice, ())
        self.assertEqual(result.segments, (Segment(*span, True),))


class IntegrationTests(unittest.TestCase):
    def test_equal_level_pitch_change_in_merged_psd_and_chroma(self):
        epoch = replace(EPOCH, rate_hz=F(3520))
        shape_grid = FeatureGrid(epoch, 64, 64, "L1 chroma", ("fraction",) * 12)
        level_grid = replace(shape_grid, feature_profile="RMS", units=("FS",))
        for after_bin, gain in ((12, .5), (16, .5), (8, .25)):
            shapes, levels = [], []
            for i in range(8):
                k, amp = (8, .5) if i < 4 else (after_bin, gain)
                pcm = [amp * math.cos(math.tau * k * j / 64) for j in range(64)]
                _, density = periodogram(pcm, [1.0] * 64, 3520)
                clock = row(i, None, grid=shape_grid, ready=O+64*(i+1)).support
                power = power_frame_from_psd(density, fft_length=64, support=clock, power_units="FS^2")
                output = analyze_chroma(power)
                shape = tuple(m / output.totals.admitted for m in output.raw_chroma)
                rms = math.sqrt(math.fsum(v*v for v in pcm) / 64)
                shapes.append(FeatureFrame(shape_grid, i, clock, shape))
                levels.append(FeatureFrame(level_grid, i, clock, (rms,)))
            d_shape = cuts(analyze_frames(shape_grid, shapes, 8))[4].score.squared_novelty
            d_rms = cuts(analyze_frames(level_grid, levels, 8))[4].score.squared_novelty
            with self.subTest(after_bin=after_bin, gain=gain):
                if after_bin == 12:
                    self.assertAlmostEqual(float(d_shape), 1.9616643883689844, delta=5e-13)
                    self.assertLess(d_rms, F(1, 10**26))
                elif after_bin == 16:
                    self.assertLess(max(d_rms, d_shape), F(1, 10**26))
                else:
                    self.assertLess(d_shape, F(1, 10**26))
                    self.assertAlmostEqual(float(d_rms), 1/32, delta=1e-14)

    def test_boundaries_use_existing_matcher_on_the_interior_span(self):
        result = analyze([0, 0, 0, 0, 2, 2, 2, 2])
        event, = result.boundaries
        eligible, = result.peak_eligible_spans_twice
        verdict = match_onsets(
            [event.position_sample_twice - 8], [event.position_sample_twice],
            tolerance_sample_twice=8, eligible_interval_twice=eligible,
        )
        self.assertEqual((verdict.precision, verdict.recall, verdict.f1), (1, 1, 1))
        self.assertEqual(verdict.matches[0].error_sample_twice, 8)
        self.assertTrue(all(event.position_sample_twice != x for x in result.analysis_span_twice))


class ValidationTests(unittest.TestCase):
    def test_reject_invalid_features_and_profiles(self):
        good = row(0, 2)
        checks = (
            lambda: replace(GRID, window_samples=0), lambda: replace(GRID, hop_samples=961),
            lambda: replace(GRID, units=("",)), lambda: replace(GRID, units=("FS",)*65),
            lambda: replace(GRID, feature_profile=" "),
            lambda: SegmentationProfile(side_frames=0), lambda: SegmentationProfile(peak_radius=True),
            lambda: SegmentationProfile(minimum_score=0), lambda: SegmentationProfile(minimum_score=math.inf),
            lambda: replace(good, values=(math.nan,)), lambda: replace(good, values=(1, 2)),
            lambda: replace(good, values=[1]), lambda: replace(good, index=1),
            lambda: replace(good, support=replace(good.support, ready_sample_exclusive=None)),
        )
        for i, check in enumerate(checks):
            with self.subTest(check=i), self.assertRaises(ValueError):
                check()

    def test_reject_cross_grid_or_duplicate_frames_and_invalid_span(self):
        params = dict(frame_count=2, analysis_span_twice=(2*O, 2*O+2500))
        reference = row(0, 1)
        incompatible = (
            row(0, 1, grid=replace(GRID, feature_profile="alternate")),
            row(0, 1, grid=replace(GRID, epoch=replace(EPOCH, epoch_id="post-gap"))),
        )
        for sequence in ([reference, reference], [row(2, 1)], *([x] for x in incompatible)):
            with self.subTest(sequence=sequence), self.assertRaises(ValueError):
                analyze_segments(GRID, sequence, **params)
        with self.assertRaises(ValueError):
            analyze_segments(GRID, [], frame_count=MAX_FEATURE_FRAMES+1,
                             analysis_span_twice=params["analysis_span_twice"])
        with self.assertRaises(ValueError):
            analyze_segments(GRID, [], frame_count=2, analysis_span_twice=(2*O+1, 2*O))

    def test_final_representable_window_is_allowed(self):
        start = MAX_SAMPLE_INDEX - 9
        ep = replace(EPOCH, origin_sample=start)
        grid = FeatureGrid(ep, 9, 1, "level", ("FS",))
        first = FeatureFrame(grid, 0, TuningSupport(ep, start, MAX_SAMPLE_INDEX, MAX_SAMPLE_INDEX,
                                                    MAX_SAMPLE_INDEX), (1,))
        report = analyze_segments(grid, [first], frame_count=1,
                                  analysis_span_twice=(2*start, 2*MAX_SAMPLE_INDEX))
        self.assertEqual(report.source_frames[0].support.end_sample_exclusive, MAX_SAMPLE_INDEX)
        with self.assertRaises(ValueError):
            grid.start_sample(1)
