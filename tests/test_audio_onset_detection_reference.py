"""Engineering fixtures for onset score, peak readiness, and event matching."""

from dataclasses import replace
from fractions import Fraction as F
from itertools import combinations_with_replacement
import math
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in (
    "audio-oscilloscope", "audio-stereo-correlation",
    "audio-spectrogram-waterfall", "audio-onset-detection",
):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_oscilloscope import MAX_SAMPLE_INDEX, ScopeEpoch
from reference_onset_detection import (
    OnsetDetector, OnsetFrame, OnsetGrid, OnsetProfile, analyze_pcm_chunks, match_onsets,
)


def grid(m=2, n=2, h=1, origin=0, *, window=None, epoch_id="capture-A"):
    epoch = ScopeEpoch(epoch_id, origin, F(48000), "device-A", "post-fader", "FS", ("mono",))
    return OnsetGrid(epoch, (1.0,) * m if window is None else tuple(window), n, h)


def frame(g, i, amplitudes, rms=0.0):
    start = g.first_start_sample + i * g.hop
    return OnsetFrame(g, start, start + g.window_length, amplitudes, rms)


def score_frames(detector, g, scores, *, rms_source=False):
    level = 0.0
    for i, score in enumerate(scores):
        if score is not None:
            level += score
        values = [0.0] * g.bin_count
        if not rms_source:
            values[1] = level
        yield detector.push(frame(g, i, values, level if rms_source else 0.0))


def blocks(origin, samples, cuts):
    return [(origin + lo, samples[lo:hi]) for lo, hi in zip([0, *cuts], [*cuts, len(samples)])]


def tone(length, bin_index, amplitude):
    return [amplitude * math.cos(math.tau * bin_index * j / length) for j in range(length)]


def impulse_frames(g, sample, boundaries):
    """Closed-form spectrum and RMS for a unit impulse on a periodic Hann."""
    m = g.window_length
    total = math.fsum(g.window)
    norm = math.sqrt(math.fsum(w*w for w in g.window))
    for i, offset in enumerate(range(0, boundaries[-1] - m + 1, g.hop)):
        relative = sample - offset
        w = g.window[relative] if 0 <= relative < m else 0.0
        values = [2*w/total] * g.bin_count
        values[0] = values[-1] = w/total
        end = next(boundary for boundary in boundaries if boundary >= offset + m)
        yield frame(g, i, values, w/norm), g.first_start_sample + end


class NoveltyTests(unittest.TestCase):
    def test_lag_comparison_preserves_support_and_warmup(self):
        g = grid(m=3, n=5, h=2, origin=2**60 + 37)
        g = replace(g, first_start_sample=g.epoch.origin_sample + 10)
        d = OnsetDetector(g, OnsetProfile(lag=2, weights=(0, 2, 0.5)))
        inputs = [((1, 0.125, 0.75), 0.5), ((0, 5, 2), 4), ((10, 0.375, 1.25), 0.75)]
        points = [d.push(frame(g, i, values, rms))[0] for i, (values, rms) in enumerate(inputs)]
        for p in points[:2]:
            self.assertIsNone(p.reference_start_sample)
            self.assertIsNone(p.flux)
            self.assertIsNone(p.rms_rise)
        p = points[2]
        self.assertEqual(p.reference_start_sample, g.first_start_sample)
        self.assertEqual(p.frame.start_sample, g.first_start_sample + 4)
        self.assertEqual(p.center_sample_twice, 2 * (g.first_start_sample + 5))
        self.assertEqual(p.contributions, ((1, F(1, 2)), (2, F(1, 4))))
        self.assertEqual((p.flux, p.rms_rise), (F(3, 4), F(1, 4)))

    def test_supported_silence_and_falling_level(self):
        g = grid()
        d = OnsetDetector(g)
        points = [d.push(frame(g, i, [v, v], v))[0] for i, v in enumerate([0, 0, 1, 0])]
        self.assertEqual([p.flux for p in points], [None, 0, 2, 0])
        self.assertEqual([p.rms_rise for p in points], [None, 0, 1, 0])
        self.assertEqual(points[1].contributions, ())
        self.assertEqual(points[1].reference_start_sample, 0)

    def test_radius_is_clipped_at_both_edges(self):
        g = grid(n=8)
        d = OnsetDetector(g, OnsetProfile(neighbor_radius=1))
        d.push(frame(g, 0, (0, 0, 0, 0, 2)))
        p, _ = d.push(frame(g, 1, (1, 1, 0, 1, 0)))
        self.assertEqual(p.contributions, ((0, 1), (1, 1)))
        p, _ = d.push(frame(g, 2, (0, 0, 0, 0, 1)))
        self.assertEqual(p.contributions, ())
        p, _ = d.push(frame(g, 3, (10, 0, 0, 0, 0)))
        self.assertEqual(p.contributions, ((0, 10),))

    def test_maximum_radius_references_all_bins(self):
        g = grid(n=8)
        d = OnsetDetector(g, OnsetProfile(neighbor_radius=4))
        d.push(frame(g, 0, (0, 0, 0, 0, 2)))
        p, _ = d.push(frame(g, 1, (3, 0, 0, 0, 3)))
        self.assertEqual(p.contributions, ((0, 1), (4, 1)))

    def test_fixed_log_reference_and_weights(self):
        g = grid(n=4)
        d = OnsetDetector(g, OnsetProfile(amplitude_reference=0.125, weights=(2, 0.5, 0)))
        d.push(frame(g, 0, (0.5, 0.125, 0)))
        p, _ = d.push(frame(g, 1, (0.75, 0.375, 10)))
        expected = 2 * (math.log1p(6) - math.log1p(4)) + 0.5 * (math.log1p(3) - math.log1p(1))
        self.assertAlmostEqual(float(p.flux), expected, delta=4e-16)
        self.assertEqual(tuple(k for k, _ in p.contributions), (0, 1))
        self.assertEqual(p.flux, sum(value for _, value in p.contributions))

    def test_log_neighbor_filter_matches_compressed_maximum(self):
        g = grid(n=4)
        d = OnsetDetector(g, OnsetProfile(amplitude_reference=0.5, neighbor_radius=1))
        d.push(frame(g, 0, (2, 0.5, 0)))
        p, _ = d.push(frame(g, 1, (1, 0.75, 0.75)))
        self.assertEqual(tuple(k for k, _ in p.contributions), (2,))
        self.assertAlmostEqual(float(p.flux), math.log(2.5) - math.log(2), delta=3e-16)

    def test_log_range_and_subtraction_near_maximum_amplitude(self):
        lo = math.ldexp(1.0, -1074)
        hi = sys.float_info.max
        g = grid()
        d = OnsetDetector(g, OnsetProfile(amplitude_reference=lo))
        d.push(frame(g, 0, (0, math.nextafter(hi, 0))))
        p, _ = d.push(frame(g, 1, (hi, hi)))
        expected = math.log(hi) - math.log(lo)
        self.assertAlmostEqual(float(p.contributions[0][1]), expected, delta=3e-13)
        # Subtracting the two large compressed ordinates would lose this positive change.
        self.assertGreater(p.contributions[1][1], 0)
        self.assertLess(p.contributions[1][1], F(1, 10**15))

    def test_range_failure_leaves_detector_ready_to_retry(self):
        g = grid()
        profile = OnsetProfile(amplitude_reference=sys.float_info.max)
        d = OnsetDetector(g, profile)
        first = frame(g, 0, (0, 0))
        d.push(first, observed_release_sample_exclusive=3)
        smallest = math.ldexp(1.0, -1074)
        with self.assertRaisesRegex(ValueError, "log change underflows"):
            d.push(frame(g, 1, (0, smallest)), observed_release_sample_exclusive=10)
        fallback = frame(g, 1, (0, 1))
        other = OnsetDetector(g, profile)
        other.push(first)
        self.assertEqual(d.push(fallback, observed_release_sample_exclusive=3), other.push(fallback))

    def test_plain_products_and_sum_keep_binary64_extremes(self):
        g = grid(n=4)
        hi, lo = sys.float_info.max, math.ldexp(1.0, -1074)
        d = OnsetDetector(g, OnsetProfile(weights=(hi, lo, 1)))
        d.push(frame(g, 0, (0, 0, 0)))
        p, _ = d.push(frame(g, 1, (hi, lo, hi)))
        self.assertEqual(p.flux, F(hi)**2 + F(lo)**2 + F(hi))
        self.assertGreater(p.contributions[1][1], 0)

    def test_grid_and_profile_validate_dimensions_and_units(self):
        g = grid()
        cases = (
            lambda: replace(g, fft_length=1),
            lambda: replace(g, window=(0, 0)),
            lambda: replace(g, window=(1, math.nan)),
            lambda: replace(g, hop=True),
            lambda: replace(g, hop=3),
            lambda: replace(g, epoch=replace(g.epoch, channel_ids=("L", "R"))),
            lambda: replace(g, first_start_sample=-1),
            lambda: OnsetProfile(lag=0),
            lambda: OnsetProfile(right=0),
            lambda: OnsetProfile(background=129),
            lambda: OnsetProfile(margin=-1),
            lambda: OnsetProfile(amplitude_reference=0),
            lambda: OnsetProfile(weights=(1, -1)),
            lambda: OnsetProfile(source="peak"),
            lambda: OnsetDetector(g, OnsetProfile(neighbor_radius=2)),
            lambda: OnsetDetector(g, OnsetProfile(weights=(1, 1, 1))),
        )
        for i, make in enumerate(cases):
            with self.subTest(case=i), self.assertRaises(ValueError):
                make()

    def test_reject_malformed_calibrated_frames(self):
        g = grid()
        valid = frame(g, 0, (0, 0))
        for attrs in (
            {"amplitudes": (1,)}, {"amplitudes": (0, -1)},
            {"amplitudes": (0, math.inf)}, {"weighted_rms": math.nan},
            {"weighted_rms": -0.01}, {"weighted_rms": True},
            {"weighted_rms": 2**53 + 1}, {"end_sample_exclusive": 3},
        ):
            with self.subTest(attrs=attrs), self.assertRaises(ValueError):
                replace(valid, **attrs)
        near_end = grid(origin=MAX_SAMPLE_INDEX - 1)
        with self.assertRaises(ValueError):
            frame(near_end, 0, (0, 0))

    def test_reject_discontinuity_grid_change_or_impossible_release(self):
        g = grid(origin=10)
        d = OnsetDetector(g)
        first = frame(g, 0, (0, 0))
        d.push(first, observed_release_sample_exclusive=15)
        expected = frame(g, 1, (1, 0))
        foreign = (
            replace(g, epoch=replace(g.epoch, clock_domain="clock-B")),
            replace(g, epoch=replace(g.epoch, rate_hz=F(44100))),
            replace(g, epoch=replace(g.epoch, epoch_id="capture-B")),
            replace(g, epoch=replace(g.epoch, tap_id="pre-fader")),
            replace(g, epoch=replace(g.epoch, units="V")),
            replace(g, epoch=replace(g.epoch, channel_ids=("right",))),
            replace(g, window=(1, 0.5)),
        )
        for rejected in (first, frame(g, 2, (1, 0)), *(frame(item, 1, (1, 0)) for item in foreign)):
            with self.subTest(rejected=rejected), self.assertRaises(ValueError):
                d.push(rejected)
        for boundary in (12, 14, True):
            with self.subTest(boundary=boundary), self.assertRaises(ValueError):
                d.push(expected, observed_release_sample_exclusive=boundary)
        p, _ = d.push(expected, observed_release_sample_exclusive=15)
        self.assertEqual((p.reference_start_sample, p.flux), (10, 1))


class PickerTests(unittest.TestCase):
    def test_plateau_margin_separation_and_pending_capture_end(self):
        scores = [None, 0, 0, 4, 4, 1, 0, 5, 0, 0, 0]
        g = grid(240, 240, 240)
        base = OnsetProfile(left=1, right=2, background=2, margin=0.5)
        for separation, count, confirmed in ((960, 11, (3, 7)), (961, 11, (3,)), (960, 9, (3,))):
            with self.subTest(separation=separation, count=count):
                detector = OnsetDetector(g, replace(base, refractory_samples=separation))
                replies = list(score_frames(detector, g, scores[:count]))
                self.assertEqual([point.flux for point, _ in replies], scores[:count])
                self.assertEqual(
                    tuple(i - 2 for i, (_, event) in enumerate(replies) if event), confirmed
                )
                for peak in confirmed:
                    _, event = replies[peak + 2]
                    self.assertEqual(event.peak.frame.start_sample, peak * 240)
                    self.assertEqual(event.ready_sample_exclusive, (peak + 3) * 240)
                    self.assertEqual(event.estimated_sample_twice, (2 * peak + 1) * 240 - 1)
                    self.assertIsNone(event.observed_release_sample_exclusive)

    def test_trailing_median_uses_all_preceding_scores_and_strict_margin(self):
        g = grid()
        scores = [None, 2, 0, 3, 0]
        base = OnsetProfile(left=1, right=1, background=2, margin=2)
        for margin, expect_event in ((2, False), (math.nextafter(2, 0), True)):
            detector = OnsetDetector(g, replace(base, margin=margin))
            replies = list(score_frames(detector, g, scores))
            self.assertTrue(all(event is None for _, event in replies[:-1]))
            self.assertEqual(replies[-1][1] is not None, expect_event)

    def test_entire_left_and_right_flanks_are_required(self):
        g = grid()
        fixtures = (
            ([None, 0, 0, 4, 1, 4, 0, 0], [3]),
            ([None, 0, 0, 2, 1, 3, 0, 0], [5]),
        )
        for scores, expected in fixtures:
            detector = OnsetDetector(g, OnsetProfile(left=2, right=2, background=1))
            replies = list(score_frames(detector, g, scores))
            self.assertEqual([event.peak.frame.start_sample for _, event in replies if event], expected)

    def test_rms_picker_keeps_both_curves(self):
        g = grid()
        d = OnsetDetector(g, OnsetProfile(source="rms_rise", background=1))
        replies = list(score_frames(d, g, [None, 0, 3, 0], rms_source=True))
        p, event = replies[-1]
        self.assertEqual(p.rms_rise, 0)
        self.assertEqual(event.score_source, "rms_rise")
        self.assertEqual(event.peak.flux, 0)
        self.assertEqual(event.score, 3)

    def test_reset_drops_lag_background_and_refractory_history(self):
        g = grid(origin=100)
        d = OnsetDetector(g, OnsetProfile(background=1, refractory_samples=1000))
        prior = list(score_frames(d, g, [None, 0, 3, 0]))[-1][1]
        self.assertIsNotNone(prior)
        with self.assertRaises(ValueError):
            d.reset(g)
        new = replace(g, epoch=replace(g.epoch, epoch_id="after-seek"))
        changed_profile = replace(prior.peak.profile, amplitude_reference=2)
        d.reset(new, changed_profile)
        replies = list(score_frames(d, new, [None, 0, 3, 0]))
        self.assertIsNone(replies[0][0].flux)
        self.assertTrue(all(event is None for _, event in replies[:-1]))
        event = replies[-1][1]
        self.assertIsNotNone(event)
        self.assertEqual(event.estimated_sample_twice, prior.estimated_sample_twice)
        self.assertEqual(event.peak.frame.grid.epoch.epoch_id, "after-seek")
        self.assertEqual(event.peak.profile, changed_profile)

    def test_failed_reset_preserves_pending_candidate(self):
        g = grid()
        d = OnsetDetector(g, OnsetProfile(background=1))
        list(score_frames(d, g, [None, 0, 3]))
        new = replace(g, epoch=replace(g.epoch, epoch_id="after-gap"))
        with self.assertRaises(ValueError):
            d.reset(new, OnsetProfile(weights=(1, 1, 1)))
        _, event = d.push(frame(g, 3, (0, 3)), observed_release_sample_exclusive=6)
        self.assertEqual(event.estimated_sample_twice, 5)
        self.assertEqual((event.ready_sample_exclusive, event.observed_release_sample_exclusive), (5, 6))

    def test_hann_impulse_peak_and_readiness_are_partition_invariant(self):
        origin = 2**60 + 37
        hann = tuple(0.5 - 0.5 * math.cos(math.tau * j / 960) for j in range(960))
        g = grid(960, 960, 240, origin, window=hann)
        profile = OnsetProfile(right=2, background=4, margin=0.01)
        rng = random.Random(360036)
        irregular = []
        offset = 0
        while offset < 7200:
            offset = min(7200, offset + rng.randint(1, 600))
            irregular.append(offset)
        expected_novelty = None
        for boundaries in ([7200], list(range(1, 7201)), irregular, [5279], [5280]):
            with self.subTest(last=boundaries[-1], blocks=len(boundaries)):
                detector = OnsetDetector(g, profile)
                points = []
                events = []
                for f, delivered in impulse_frames(g, 4440, boundaries):
                    point, event = detector.push(f, observed_release_sample_exclusive=delivered)
                    points.append((point.center_sample_twice, point.flux, point.rms_rise))
                    if event:
                        events.append(event)
                if expected_novelty is None:
                    expected_novelty = points
                    self.assertEqual(len(points), 27)
                self.assertEqual(points, expected_novelty[:len(points)])
                if boundaries[-1] == 5279:
                    self.assertEqual(events, [])
                    continue
                self.assertEqual(len(events), 1)
                event = events[0]
                self.assertEqual(event.peak.frame.start_sample, origin + 3840)
                self.assertEqual(event.estimated_sample_twice, 2 * origin + 8639)
                self.assertEqual(event.ready_sample_exclusive, origin + 5280)
                delivered = next(b for b in boundaries if b >= 5280)
                self.assertEqual(event.observed_release_sample_exclusive, origin + delivered)


class PCMTests(unittest.TestCase):
    def test_amplitude_calibration_at_dc_and_both_transform_parities(self):
        for n in (7, 8):
            with self.subTest(n=n):
                g = grid(n, n, n)
                samples = [0.125 + x for x in tone(n, n // 2, 0.25)]
                p = analyze_pcm_chunks([(0, samples)], g).novelty[0]
                self.assertAlmostEqual(p.frame.amplitudes[0], 0.125, delta=1e-15)
                self.assertAlmostEqual(p.frame.amplitudes[-1], 0.25, delta=1e-15)
                expected_power = F(1, 64) + F(1, 16 if n == 8 else 32)
                self.assertAlmostEqual(p.frame.weighted_rms, math.sqrt(expected_power), delta=1e-15)

    def test_weighted_rms_uses_squared_weights_and_only_frame_support(self):
        g = grid(3, 7, 3, window=(0, 0.25, 0.75))
        p = analyze_pcm_chunks([(0, [100, 1, 3, 20, 40])], g).novelty[0]
        self.assertAlmostEqual(p.frame.weighted_rms, math.sqrt(8.2), delta=1e-15)
        self.assertEqual(p.center_sample_twice, 2)
        self.assertEqual(p.frame.end_sample_exclusive, 3)

    def test_pcm_partitions_keep_scores_and_exact_timestamps(self):
        origin = 2**60 + 37
        g = grid(4, 8, 2, origin, window=(0, 0.5, 1, 0.5))
        samples = [0.0] * 24
        samples[10] = 1.0
        profile = OnsetProfile(background=1, right=2, margin=0.01)
        full = analyze_pcm_chunks([(origin, samples)], g, profile)
        self.assertEqual(len(full.events), 1)
        for cuts in ([3, 4, 11, 12, 19], list(range(1, len(samples)))):
            result = analyze_pcm_chunks(blocks(origin, samples, cuts), g, profile)
            self.assertEqual(result.novelty, full.novelty)
            self.assertEqual(
                replace(result.events[0], observed_release_sample_exclusive=origin + len(samples)),
                full.events[0],
            )
            self.assertEqual(result.events[0].ready_sample_exclusive, origin + 16)
            self.assertEqual(result.events[0].estimated_sample_twice, 2 * origin + 19)
            self.assertEqual(
                result.events[0].observed_release_sample_exclusive,
                origin + next(c for c in [*cuts, len(samples)] if c >= 16),
            )

    def test_tone_changes_distinguish_spectral_motion_and_amplitude(self):
        m = 480
        g = grid(m, m, m)
        held = tone(m, 8, 0.5)
        louder = tone(m, 8, 0.6)
        soft_neighbor = tone(m, 9, 0.2)
        fixtures = (
            (held, tone(m, 9, 0.5), 0.5, 0.0, 0.0),
            (held, tone(m, 12, 0.5), 0.5, 0.5, 0.0),
            (louder, [a + b for a, b in zip(louder, soft_neighbor)], 0.2, 0.0,
             (math.hypot(0.6, 0.2) - 0.6) / math.sqrt(2)),
            (held, tone(m, 8, 0.25), 0.0, 0.0, 0.0),
            (held, tone(m, 8, 0.75), 0.25, 0.25, 0.25 / math.sqrt(2)),
        )
        for i, (first, second, plain, filtered, rms) in enumerate(fixtures):
            with self.subTest(case=i):
                pcm = [(0, first + second)]
                for radius, want in enumerate((plain, filtered)):
                    p = analyze_pcm_chunks(pcm, g, OnsetProfile(neighbor_radius=radius)).novelty[1]
                    self.assertAlmostEqual(float(p.flux), want, delta=3e-13)
                    self.assertAlmostEqual(float(p.rms_rise), rms, delta=2e-15)

    def test_inverted_pair_cancels_in_declared_mono_mix(self):
        g = grid(4, 4, 4)
        left = [0] * 6 + [1, 0]
        right = [-x for x in left]
        lgrid = replace(g, epoch=replace(g.epoch, channel_ids=("L",)))
        rgrid = replace(g, epoch=replace(g.epoch, channel_ids=("R",)))
        for named_grid, data in ((lgrid, left), (rgrid, right)):
            point = analyze_pcm_chunks([(0, data)], named_grid).novelty[-1]
            self.assertEqual(point.flux, 1)
            self.assertEqual(point.rms_rise, F(1, 2))
        mix = [(a + b) * 0.5 for a, b in zip(left, right)]
        point = analyze_pcm_chunks([(0, mix)], g).novelty[-1]
        self.assertEqual((point.flux, point.rms_rise), (0, 0))

    def test_flat_silence_and_incomplete_tails(self):
        g = grid(4, 4, 3)
        for data in ([], [(0, [0] * 3)]):
            self.assertEqual(analyze_pcm_chunks(data, g).novelty, ())
        run = analyze_pcm_chunks([(0, [0] * 9)], g)
        self.assertEqual([p.frame.end_sample_exclusive for p in run.novelty], [4, 7])
        self.assertEqual([p.flux for p in run.novelty], [None, 0])
        self.assertEqual(run.events, ())

    def test_pcm_limits_and_invalid_data_are_explicit(self):
        g = grid()
        with self.assertRaisesRegex(ValueError, "calibrated frames"):
            analyze_pcm_chunks([], grid(n=513))
        for data in (
            [(1, [0, 0])], [(0, [0]), (0, [0])], [(0, [0]), (2, [0])],
            [(0, [0] * 130)], [(0, [])], [(0, [0, math.inf])],
        ):
            with self.subTest(data=data[:1]), self.assertRaises(ValueError):
                analyze_pcm_chunks(data, g)
        self.assertEqual(len(analyze_pcm_chunks([(0, [0] * 129)], g).novelty), 128)

    def test_pcm_fft_and_weighted_rms_range_failures(self):
        g = grid()
        hi, lo = sys.float_info.max, math.ldexp(1.0, -1074)
        with self.assertRaisesRegex(ValueError, "bin amplitude"):
            analyze_pcm_chunks([(0, [hi, hi])], g)
        with self.assertRaisesRegex(ValueError, "underflows"):
            analyze_pcm_chunks([(0, [lo, 0, 0, 0])], grid(4, 4, 4, window=(0.25, 1, 1, 1)))
        with self.assertRaisesRegex(ValueError, "underflows"):
            analyze_pcm_chunks([(0, [0, lo])], g)
        p = analyze_pcm_chunks([(0, [lo, lo])], g).novelty[0]
        self.assertEqual(p.frame.weighted_rms, lo)


class MatchingTests(unittest.TestCase):
    def test_earliest_feasible_maximizes_matches_in_ambiguous_window(self):
        # Half-samples at 1 kHz put each recorded millisecond at twice its value.
        m = match_onsets([200, 280], [250, 320], tolerance_sample_twice=50,
                         eligible_interval_twice=(0, 400))
        self.assertEqual([(p.reference_index, p.estimate_index, p.error_sample_twice) for p in m.matches],
                         [(0, 0, 50), (1, 1, 40)])
        self.assertEqual((m.true_positives, m.false_positives, m.false_negatives), (2, 0, 0))
        self.assertEqual((m.precision, m.recall, m.f1), (1, 1, 1))

    def test_double_detection_counts_one_false_positive_and_signed_error(self):
        m = match_onsets([2000], [2020, 1980], tolerance_sample_twice=40,
                         eligible_interval_twice=(1900, 2200))
        self.assertEqual(m.matches[0].estimate_index, 1)
        self.assertEqual(m.matches[0].error_sample_twice, -20)
        self.assertEqual(m.unmatched_estimates, (0,))
        self.assertEqual((m.precision, m.recall, m.f1), (F(1, 2), 1, F(2, 3)))

    def test_duplicate_times_stable_at_inclusive_exact_boundary(self):
        origin = 2**61 + 75
        m = match_onsets([origin, origin], [origin + 2, origin + 1, origin + 1],
                         tolerance_sample_twice=1, eligible_interval_twice=(origin, origin + 4))
        self.assertEqual([(x.reference_index, x.estimate_index) for x in m.matches], [(0, 1), (1, 2)])
        self.assertEqual(m.unmatched_estimates, (0,))

    def test_empty_metric_denominators_and_eligible_interval(self):
        for refs, estimates, expected in (
            ([], [], (None, None, None)), ([1], [], (None, 0, 0)),
            ([], [1], (0, None, 0)), ([1], [3], (0, 0, 0)),
        ):
            m = match_onsets(refs, estimates, tolerance_sample_twice=0, eligible_interval_twice=(1, 4))
            self.assertEqual((m.precision, m.recall, m.f1), expected)
        for refs, est, tolerance, span in (
            ([0], [], 0, (1, 4)), ([], [4], 0, (1, 4)),
            ([1.0], [], 0, (1, 4)), ([True], [], 0, (1, 4)),
            ([], [], -1, (1, 4)), ([], [], 0, (4, 4)),
        ):
            with self.subTest(refs=refs, est=est, tolerance=tolerance, span=span), self.assertRaises(ValueError):
                match_onsets(refs, est, tolerance_sample_twice=tolerance, eligible_interval_twice=span)

    def test_exhaustive_small_matching_against_unordered_assignments(self):
        def maximum(labels, estimates, tolerance):
            if not labels:
                return 0
            possibilities = [maximum(labels[1:], estimates, tolerance)]
            for j, candidate in enumerate(estimates):
                if abs(labels[0] - candidate) <= tolerance:
                    rest = estimates[:j] + estimates[j + 1:]
                    possibilities.append(1 + maximum(labels[1:], rest, tolerance))
            return max(possibilities)

        sets = [values for n in range(4) for values in combinations_with_replacement(range(5), n)]
        for labels in sets:
            for estimates in sets:
                for tolerance in range(4):
                    result = match_onsets(labels, estimates, tolerance_sample_twice=tolerance,
                                          eligible_interval_twice=(0, 5))
                    self.assertEqual(result.true_positives, maximum(labels, estimates, tolerance))
