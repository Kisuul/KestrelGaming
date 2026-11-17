"""Analytic and adversarial tests for the Kestrel Skill #22 educational reference."""
from __future__ import annotations

from decimal import Decimal, localcontext
import importlib.util
import math
from pathlib import Path
import random
import sys
import unittest


_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "reference_envelope_dynamics",
    _ROOT / "skills/audio-envelope-dynamics/scripts/reference_envelope_dynamics.py",
)
mod = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = mod
_SPEC.loader.exec_module(mod)


def cfg(**changes):
    data = dict(sample_rate_hz=1000, channel_labels=("L", "R"), source_tap="test-post-decode",
                detector="peak", link="independent", attack_seconds=0.01,
                release_seconds=0.04)
    data.update(changes)
    return mod.EnvelopeConfig(**data)


class CoefficientTests(unittest.TestCase):
    def test_attack_step_closed_form_one_e(self):
        s = mod.EnvelopeStream(cfg(channel_labels=("L",), attack_seconds=0.1),
                               epoch_id="A", start_sample=0)
        frames = s.push(0, ([1.0] * 100,), epoch_id="A")
        for i in (0, 1, 4, 49, 99):
            self.assertAlmostEqual(frames[i].envelopes[0],
                                   -math.expm1(-(i + 1) / 100.0), delta=5e-15)
        self.assertAlmostEqual(frames[-1].envelopes[0], 1 - math.exp(-1), delta=5e-15)

    def test_release_closed_form_and_state(self):
        s = mod.EnvelopeStream(cfg(channel_labels=("L",), initial_envelope=1.0,
                                       release_seconds=0.1), epoch_id="A", start_sample=0)
        a = s.push(0, ([0.0] * 100,), epoch_id="A")
        for i in (0, 1, 49, 99):
            self.assertAlmostEqual(a[i].envelopes[0], math.exp(-(i + 1) / 100),
                                   delta=5e-15)
            self.assertEqual(a[i].phases, ("release",))

    def test_impulse_first_attack_then_release(self):
        attack = -math.expm1(-1 / 10)
        s = mod.EnvelopeStream(cfg(channel_labels=("L",)), epoch_id="i", start_sample=0)
        observed = s.push(0, ([1.0, 0.0, 0.0, 0.0],), epoch_id="i")
        self.assertAlmostEqual(observed[0].envelopes[0], attack, delta=5e-16)
        self.assertEqual(observed[0].phases, ("attack",))
        for i in (1, 2, 3):
            # The test fixture uses configured release of 40 milliseconds.
            self.assertAlmostEqual(observed[i].envelopes[0],
                                   attack * math.exp(-i / 40), delta=5e-16)
            self.assertEqual(observed[i].phases, ("release",))

    def test_near_equality_uses_unrounded_amplitude_comparison(self):
        state = 0.5
        above = math.nextafter(state, math.inf)
        below = math.nextafter(state, -math.inf)
        for value, expected in ((above, "attack"), (state, "steady"),
                                (below, "release")):
            with self.subTest(value=value):
                s = mod.EnvelopeStream(cfg(channel_labels=("L",), initial_envelope=state),
                                       epoch_id="x", start_sample=0)
                result = s.push(0, ([value],), epoch_id="x")
                self.assertEqual(result[0].phases[0], expected)

    def test_time_conventions(self):
        for convention, expected in (("one_e", math.exp(-1)),
                                      ("rise_90", 0.1),
                                      ("residual_minus60_db", 0.001)):
            with self.subTest(convention=convention):
                beta = mod.one_pole_weight(1000, 0.1, convention)
                self.assertAlmostEqual((1-beta) ** 100, expected, delta=3e-14)

    def test_tau_zero_is_immediate(self):
        s = mod.EnvelopeStream(cfg(channel_labels=("L",), attack_seconds=0,
                                       release_seconds=0), epoch_id="e", start_sample=0)
        out = s.push(0, ([0.5, 0.8, 0.1, 0],), epoch_id="e")
        self.assertEqual([v.envelopes[0] for v in out], [0.5, 0.8, 0.1, 0.0])

    def test_long_finite_tau_does_not_freeze_due_to_fs_times_tau_overflow(self):
        beta = mod.one_pole_weight(48000, 1e308)
        self.assertGreater(beta, 0)
        self.assertLess(beta, 1e-300)
        self.assertTrue(math.isfinite(beta))

    def test_independently_derived_decimal_coefficient(self):
        with localcontext() as ctx:
            ctx.prec = 90
            x = -(Decimal(1) / (Decimal(48000)*Decimal("0.000123")))
            expected = 1 - x.exp()
        actual = mod.one_pole_weight(48000, 0.000123)
        # Decimal input is intentionally decimal, float API input is binary64;
        # 2e-15 covers input representation, not a gate decision.
        self.assertAlmostEqual(actual, float(expected), delta=2e-15)

    def test_invalid_config(self):
        for kwargs in ({"sample_rate_hz": True}, {"sample_rate_hz": 0},
                       {"sample_rate_hz": 10**20}, {"channel_labels": ()},
                       {"channel_labels": ("L", "L")}, {"channel_labels": ["L"]},
                       {"source_tap": ""}, {"detector": "hilbert"}, {"link": "mean"},
                       {"attack_seconds": -1}, {"release_seconds": math.inf},
                       {"attack_seconds": math.nan}, {"convention": "random"},
                       {"initial_envelope": -1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                cfg(**kwargs)

    def test_one_pole_invalid_inputs(self):
        for args in ((48000, -1), (48000, math.nan), (48000, math.inf),
                     (0, 0.1), (True, 0.1), (48000, True), (48000, 0.1, "nope")):
            with self.subTest(args=args), self.assertRaises(ValueError):
                mod.one_pole_weight(*args)


class EnvelopeTests(unittest.TestCase):
    def test_negative_polarity_and_alternating_sign(self):
        a = mod.EnvelopeStream(cfg(channel_labels=("L",)), epoch_id="a", start_sample=0)
        b = mod.EnvelopeStream(cfg(channel_labels=("L",)), epoch_id="b", start_sample=0)
        p = a.push(0, ([0.5] * 60,), epoch_id="a")
        q = b.push(0, ([(-1 if i % 2 else 1) * 0.5 for i in range(60)],), epoch_id="b")
        self.assertEqual([f.envelopes for f in p], [f.envelopes for f in q])

    def test_no_hidden_dc_removal(self):
        s = mod.EnvelopeStream(cfg(channel_labels=("L",), attack_seconds=0),
                               epoch_id="a", start_sample=0)
        self.assertEqual(s.push(0, ([0.25],), epoch_id="a")[0].envelopes, (0.25,))

    def test_rms_step_is_sqrt_of_energy_response(self):
        s = mod.EnvelopeStream(cfg(channel_labels=("L",), detector="rms",
                                       attack_seconds=0.1), epoch_id="a", start_sample=0)
        a = s.push(0, ([1] * 100,), epoch_id="a")
        for i in (0, 1, 25, 99):
            self.assertAlmostEqual(a[i].envelopes[0],
                                   math.sqrt(1-math.exp(-(i+1)/100)), delta=4e-15)
        self.assertGreater(a[-1].envelopes[0], 1-math.exp(-1))

    def test_rms_large_finite_without_square_overflow(self):
        huge = sys.float_info.max
        s = mod.EnvelopeStream(cfg(channel_labels=("L",), detector="rms",
                                       attack_seconds=0), epoch_id="x", start_sample=0)
        f = s.push(0, ([huge, huge],), epoch_id="x")
        self.assertEqual(f[0].envelopes[0], huge)
        self.assertEqual(f[-1].envelopes[0], huge)

    def test_rms_moderate_against_decimal_energy_recurrence(self):
        s = mod.EnvelopeStream(cfg(channel_labels=("L",), detector="rms",
                                       attack_seconds=0.2, release_seconds=0.4),
                               epoch_id="x", start_sample=0)
        samples = [0.25, 0.5, 1.0, 0.8, 0.25, 0, 0.1, 0.3] * 5
        frames = s.push(0, (samples,), epoch_id="x")
        with localcontext() as ctx:
            ctx.prec = 90
            state = Decimal(0)
            a = (-(Decimal(1) / Decimal(200))).exp()
            r = (-(Decimal(1) / Decimal(400))).exp()
            for x, frame in zip(samples, frames):
                target = Decimal.from_float(float(x))
                alpha = a if target * target > state else r
                state = alpha * state + (1-alpha) * target * target
                self.assertAlmostEqual(frame.envelopes[0], float(state.sqrt()),
                                       delta=5e-15)

    def test_rms_tiny_finite_without_intermediate_zero(self):
        tiny = 1e-250
        s = mod.EnvelopeStream(cfg(channel_labels=("L",), detector="rms",
                                       attack_seconds=0), epoch_id="a", start_sample=0)
        self.assertEqual(s.push(0, ([tiny],), epoch_id="a")[0].envelopes, (tiny,))

    def test_stereo_max_link_and_antiphase(self):
        s = mod.EnvelopeStream(cfg(link="max", attack_seconds=0, release_seconds=0), epoch_id="a", start_sample=0)
        frames = s.push(0, ([1., -0.5], [-1., 0.8]), epoch_id="a")
        self.assertEqual([f.detector_targets for f in frames], [(1.,), (0.8,)])
        self.assertEqual([f.envelopes for f in frames], [(1.,), (0.8,)])

    def test_independent_is_not_max_link(self):
        s = mod.EnvelopeStream(cfg(attack_seconds=0), epoch_id="a", start_sample=0)
        self.assertEqual(s.push(0, ([1.], [0.25]), epoch_id="a")[0].envelopes,
                         (1., 0.25))

    def test_linked_permutation_and_independent_permutation(self):
        left, right = [0.25, -0.75, 0.5], [0.8, 0.1, -0.2]
        for link in ("independent", "max"):
            a = mod.EnvelopeStream(cfg(link=link), epoch_id="a", start_sample=0)
            b = mod.EnvelopeStream(cfg(link=link, channel_labels=("R", "L")),
                                   epoch_id="b", start_sample=0)
            x = a.push(0, (left, right), epoch_id="a")
            y = b.push(0, (right, left), epoch_id="b")
            for u, v in zip(x, y):
                self.assertEqual(u.envelopes, v.envelopes if link == "max"
                                 else tuple(reversed(v.envelopes)))

    def test_equality_does_not_advance_attack_release(self):
        s = mod.EnvelopeStream(cfg(channel_labels=("L",), initial_envelope=0.5),
                               epoch_id="a", start_sample=0)
        out = s.push(0, ([0.5, 0.5],), epoch_id="a")
        self.assertEqual(tuple(f.phases for f in out), (("steady",), ("steady",)))
        self.assertEqual(s.envelope, (0.5,))

    def test_callback_partition_invariance_with_large_clock(self):
        origin = (1 << 53) + 173
        rng = random.Random(20261117)
        a, b = [rng.uniform(-1, 1) for _ in range(117)], [rng.uniform(-1, 1) for _ in range(117)]
        for detector in ("peak", "rms"):
            for link in ("independent", "max"):
                with self.subTest(detector=detector, link=link):
                    conf = cfg(detector=detector, link=link)
                    single = mod.EnvelopeStream(conf, epoch_id="all", start_sample=origin)
                    split = mod.EnvelopeStream(conf, epoch_id="parts", start_sample=origin)
                    ref = single.push(origin, (a, b), epoch_id="all")
                    seen = []
                    for lo, hi in ((0, 1), (1, 9), (9, 40), (40, 88), (88, 117)):
                        seen += split.push(origin + lo, (a[lo:hi], b[lo:hi]), epoch_id="parts")
                    self.assertEqual(ref, tuple(seen))
                    self.assertEqual(single.envelope, split.envelope)
                    self.assertEqual(split.next_sample, origin + 117)
                    self.assertEqual(ref[-1].sample_index, origin + 116)

    def test_atomic_invalid_late_pcm(self):
        s = mod.EnvelopeStream(cfg(), epoch_id="a", start_sample=20)
        s.push(20, ([0.1], [0.2]), epoch_id="a")
        before = s.next_sample, s.envelope
        for args in ((21, ([0.3, math.nan], [0.2, 0.4]), "a"),
                     (21, ([0.3], [math.inf]), "a"),
                     (22, ([0.2], [0.3]), "a"),
                     (21, ([0.2], [0.3]), "wrong"),
                     (21, ([0.2, 0.3], [0.1]), "a")):
            with self.subTest(args=args), self.assertRaises(ValueError):
                s.push(args[0], args[1], epoch_id=args[2])
            self.assertEqual((s.next_sample, s.envelope), before)

    def test_atomic_recovery_after_rejection(self):
        s = mod.EnvelopeStream(cfg(), epoch_id="a", start_sample=0)
        with self.assertRaises(ValueError):
            s.push(0, ([0.1, 0.2], [0.1, math.nan]), epoch_id="a")
        result = s.push(0, ([0.1], [0.1]), epoch_id="a")
        self.assertEqual(result[0].sample_index, 0)

    def test_empty_push_no_op(self):
        s = mod.EnvelopeStream(cfg(), epoch_id="a", start_sample=17)
        self.assertEqual(s.push(17, ([], []), epoch_id="a"), ())
        self.assertEqual(s.next_sample, 17)

    def test_reset_does_not_reuse_epoch(self):
        s = mod.EnvelopeStream(cfg(), epoch_id="a", start_sample=0)
        s.push(0, ([1], [1]), epoch_id="a")
        s.reset_epoch("b", 100, cfg(attack_seconds=0))
        self.assertEqual(s.envelope, (0., 0.))
        self.assertEqual(s.push(100, ([0.4], [0.2]), epoch_id="b")[0].envelopes,
                         (0.4, 0.2))
        with self.assertRaises(ValueError):
            s.reset_epoch("a", 0)


class GainTests(unittest.TestCase):
    def test_gain_maps(self):
        self.assertEqual(mod.compressor_gain_db(-10, -20, 4), -7.5)
        self.assertEqual(mod.compressor_gain_db(-20, -20, 4), 0)
        self.assertEqual(mod.compressor_gain_db(-10, -20, 1), 0)
        self.assertEqual(mod.expander_gain_db(-30, -20, 2), -10)
        self.assertEqual(mod.expander_gain_db(-20, -20, 2), 0)
        self.assertEqual(mod.expander_gain_db(-30, -20, 1), 0)
        self.assertEqual(mod.compressor_gain_db(-math.inf, -20, 4), 0)
        self.assertEqual(mod.expander_gain_db(-math.inf, -20, 4), -math.inf)

    def test_gain_reduction_step_is_opposite_of_signal_gain(self):
        s = mod.GainReductionStream(sample_rate_hz=1000, attack_seconds=0.1,
                                    release_seconds=0.2, epoch_id="a", start_sample=0)
        out = s.push(0, [12] * 100, epoch_id="a")
        self.assertAlmostEqual(out[-1].applied_reduction_db,
                               12 * (1 - math.exp(-1)), delta=1e-13)
        self.assertLess(out[-1].gain_db, 0)
        self.assertLess(out[-1].gain_linear, 1)
        self.assertEqual(out[0].phase, "attack")
        tail = s.push(100, [0] * 200, epoch_id="a")
        self.assertAlmostEqual(tail[-1].applied_reduction_db,
                               out[-1].applied_reduction_db * math.exp(-1), delta=1e-13)
        self.assertEqual(tail[0].phase, "release")

    def test_gain_stream_partition(self):
        g1 = mod.GainReductionStream(sample_rate_hz=48000, attack_seconds=0.01,
                                     release_seconds=0.08, epoch_id="a", start_sample=8)
        g2 = mod.GainReductionStream(sample_rate_hz=48000, attack_seconds=0.01,
                                     release_seconds=0.08, epoch_id="b", start_sample=8)
        values = [0, 1, 5, 10, 5, 0, 0, 3] * 20
        self.assertEqual(g1.push(8, values, epoch_id="a"),
                         g2.push(8, values[:30], epoch_id="b")+
                         g2.push(38, values[30:], epoch_id="b"))

    def test_gain_stream_atomic(self):
        g = mod.GainReductionStream(sample_rate_hz=1000, attack_seconds=0.01,
                                    release_seconds=0.05, epoch_id="a", start_sample=0)
        with self.assertRaises(ValueError):
            g.push(0, [1, 2, -1], epoch_id="a")
        self.assertEqual(g.next_sample, 0)
        self.assertEqual(g.reduction_db, 0)
        with self.assertRaises(ValueError):
            g.push(0, [math.nan], epoch_id="a")
        self.assertEqual(g.next_sample, 0)

    def test_exponential_rms_vs_peak_and_dbfs_units(self):
        self.assertAlmostEqual(mod.amplitude_dbfs(0.5), -6.020599913279624)
        self.assertEqual(mod.amplitude_dbfs(0), -math.inf)
        with self.assertRaises(ValueError):
            mod.amplitude_dbfs(-1)
        self.assertNotEqual(mod.amplitude_dbfs(0.5), -0.5)

    def test_gain_map_bad_values(self):
        for fn in (mod.compressor_gain_db, mod.expander_gain_db):
            for args in ((-20, -30, 0.5), (math.nan, -20, 2),
                         (-20, math.nan, 2), (-20, 0, math.inf), (0, 0, True)):
                with self.subTest(fn=fn.__name__, args=args), self.assertRaises(ValueError):
                    fn(*args)

    def test_gain_frame_at_exact_clock(self):
        origin = 2**53 + 23
        g = mod.GainReductionStream(sample_rate_hz=48000, attack_seconds=0,
                                    release_seconds=0, epoch_id="a", start_sample=origin)
        frames = g.push(origin, [0, 12], epoch_id="a")
        self.assertEqual([x.sample_index for x in frames], [origin, origin+1])
        self.assertEqual(frames[-1].gain_db, -12)
        self.assertAlmostEqual(frames[-1].gain_linear, 10**(-12/20))
        self.assertEqual(g.next_sample, origin+2)


if __name__ == "__main__":
    unittest.main()
