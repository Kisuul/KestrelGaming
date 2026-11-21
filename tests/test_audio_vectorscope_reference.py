"""Vectorscope geometry, numeric range, and shared capture fixtures."""

from dataclasses import replace
from decimal import Inexact, localcontext
from fractions import Fraction
import itertools
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-oscilloscope/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-scope-triggering/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-vectorscope/scripts"))
from reference_oscilloscope import CaptureWindow, ScopeAcquisition, ScopeEpoch
from reference_scope_triggering import CaptureComplete, ScopeTrigger, TriggerSettings
from reference_vectorscope import VectorscopeViewport, ViewportPoint, project_vectorscope


EPOCH = ScopeEpoch("take-a", 0, Fraction(48_000), "input-clock", "pre-gain", "FS", ("L", "R"))
RECTANGLE = VectorscopeViewport(320, 180, 320, 180, 1)
SMALLEST = float.fromhex("0x0.0000000000001p-1022")


def project(capture, viewport=None):
    return project_vectorscope(capture, left_channel="L", right_channel="R", viewport=viewport)


def trace(pairs, viewport=None):
    left, right = zip(*pairs)
    return project(CaptureWindow(EPOCH, 0, (left, right)), viewport)


def xy(frame):
    return [(p.x, p.y) for p in frame.points]


def tone(period, lag):
    cycle = tuple(0.75 * math.cos(math.tau * n / period) for n in range(period))
    return tuple((cycle[n % period], cycle[(n - lag) % period]) for n in range(480))


class PairProjectionTests(unittest.TestCase):
    def test_signed_basis_pairs_and_measured_silence(self):
        frame = trace(((1, 1), (1, -1), (1, 0), (0, 1), (0, 0), (-1, -1)))
        root = math.sqrt(2)
        half = math.sqrt(0.5)
        self.assertEqual(xy(frame), [
            (0, root), (-root, 0), (-half, half), (half, half), (0, 0), (0, -root),
        ])
        self.assertEqual([p.sample_index for p in frame.points], list(range(6)))
        self.assertEqual((frame.start_sample, frame.end_sample_exclusive), (0, 6))
        self.assertEqual(frame.view_points, ())
        self.assertIsNone(frame.viewport)

    def test_swap_reflects_the_horizontal_axis_only(self):
        frame = CaptureWindow(EPOCH, 0, ((1, -0.5, 0.375), (-1, 0.25, 0)))
        a = project_vectorscope(frame, left_channel="L", right_channel="R")
        b = project_vectorscope(frame, left_channel="R", right_channel="L")
        self.assertEqual(xy(b), [(-x, y) for x, y in xy(a)])
        self.assertEqual((b.left_channel, b.right_channel), ("R", "L"))

    def test_explicit_ids_preserve_clock_support_and_skip_unselected_channels(self):
        origin = 2**130 + 5
        epoch = replace(
            EPOCH, origin_sample=origin, rate_hz=Fraction(48_000_000, 1001),
            channel_ids=("R", "C", "L"), tap_id="post-gain", units="V",
        )
        window = CaptureWindow(epoch, origin + 7, ((1, 0), (100, 100), (0, 1)))
        frame = project(window)
        self.assertIs(frame.epoch, epoch)
        self.assertEqual((frame.start_sample, frame.end_sample_exclusive), (origin + 7, origin + 9))
        self.assertEqual([x.sample_index for x in frame.points], [origin + 7, origin + 8])
        self.assertEqual((frame.left_channel, frame.right_channel), ("L", "R"))
        self.assertEqual(xy(frame), [(math.sqrt(0.5), math.sqrt(0.5)), (-math.sqrt(0.5), math.sqrt(0.5))])

    def test_channel_validation_rejects_missing_or_duplicate_selectors(self):
        window = CaptureWindow(EPOCH, 0, ((0,), (0,)))
        for left, right, reason in (("L", "L", "distinct"), ("C", "R", "left channel"),
                                    ("L", None, "right channel")):
            with self.subTest(left=left, right=right), self.assertRaisesRegex(ValueError, reason):
                project_vectorscope(window, left_channel=left, right_channel=right)
        with self.assertRaisesRegex(ValueError, "CaptureWindow"):
            project_vectorscope(None, left_channel="L", right_channel="R")

    def test_reference_preserves_pcm32_range_and_amplitude_units(self):
        code = 2**31 - 1
        epoch = replace(EPOCH, units="signed PCM code")
        result = project(CaptureWindow(epoch, 0, ((code, -2**31), (code, 0))))
        self.assertAlmostEqual(result.points[0].y / code, math.sqrt(2), delta=2e-16)
        self.assertGreater(result.points[1].x, 1)
        self.assertLess(result.points[1].y, -1)
        self.assertEqual(result.epoch.units, "signed PCM code")

    def test_grid_preserves_pair_energy_and_inverts(self):
        grid = (-1.25, -1, -0.75, -0.25, 0, 0.25, 0.75, 1, 1.25)
        pairs = tuple(itertools.product(grid, repeat=2))
        rotated = xy(trace(pairs))
        for (left, right), (x, y) in zip(pairs, rotated):
            with self.subTest(left=left, right=right):
                self.assertAlmostEqual((y - x) / math.sqrt(2), left, delta=5e-16)
                self.assertAlmostEqual((y + x) / math.sqrt(2), right, delta=5e-16)
                self.assertAlmostEqual(x*x + y*y, left*left + right*right, delta=9e-16)

    def test_view_cannot_invent_a_pair_from_separate_channel_maxima(self):
        paired = trace(((1, 0), (0, 1)))
        shifted = trace(((1, 1), (0, 0)))
        self.assertEqual([p.sample_index for p in paired.points], [0, 1])
        self.assertNotEqual(xy(paired), xy(shifted))
        for p in paired.points:
            self.assertAlmostEqual(p.x*p.x + p.y*p.y, 1, delta=3e-16)
        self.assertEqual(shifted.points[0].x, 0)
        self.assertAlmostEqual(shifted.points[0].y**2, 2, delta=5e-16)

    def test_quadrature_shape_and_lead_lag_direction(self):
        for delay, expected in ((12, -0.5625), (-12, 0.5625)):
            with self.subTest(delay=delay):
                points = trace(tone(48, delay)).points
                for p in points:
                    self.assertAlmostEqual(p.x*p.x + p.y*p.y, 0.5625, delta=2e-15)
                a, b = points[0], points[12]
                self.assertAlmostEqual(a.x*b.y - a.y*b.x, expected, delta=2e-15)
        points = trace(tone(24, 12)).points
        self.assertLess(max(abs(p.y) for p in points), 2e-15)

    def test_stride_can_reduce_an_accurate_circle_to_one_position(self):
        points = trace(tone(48, 12)).points
        observed = [
            len({(round(p.x, 12), round(p.y, 12)) for p in points[::stride]})
            for stride in (1, 12, 48)
        ]
        self.assertEqual(observed, [48, 4, 1])
        self.assertEqual(len(points), 480)

    def test_unbalanced_channels_and_dc_offsets_preserve_their_geometry(self):
        tilted = trace(tuple((x, x / 2) for x in (-1, -0.25, 0.25, 1)))
        horizontal = sum(p.x**2 for p in tilted.points)
        vertical = sum(p.y**2 for p in tilted.points)
        for point in tilted.points:
            self.assertAlmostEqual(point.y, -3 * point.x, delta=3e-16)
        self.assertAlmostEqual((vertical - horizontal) / (vertical + horizontal), 0.8, delta=3e-16)

        base = trace(((0.25, -0.125),)).points[0]
        common = trace(((0.75, 0.375),)).points[0]
        opposite = trace(((0.75, -0.625),)).points[0]
        self.assertEqual(common.x, base.x)
        self.assertAlmostEqual(common.y - base.y, math.sqrt(0.5), delta=2e-16)
        self.assertAlmostEqual(opposite.x - base.x, -math.sqrt(0.5), delta=2e-16)
        self.assertEqual(opposite.y, base.y)


class NumericTests(unittest.TestCase):
    def test_round_after_the_difference_for_nearly_equal_samples(self):
        right = math.nextafter(1.0, 2.0)
        frame = trace(((1, right),))
        x = frame.points[0].x
        self.assertEqual(x, math.ldexp(math.sqrt(0.5), -52))
        self.assertGreater(abs(x - (right / math.sqrt(2) - 1 / math.sqrt(2))), 6e-17)

    def test_subnormal_pair_keeps_the_original_units(self):
        raw = trace(((SMALLEST, SMALLEST), (SMALLEST, -SMALLEST), (0, SMALLEST)))
        self.assertEqual(xy(raw), [(0, SMALLEST), (-SMALLEST, 0), (SMALLEST, SMALLEST)])

    def test_large_sum_and_difference_fit_when_rotated(self):
        limit = sys.float_info.max
        s = 0.625 * limit
        self.assertTrue(math.isinf(s + s))
        p, q = trace(((s, s), (-s, s))).points
        self.assertEqual(p.x, 0)
        self.assertEqual(q.y, 0)
        self.assertEqual(p.y, q.x)
        self.assertLess(p.y, limit)
        self.assertAlmostEqual(p.y / limit, 0.625 * math.sqrt(2), delta=2e-16)

    def test_range_check_is_exact_around_the_limit(self):
        limit = sys.float_info.max
        threshold = limit / math.sqrt(2)
        safe = math.nextafter(threshold, 0)
        unsafe = math.nextafter(threshold, math.inf)
        self.assertLessEqual(2 * Fraction(safe)**2, Fraction(limit)**2)
        self.assertGreater(2 * Fraction(unsafe)**2, Fraction(limit)**2)
        self.assertTrue(math.isfinite(trace(((safe, safe),)).points[0].y))
        with self.assertRaisesRegex(ValueError, "y axis exceeds finite binary64 range at sample 0"):
            trace(((unsafe, unsafe),))

    def test_out_of_range_coordinate_names_axis_and_exact_sample(self):
        high = sys.float_info.max
        epoch = replace(EPOCH, origin_sample=2**53 + 1)
        for axis, pair in (("x", (-high, high)), ("y", (high, high))):
            frame = CaptureWindow(epoch, epoch.origin_sample, ((0, pair[0]), (0, pair[1])))
            with self.subTest(axis=axis), self.assertRaisesRegex(
                ValueError, f"{axis} axis exceeds finite binary64 range at sample {epoch.origin_sample + 1}"
            ):
                project(frame, RECTANGLE)
            self.assertEqual(frame.planes, ((0, pair[0]), (0, pair[1])))

    def test_rounding_context_is_local_to_the_projection(self):
        baseline = trace(((1, 1), (1, 0), (SMALLEST, SMALLEST)), RECTANGLE)
        with localcontext() as caller:
            caller.prec = 2
            caller.Emin = -5
            caller.Emax = 5
            caller.traps[Inexact] = True
            self.assertEqual(trace(((1, 1), (1, 0), (SMALLEST, SMALLEST)), RECTANGLE), baseline)
            self.assertEqual(caller.prec, 2)
            self.assertTrue(caller.traps[Inexact])


class ViewportTests(unittest.TestCase):
    def test_signed_screen_basis_and_inclusive_geometric_edges(self):
        pairs = ((1, 1), (1, -1), (1, 0), (0, 1), (0, 0), (-1, -1))
        viewed = trace(pairs, RECTANGLE)
        expected = ((320, 0), (140, 180), (230, 90), (410, 90), (320, 180), (320, 360))
        self.assertEqual(viewed.view_points, tuple(
            ViewportPoint(index, x, y, False, False) for index, (x, y) in enumerate(expected)
        ))
        self.assertEqual(viewed.points, trace(pairs).points)
        self.assertEqual(viewed.viewport, RECTANGLE)

    def test_one_view_gain_keeps_quadrature_round_in_both_aspects(self):
        nominal_radius_squared = (180 * 0.75 / math.sqrt(2))**2
        for geom in (VectorscopeViewport(180, 180, 180, 180, 1), RECTANGLE):
            with self.subTest(geom=geom):
                frame = trace(tone(48, 12), geom)
                for point in frame.view_points:
                    dx, dy = point.pixel_x - geom.center_x, point.pixel_y - geom.center_y
                    self.assertAlmostEqual(float(dx*dx + dy*dy), nominal_radius_squared, delta=1e-11)

    def test_above_nominal_and_out_of_view_are_independent_flags(self):
        first, second = trace(((1.25, -1.25), (1.25, 1.25)), RECTANGLE).view_points
        self.assertEqual(first, ViewportPoint(0, 95, 180, True, False))
        self.assertEqual(second, ViewportPoint(1, 320, -45, True, True))

    def test_geometry_keeps_fractional_pixels_and_checks_before_rounding(self):
        v = VectorscopeViewport(3.5, 2.5, 3.5, 2.5, 1)
        inside, outside = trace(((1, 0), (math.nextafter(1, 2), 1)), v).view_points
        self.assertEqual((inside.pixel_x, inside.pixel_y), (Fraction(9, 4), Fraction(5, 4)))
        self.assertIsInstance(inside.pixel_x, Fraction)
        self.assertFalse(inside.out_of_view)
        self.assertLess(outside.pixel_y, 0)
        self.assertTrue(outside.out_of_view)

    def test_view_scaling_handles_subnormal_and_maximum_nominal_reference(self):
        tiny = replace(RECTANGLE, nominal_full_scale=SMALLEST)
        large = replace(RECTANGLE, nominal_full_scale=sys.float_info.max)
        self.assertEqual(trace(((SMALLEST, 0),), tiny).view_points, (ViewportPoint(0, 230, 90, False, False),))
        self.assertEqual(trace(((sys.float_info.max, 0),), large).view_points, (ViewportPoint(0, 230, 90, False, False),))
        (outside,) = trace(((1, 1),), tiny).view_points
        self.assertTrue(outside.out_of_view)
        self.assertTrue(outside.over_nominal)
        self.assertLess(outside.pixel_y, -Fraction(sys.float_info.max))

    def test_invalid_viewport_values(self):
        for kwargs in (
            {"half_width": 0}, {"half_height": -1}, {"nominal_full_scale": math.nan},
            {"nominal_full_scale": 0}, {"center_x": math.inf}, {"center_y": False},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(RECTANGLE, **kwargs)
        with self.assertRaisesRegex(ValueError, "VectorscopeViewport"):
            trace(((0, 0),), object())


class CaptureIntegrationTests(unittest.TestCase):
    def test_completed_trigger_capture_projects_both_channels(self):
        epoch = replace(EPOCH, origin_sample=100)
        config = TriggerSettings("R", hysteresis=0.5, pre_frames=2, post_frames=1)
        scope = ScopeTrigger(epoch, config)
        left = (1, 0, -1, 1)
        right = (-1, -0.25, 0.75, 0.5)
        self.assertEqual(scope.ingest(epoch=epoch, start_sample=100, planes=(left[:2], right[:2])), ())
        events = scope.ingest(epoch=epoch, start_sample=102, planes=(left[2:], right[2:]))
        completion = next(x for x in events if type(x) is CaptureComplete)
        frame = project(completion.window, RECTANGLE)
        self.assertEqual(completion.trigger.detection_sample, 102)
        self.assertEqual((frame.start_sample, frame.end_sample_exclusive), (100, 104))
        self.assertEqual(xy(frame), xy(trace(tuple(zip(left, right)))))
        self.assertEqual([p.sample_index for p in frame.points], [100, 101, 102, 103])

    def test_rejected_block_and_fresh_epoch_keep_sample_pairs_coherent(self):
        epoch = replace(EPOCH, origin_sample=2**53 + 1)
        s = epoch.origin_sample
        acq = ScopeAcquisition(epoch, window_frames=4, hop_frames=2, history_frames=4)
        self.assertEqual(acq.ingest(epoch=epoch, start_sample=s, planes=((1, 0), (0, 1))), ())
        with self.assertRaises(ValueError):
            acq.ingest(epoch=epoch, start_sample=s+2, planes=((0, -1), (0, math.nan)))
        with self.assertRaisesRegex(ValueError, "gap"):
            acq.ingest(epoch=epoch, start_sample=s+3, planes=((0, -1), (0, -1)))
        (window,) = acq.ingest(epoch=epoch, start_sample=s+2, planes=((0, -1), (0, -1)))
        original = project(window)
        new = replace(epoch, epoch_id="take-b", channel_ids=("R", "L"))
        acq.reset_epoch(new)
        (fresh_window,) = acq.ingest(epoch=new, start_sample=s, planes=((0,)*4, (0,)*4))
        fresh = project(fresh_window)
        self.assertEqual(original.epoch.epoch_id, "take-a")
        self.assertNotEqual(xy(original), xy(fresh))
        self.assertEqual([p.sample_index for p in original.points], [p.sample_index for p in fresh.points])
        self.assertEqual(fresh.epoch.epoch_id, "take-b")
        self.assertEqual(xy(fresh), [(0, 0)] * 4)

    def test_every_callback_partition_preserves_indexed_geometry(self):
        left = (1, 0, 0.75, -1, 0, -1.25, 1.25, -0.75, 0, 1, -0.5, 1)
        right = (0, 1, 0.75, 1, 0, 1.25, 1.25, -0.75, -0.75, 0, 0.25, -1)
        configs = (
            (4, 2, 4, ("L", "R"), 2**53 + 1),
            (3, 3, 3, ("R", "L"), 2**53 + 1),
            (4, 7, 5, ("L", "R"), 2**226 + 5),
            (5, 1, 5, ("R", "L"), 2**226 + 5),
        )
        scale = math.sqrt(0.5)
        exact_order = [(scale*(r-l), scale*(l+r)) for l, r in zip(left, right)]
        planes = {"L": left, "R": right}
        cuts = [
            [0] + [i for i in range(1, 12) if mask & (1 << (i-1))] + [12]
            for mask in range(2**11)
        ]
        for window, hop, capacity, labels, origin in configs:
            epoch = replace(EPOCH, origin_sample=origin, channel_ids=labels)
            expected_starts = tuple(range(0, 13 - window, hop))
            for boundaries in cuts:
                capture = ScopeAcquisition(epoch, window_frames=window, hop_frames=hop, history_frames=capacity)
                frames = []
                for low, high in zip(boundaries, boundaries[1:]):
                    block = tuple(planes[label][low:high] for label in labels)
                    windows = capture.ingest(epoch=epoch, start_sample=origin+low, planes=block)
                    frames.extend(project(w) for w in windows)
                self.assertEqual([f.start_sample for f in frames], [origin+s for s in expected_starts])
                for f, start in zip(frames, expected_starts):
                    self.assertEqual(f.end_sample_exclusive, origin+start+window)
                    for i, point in enumerate(f.points, start):
                        x, y = exact_order[i]
                        self.assertEqual(point.sample_index, origin+i)
                        self.assertAlmostEqual(point.x, x, delta=6e-16)
                        self.assertAlmostEqual(point.y, y, delta=6e-16)


if __name__ == "__main__":
    unittest.main()
