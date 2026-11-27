"""Independent waveform, clock, headroom, and response-tail checks."""

from dataclasses import replace
from fractions import Fraction as F
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in ("audio-oscilloscope", "audio-dsp-test-fixtures", "audio-fft-spectrum", "audio-test-signals"):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from fixture_bank import make_fixture
from reference_dft import one_sided_amplitude
from reference_oscilloscope import MAX_SAMPLE_INDEX, ScopeEpoch
from reference_test_signals import (
    MAX_COMPONENTS, MAX_SIGNAL_FRAMES, ChannelSignal, Impulse, LogSweep, SignalPlan, Tone, render_signal,
)


ORIGIN = 2**60 + 37
RATE = 48000
EPOCH = ScopeEpoch("fixture", ORIGIN, F(RATE), "sample clock", "generator", "FS", ("mono",))
BLOCKS = (97, 233, 1024, 611, 2835)
FIR = (0, 0, 0, 0.5, -0.25, 0.125)


def plan(*components, count=4800, s=ORIGIN, **settings):
    return SignalPlan(EPOCH, s, count, (ChannelSignal(components),), **settings)


def samples(spec, **bounds):
    return render_signal(spec, **bounds).planes[0]


def rms(values):
    return math.sqrt(math.fsum(x*x for x in values)/len(values))


def dft_bin(values, nfft, index):
    angle = -math.tau*index/nfft
    return complex(
        math.fsum(v * math.cos(angle*j) for j, v in enumerate(values)),
        math.fsum(v * math.sin(angle*j) for j, v in enumerate(values)),
    )


def apply_fir(values):
    return tuple(math.fsum(h*values[n-k] for k, h in enumerate(FIR) if 0 <= n-k < len(values))
                 for n in range(len(values) + len(FIR) - 1))


def subspan_starts(start, sizes):
    for size in sizes:
        yield start, size
        start += size


class ClockTests(unittest.TestCase):
    def test_independent_blocks_preserve_a_large_origin_tone(self):
        spec = plan(Tone(1000, 0.5))
        whole = render_signal(spec)
        blocks = [render_signal(spec, start_sample=start, frame_count=count)
                  for start, count in subspan_starts(ORIGIN, BLOCKS)]
        joined = tuple(x for block in blocks for x in block.planes[0])
        self.assertTrue(joined == whole.planes[0], "tone block replay changed the samples")
        self.assertEqual(blocks[-1].end_sample_exclusive, ORIGIN + 4800)
        self.assertTrue(all(b.plan is spec and b.generator_id == "audio-test-signals-v1" for b in blocks))
        self.assertAlmostEqual(whole.planes[0][1], 0.5*math.sin(math.pi/24), delta=1e-16)
        self.assertEqual(float(ORIGIN + 1), float(ORIGIN))

    def test_crop_preserves_the_original_phase_and_aperture(self):
        spec = plan(Tone(F(2005, 2), 0.75, F(3, 14)))
        whole = samples(spec)
        start = ORIGIN + 299
        self.assertEqual(samples(spec, start_sample=start, frame_count=23), whole[299:322])
        self.assertEqual(samples(spec, start_sample=start), whole[299:])
        self.assertNotEqual(whole[299], whole[0])

    def test_active_origin_and_guards_have_exact_support(self):
        spec = plan(Tone(12000, 0.5, F(1, 4)), count=4, s=ORIGIN+3,
                    leading_guard_frames=3, tail_guard_frames=2)
        block = render_signal(spec)
        self.assertEqual((spec.active_start_sample, spec.active_end_sample_exclusive), (ORIGIN+3, ORIGIN+7))
        self.assertEqual((block.start_sample, block.end_sample_exclusive), (ORIGIN, ORIGIN+9))
        self.assertEqual(block.planes[0], (0, 0, 0, 0.5, 0, -0.5, 0, 0, 0))
        self.assertEqual(block.sample_peaks, (0.5,))
        self.assertEqual(samples(spec, start_sample=ORIGIN+2, frame_count=7), block.planes[0][2:])

    def test_crops_wholly_inside_a_guard_remain_zero(self):
        spec = plan(Impulse(0, 1), count=1, s=ORIGIN+8,
                    leading_guard_frames=8, tail_guard_frames=7)
        self.assertEqual(samples(spec, start_sample=ORIGIN+2, frame_count=3), (0.0,)*3)
        self.assertEqual(samples(spec, start_sample=ORIGIN+11, frame_count=2), (0.0,)*2)

    def test_end_exclusive_can_equal_the_maximum_sample_boundary(self):
        epoch = replace(EPOCH, origin_sample=MAX_SAMPLE_INDEX-2)
        spec = SignalPlan(epoch, MAX_SAMPLE_INDEX-2, 1,
                          (ChannelSignal((Impulse(0, 0.5),)),), tail_guard_frames=1)
        block = render_signal(spec)
        self.assertEqual(block.end_sample_exclusive, MAX_SAMPLE_INDEX)
        self.assertEqual(block.planes[0], (0.5, 0.0))

    def test_phase_can_be_many_turns_from_zero(self):
        phase = F(-2**160) + F(1, 7)
        a = samples(plan(Tone(F(48001, 7), 0.5, phase), count=19))
        b = samples(plan(Tone(F(48001, 7), 0.5, F(1, 7)), count=19))
        self.assertEqual(a, b)


class ToneTests(unittest.TestCase):
    def test_coherent_interior_amplitude_and_rms(self):
        tone = samples(plan(Tone(1000, 0.5)))
        amplitude = 2*abs(dft_bin(tone, len(tone), 100))/len(tone)
        self.assertAlmostEqual(rms(tone), 1/(2*math.sqrt(2)), delta=1e-15)
        self.assertAlmostEqual(amplitude, 0.5, delta=1e-14)
        self.assertLess(abs(dft_bin(tone, len(tone), 101))/len(tone), 1e-14)

    def test_off_bin_nearest_amplitude_and_leaked_power(self):
        tone = samples(plan(Tone(F(2005, 2), 0.5, F(1, 14))))
        near = 2*abs(dft_bin(tone, len(tone), 100))/len(tone)
        measured_rms = rms(tone)
        self.assertAlmostEqual(near, 0.4505492190530849, delta=5e-14)
        self.assertAlmostEqual(measured_rms, 0.35374853244959775, delta=5e-15)
        self.assertAlmostEqual(1-near**2/(2*measured_rms**2), 0.1889171973488495, delta=1e-13)

    def test_dc_and_even_nyquist_follow_sine_phase(self):
        for phase, level in ((0, 0), (F(1, 12), 0.25), (F(1, 4), 0.5)):
            with self.subTest(phase=phase):
                dc = samples(plan(Tone(0, 0.5, phase), count=128))
                nyquist = samples(plan(Tone(24000, 0.5, phase), count=128))
                self.assertEqual(dc, (dc[0],)*128)
                self.assertEqual(nyquist, (dc[0], -dc[0])*64)
                self.assertAlmostEqual(dc[0], level, delta=1e-16)
                self.assertAlmostEqual(one_sided_amplitude(list(nyquist), [1.0]*128)[-1], level, delta=2e-15)
                if phase == 0:
                    self.assertEqual(nyquist, (0.0,)*128)

    def test_highest_odd_bin_keeps_interior_amplitude_scaling(self):
        tone = samples(plan(Tone(F(127*RATE, 255), 0.5, F(1, 14)), count=255))
        spectrum = one_sided_amplitude(list(tone), [1.0]*255)
        self.assertAlmostEqual(spectrum[-1], 0.5, delta=1e-14)
        self.assertAlmostEqual(rms(tone), 0.5/math.sqrt(2), delta=1e-15)

    def test_phase_near_a_half_turn_retains_its_sign_and_small_magnitude(self):
        delta = F(1, 10**35)
        positive = samples(plan(Tone(0, 1, F(1, 2) - delta), count=1))[0]
        negative = samples(plan(Tone(0, 1, F(1, 2) + delta), count=1))[0]
        self.assertGreater(positive, 0)
        self.assertEqual(negative, -positive)
        self.assertAlmostEqual(positive/(math.tau*float(delta)), 1.0, delta=2e-16)

    def test_short_tones_agree_with_the_current_fixture_bank(self):
        for extra, kind in ((F(0), "coherent_sine"), (F(1, 4), "offbin_sine")):
            with self.subTest(kind=kind):
                count, k, phase = 128, 13, F(1, 14)
                tone = samples(plan(Tone((k + extra)*RATE/count, 0.5, phase), count=count))
                prior = make_fixture(kind, count, bin_index=k, phase_rad=math.tau*float(phase),
                                     origin_sample=ORIGIN)["planar_samples"][0]
                self.assertLess(max(abs(x-y) for x, y in zip(tone, prior)), 1e-14)


class MixtureAndImpulseTests(unittest.TestCase):
    def test_phase_changes_peak_with_fixed_distinct_bin_mean_square(self):
        a = plan(Tone(1000, 0.25, F(1, 4)), Tone(1370, 0.125, F(1, 4)), peak_limit=0.375)
        sine = (Tone(1000, 0.25), Tone(2000, 0.125))
        b = plan(*sine, peak_limit=0.375)
        phase_only = plan(*(replace(tone, phase_turns=F(1, 4)) for tone in sine), peak_limit=0.375)
        self.assertEqual(a.channels[0].peak_bound, F(3, 8))
        self.assertEqual(b.channels[0].peak_bound, F(3, 8))
        a_block, b_block = render_signal(a), render_signal(b)
        self.assertEqual(a_block.planes[0][0], a_block.sample_peaks[0])
        self.assertEqual(a_block.sample_peaks, (0.375,))
        self.assertAlmostEqual(b_block.sample_peaks[0], 3*math.sqrt(3)/16, delta=1e-15)
        phase_block = render_signal(phase_only)
        self.assertEqual(phase_block.sample_peaks, (0.375,))
        for block in (a_block, b_block, phase_block):
            self.assertAlmostEqual(rms(block.planes[0]), math.sqrt(5/128), delta=1e-15)

    def test_exact_peak_gate_rejects_a_sub_ulp_excess(self):
        self.assertEqual(1.0 + 2**-54, 1.0)
        channel = ChannelSignal((Tone(1000, 1.0, F(1, 4)), Tone(2000, 2**-54, F(1, 4))))
        self.assertEqual(channel.peak_bound, F(1)+F(1, 2**54))
        with self.assertRaisesRegex(ValueError, "exceeds the requested"):
            SignalPlan(EPOCH, ORIGIN, 48, (channel,), peak_limit=1)

    def test_dc_offset_is_in_the_headroom_and_energy_budget(self):
        channel = ChannelSignal((Tone(1000, 0.5, F(1, 4)),), dc=-0.25)
        spec = SignalPlan(EPOCH, ORIGIN, 48, (channel,), peak_limit=0.75)
        self.assertEqual(channel.peak_bound, F(3, 4))
        self.assertAlmostEqual(rms(samples(spec))**2, 0.25**2+0.5**2/2, delta=1e-15)
        self.assertEqual(render_signal(spec).sample_peaks, (0.75,))
        with self.assertRaises(ValueError):
            replace(spec, peak_limit=0.5)

    def test_channel_routing_preserves_polarity_and_separate_peaks(self):
        stereo = replace(EPOCH, channel_ids=("left", "right"))
        tone = Tone(1000, 0.5)
        spec = SignalPlan(stereo, ORIGIN, 48, (
            ChannelSignal((tone,)), ChannelSignal((replace(tone, amplitude=-0.5),)),
        ))
        output = render_signal(spec)
        left, right = output.planes
        self.assertEqual(right, tuple(-v for v in left))
        self.assertEqual(output.plan.epoch.channel_ids, ("left", "right"))
        self.assertEqual(output.sample_peaks, (0.5, 0.5))
        self.assertEqual(rms(left), rms(right))

    def test_peak_policy_checks_every_channel(self):
        stereo = replace(EPOCH, channel_ids=("left", "right"))
        left, right = ChannelSignal(), ChannelSignal((Tone(1000, 1.5, F(1, 4)),))
        spec = SignalPlan(stereo, ORIGIN, 48, (left, right))
        self.assertEqual(render_signal(spec).sample_peaks, (0.0, 1.5))
        with self.assertRaises(ValueError):
            replace(spec, peak_limit=1)

    def test_impulse_rms_location_and_known_fir_response(self):
        signal = samples(plan(Impulse(7, 0.5), count=128))
        self.assertEqual([(ORIGIN+j, v) for j, v in enumerate(signal) if v], [(ORIGIN+7, 0.5)])
        self.assertAlmostEqual(rms(signal), 0.5/math.sqrt(128), delta=1e-16)
        response = apply_fir(signal)
        self.assertEqual([(ORIGIN+j, v) for j, v in enumerate(response) if v],
                         [(ORIGIN+10, 0.25), (ORIGIN+11, -0.125), (ORIGIN+12, 0.0625)])
        prior = make_fixture("impulse", 128, impulse_index=7, origin_sample=ORIGIN)
        self.assertEqual(signal, tuple(prior["planar_samples"][0]))

    def test_an_impulse_at_the_last_active_sample_needs_response_tail(self):
        spec = plan(Impulse(127, 0.5), count=128, tail_guard_frames=5)
        pcm = samples(spec)
        self.assertEqual(pcm[127:], (0.5, 0, 0, 0, 0, 0))
        response = apply_fir(pcm[:128])
        self.assertEqual(len(response), len(pcm))
        self.assertFalse(any(response[:128]))
        self.assertEqual(response[130:133], (0.25, -0.125, 0.0625))

    def test_guard_silence_does_not_apply_channel_dc(self):
        spec = SignalPlan(EPOCH, ORIGIN+2, 2, (ChannelSignal(dc=0.5),),
                          leading_guard_frames=2, tail_guard_frames=2)
        self.assertEqual(samples(spec), (0.0, 0.0, 0.5, 0.5, 0.0, 0.0))
        self.assertEqual(samples(plan(count=5, peak_limit=0)), (0.0,)*5)

    def test_shared_seeded_noise_keeps_bank_identity_and_channel_levels(self):
        fixture = make_fixture("seeded_noise", 128, amplitude=0.5, seed=1729,
                               origin_sample=ORIGIN, channel_mode="stereo_antiphase")
        left, right = fixture["planar_samples"]
        self.assertEqual(fixture["provenance"], "synthetic_deterministic_lcg_v1")
        self.assertEqual(fixture["parameters"]["seed_uint32"], 1729)
        self.assertEqual(left[:3], [0.4061461193487048, -0.3946231242734939, 0.18013663543388247])
        self.assertEqual(right, [-x for x in left])
        self.assertAlmostEqual(rms(left), 0.28575989157554615, delta=1e-15)


class SweepTests(unittest.TestCase):
    def test_up_and_down_sweeps_match_integrated_phase_goldens(self):
        offsets = (0, 1, 97, 3333, 6666, 11998, 11999)
        for begin, end, phase, golden in (
            (100, 8000, 0, (0, 0.013091985682241764, 0.9615200986332161, -0.3878551216968389,
                            0.718255198836809, 0.7225349810699598, -0.23688854804702678)),
            (8000, 100, F(1, 8), (0.7071067811865476, 0.9659752893280199, 0.05460357604572272,
                                   0.5948206653483314, -0.14392041201777592, -0.8894844083382726,
                                   -0.8834233495377668)),
        ):
            with self.subTest(begin=begin, end=end):
                sweep = samples(plan(LogSweep(begin, end, 1, phase), count=12000))
                for j, target in zip(offsets, golden):
                    self.assertAlmostEqual(sweep[j], target, delta=3e-12)

    def test_sweep_restarts_each_block_from_the_same_active_time_law(self):
        spec = plan(LogSweep(100, 8000, 1), count=12000)
        whole = samples(spec)
        blocks = [samples(spec, start_sample=start, frame_count=count)
                  for start, count in subspan_starts(ORIGIN, BLOCKS + (7200,))]
        joined = tuple(v for block in blocks for v in block)
        self.assertTrue(joined == whole, "sweep block replay changed the samples")
        self.assertEqual(samples(spec, start_sample=ORIGIN+6666, frame_count=1), (whole[6666],))

    def test_adjacent_endpoints_keep_nonzero_phase_near_constant_frequency(self):
        end = F(math.nextafter(1000, math.inf))
        spec = plan(LogSweep(1000, end, 1), count=9600)
        tone = plan(Tone(1000, 1), count=9600)
        for j in (1, 1200, 2399, 4801, 8399, 9599):
            value = samples(spec, start_sample=ORIGIN+j, frame_count=1)[0]
            target = samples(tone, start_sample=ORIGIN+j, frame_count=1)[0]
            self.assertAlmostEqual(value, target, delta=3e-13)
        self.assertGreater(samples(spec, start_sample=ORIGIN+4801, frame_count=1)[0], 0.1)

    def test_equal_endpoints_use_the_exact_constant_frequency_limit(self):
        phase = F(27, 91)
        constant = samples(plan(Tone(F(2201, 2), -0.5, phase), count=231))
        swept = samples(plan(LogSweep(F(2201, 2), F(2201, 2), -0.5, phase), count=231))
        self.assertEqual(swept, constant)

    def test_wide_ascending_ratio_has_a_finite_last_sample(self):
        # The endpoint ratio is 2**1038, above the binary64 exponential range.
        low = F(RATE, 2**1040)
        spec = plan(LogSweep(low, 12000, 1), count=12000)
        block = samples(spec, start_sample=ORIGIN+11998, frame_count=2)
        for actual, target in zip(block, (-0.9480104645122006, -0.44283748116327565)):
            self.assertAlmostEqual(actual, target, delta=2e-12)

    def test_nonrepresentable_subnormal_endpoint_preserves_sweep_phase(self):
        # The exact normalized low endpoint, 3/2**1076, rounds to 2**-1074.
        low = F(3 * RATE, 2**1076)
        cases = (
            ("ascending", low, 12000, (
                (65438, 0.9998803894356549),
                (65534, -0.2888909484115301),
                (65535, -0.9646781601669617),
            )),
            ("descending", 12000, low, (
                (1, 0.9999606193497695),
                (97, -0.9617247960767547),
                (65534, 0.25485972176566834),
                (65535, 0.25485972176566834),
            )),
        )
        for direction, start, end, golden in cases:
            spec = plan(LogSweep(start, end, 1), count=MAX_SIGNAL_FRAMES)
            for offset, target in golden:
                with self.subTest(direction=direction, offset=offset):
                    value, = samples(spec, start_sample=ORIGIN + offset, frame_count=1)
                    self.assertAlmostEqual(value, target, delta=2e-12)

    def test_known_fir_sweep_recovers_complex_response_with_the_tail(self):
        excitation = samples(plan(LogSweep(100, 8000, 1), count=12000))
        full = apply_fir(excitation)
        truncated = full[:len(excitation)]
        geometry = 16384
        cut_errors = []
        for k in (86, 144, 512, 1024, 1706):
            power = dft_bin(excitation, geometry, k)
            with self.subTest(bin_index=k):
                self.assertGreater(abs(power), 1)
                expected = dft_bin(FIR, geometry, k)
                actual = dft_bin(full, geometry, k)/power
                self.assertLess(abs(actual - expected), 3e-13)
                cut_errors.append(abs(dft_bin(truncated, geometry, k)/power - expected))
        self.assertGreater(max(cut_errors), 1e-3)


class ValidationTests(unittest.TestCase):
    def test_reject_invalid_component_parameters(self):
        cases = (
            lambda: Tone(-1, 0.5), lambda: Tone(1000.0, 0.5), lambda: Tone(True, 0.5),
            lambda: Tone(1000, math.nan), lambda: Tone(1000, math.inf),
            lambda: Tone(1000, 0.5, 0.25), lambda: Impulse(-1, 1), lambda: Impulse(True, 1),
            lambda: Impulse(1, 2**1024), lambda: LogSweep(0, 8000, 1),
            lambda: LogSweep(100, -1, 1), lambda: LogSweep(100, 8000, math.inf),
        )
        for i, check in enumerate(cases):
            with self.subTest(check=i), self.assertRaises(ValueError):
                check()

    def test_reject_invalid_recipe_and_epoch_combinations(self):
        prior = plan(count=4)
        cases = (
            lambda: replace(prior, channels=()),
            lambda: replace(prior, active_frame_count=0),
            lambda: replace(prior, active_frame_count=MAX_SIGNAL_FRAMES, tail_guard_frames=1),
            lambda: replace(prior, leading_guard_frames=1),
            lambda: replace(prior, active_start_sample=MAX_SAMPLE_INDEX-3),
            lambda: replace(prior, peak_limit=math.inf),
            lambda: plan(Tone(24001, 1)), lambda: plan(LogSweep(100, 24000, 1)),
            lambda: plan(LogSweep(F(1, 2**1200), 8000, 1)),
            lambda: plan(Impulse(4, 1), count=4),
            lambda: ChannelSignal((Impulse(0, 1),)*(MAX_COMPONENTS+1)),
            lambda: ChannelSignal((Tone(1000, sys.float_info.max),), dc=sys.float_info.max),
            lambda: ChannelSignal([Tone(1000, 1)]),
        )
        for i, check in enumerate(cases):
            with self.subTest(check=i), self.assertRaises(ValueError):
                check()

    def test_reject_outside_or_empty_render_spans(self):
        spec = plan(Tone(1000, 0.5), count=16)
        for fields in (
            {"start_sample": ORIGIN-1}, {"start_sample": ORIGIN+16},
            {"start_sample": float(ORIGIN)}, {"frame_count": True}, {"frame_count": 0},
            {"start_sample": ORIGIN+10, "frame_count": 7},
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                render_signal(spec, **fields)
