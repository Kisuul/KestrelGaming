"""Independent analytical, direct-DFT and adversarial Skill #24 checks."""
from dataclasses import replace
import math
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-multiresolution-spectrum/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-fft-spectrum/scripts"))
import reference_multiresolution_spectrum as multi
from reference_dft import one_sided_dft


def config(*, sizes=(64, 16, 4), fs=64, window="rectangular", labels=("L",),
           edges=(1.0, 8.0, 16.0, 32.0), padding=1):
    return multi.SpectrumConfig(fs, labels, "fixture PCM", tuple(
        multi.ProfileConfig(name, m, max(1, m//4),
                            (1 << (m-1).bit_length())*padding, window)
        for name, m in zip(("low", "mid", "high"), sizes)), edges)


def analyze(settings, *planes, origin=0):
    analyzer = multi.MultiresolutionSpectrum(settings, epoch_id="fixture", start_sample=origin)
    return analyzer.push(origin, planes, epoch_id="fixture")


def power(frame, channel=0):
    return math.fsum(frame.channels[channel].psd)*frame.bin_spacing_hz


def independent_window(profile):
    m = profile.window_samples
    return ([1.0]*m if profile.window == "rectangular" else
            [0.5-0.5*math.cos(2*math.pi*n/m) for n in range(m)])


class AnalyticalTests(unittest.TestCase):
    def near(self, actual, expected):
        self.assertTrue(math.isclose(actual, expected, rel_tol=1e-10, abs_tol=0),
                        (actual, expected))

    def test_default_48_and_96_khz_geometry_and_real_measurements(self):
        for fs, scale in ((48000, 1), (96000, 2)):
            settings = multi.reference_config(fs, ("L", "R"), "decoded PCM")
            self.assertEqual([(p.window_samples, p.hop_samples, p.nfft) for p in settings.profiles],
                             [(8192*scale, 2048*scale, 8192*scale),
                              (2048*scale, 512*scale, 2048*scale),
                              (512*scale, 128*scale, 512*scale)])
            frames = analyze(settings, [0.0]*(10240*scale), [0.0]*(10240*scale)).composites
            self.assertEqual([c.end_sample_exclusive for c in frames],
                             [8192*scale, 10240*scale])
            self.assertEqual([f.start_sample for f in frames[0].contributors],
                             [0, 6144*scale, 7680*scale])
            self.assertEqual([f.center_sample_twice for f in frames[0].contributors],
                             [8192*scale-1, 14336*scale-1, 15872*scale-1])
            self.assertEqual([f.bin_spacing_hz for f in frames[0].contributors],
                             [5.859375, 23.4375, 93.75])
            for composite in frames:
                for frame in composite.contributors:
                    self.assertTrue(all(x == 0 for c in frame.channels for x in c.psd))

    def test_silence_keeps_exact_zero_and_no_display_floor(self):
        result = analyze(config(), [0.0]*64)
        self.assertEqual(len(result.profile_observations), 75)
        for frame in result.profile_observations:
            self.assertEqual(frame.channels[0].psd, (0.0,)*(frame.profile.nfft//2+1))
        self.assertEqual(result.composites[0].at_frequency(16, "L").density, 0)

    def test_rectangular_dc_and_logarithmic_exclusion(self):
        composite = analyze(config(), [0.25]*64).composites[0]
        for frame, selection in zip(composite.contributors, composite.selections):
            self.assertEqual(frame.channels[0].psd[0], 0.25**2*frame.profile.window_samples/64)
            self.assertTrue(all(x == 0 for x in frame.channels[0].psd[1:]))
            self.assertEqual(power(frame), 1/16)
            self.assertNotIn(0, selection.bin_indices)
        self.assertEqual(composite.at_frequency(0, "L"), multi.FrequencyReading("unavailable"))

    def test_coherent_four_sample_cycle_power_and_owner(self):
        composite = analyze(config(), [0, 0.5, 0, -0.5]*16).composites[0]
        for frame in composite.contributors:
            self.assertEqual(power(frame), 1/8)
            k = frame.profile.nfft//4
            self.assertEqual(frame.channels[0].psd[k], 0.125/frame.bin_spacing_hz)
        self.assertEqual(composite.at_frequency(16, "L"),
                         multi.FrequencyReading("ok", "high", 1, 1/128))

    def test_hann_coherent_sines_have_calibrated_integrals(self):
        settings = config(sizes=(256, 64, 16), fs=1024, window="hann_periodic")
        data = [0.5*math.sin(2*math.pi*192*n/1024) for n in range(256)]
        for frame in analyze(settings, data).composites[0].contributors:
            self.near(power(frame), 1/8)

    def test_nyquist_unique_bin_not_doubled_including_final_boundary(self):
        composite = analyze(config(), [0.25, -0.25]*32).composites[0]
        for frame in composite.contributors:
            self.assertEqual(power(frame), 1/16)
            self.assertEqual(frame.channels[0].psd[-1], (1/16)/frame.bin_spacing_hz)
            self.assertTrue(all(x == 0 for x in frame.channels[0].psd[:-1]))
        self.assertEqual(composite.at_frequency(32, "L").density, 1/256)
        self.assertIn(2, composite.selections[2].bin_indices)

    def test_hann_window_gains_enbw_and_dc_leakage(self):
        settings = config(window="hann_periodic")
        for frame in analyze(settings, [0.25]*64).composites[0].contributors:
            w, m = frame.window_properties, frame.profile.window_samples
            for actual, expected in ((w.sum_w, m/2), (w.sum_w_squared, 3*m/8),
                                     (w.coherent_gain, 0.5), (w.mean_square_gain, 0.375),
                                     (w.enbw_native_bins, 1.5), (w.enbw_hz, 96/m),
                                     (w.approximate_main_lobe_width_hz, 256/m)):
                self.near(actual, expected)
            self.near(power(frame), 1/16)
            self.assertGreater(frame.channels[0].psd[1], 0)

    def test_impulse_inclusion_at_every_contributing_interval_edge(self):
        for position in (0, 47, 48, 59, 60, 63, 64):
            data = [0.0]*65
            data[position] = 1.0
            composite = analyze(config(), data).composites[0]
            for frame in composite.contributors:
                included = frame.start_sample <= position < frame.end_sample_exclusive
                m = frame.profile.window_samples
                self.assertAlmostEqual(power(frame), 1/m if included else 0, delta=1e-15)
                expected = [(1 if k in (0, m//2) else 2)/(64*m) if included else 0
                            for k in range(m//2+1)]
                for actual, oracle in zip(frame.channels[0].psd, expected):
                    self.assertAlmostEqual(actual, oracle, delta=1e-15)

    def test_end_aligned_transient_exposes_unequal_histories(self):
        for position, expected in ((63, (1/64, 1/16, 1/4)), (47, (1/64, 0, 0))):
            data = [float(n == position) for n in range(64)]
            composite = analyze(config(), data).composites[0]
            self.assertEqual([f.end_sample_exclusive for f in composite.contributors], [64]*3)
            for frame, oracle in zip(composite.contributors, expected):
                self.assertAlmostEqual(power(frame), oracle, delta=1e-15)

    def test_hann_impulse_under_zero_endpoint_is_measured_as_zero(self):
        composite = analyze(config(window="hann_periodic"), [1]+[0]*63).composites[0]
        self.assertEqual([power(f) for f in composite.contributors], [0, 0, 0])
        data = [0]*63+[1]
        for frame in analyze(config(window="hann_periodic"), data).composites[0].contributors:
            m = frame.profile.window_samples
            w = 0.5-0.5*math.cos(2*math.pi*(m-1)/m)
            self.near(power(frame), w*w/(3*m/8))

    def test_two_nearby_tones_show_frequency_grid_and_resolution_difference(self):
        settings = config(sizes=(256, 64, 16), fs=1024, edges=(1, 100, 200, 512))
        data = [sum(0.5*math.cos(2*math.pi*f*n/1024) for f in (80, 88))
                for n in range(256)]
        low, mid, high = analyze(settings, data).composites[0].contributors
        self.near(low.channels[0].psd[20], 1/32)
        self.near(low.channels[0].psd[22], 1/32)
        self.assertAlmostEqual(low.channels[0].psd[21], 0, delta=1e-12*0.25/4)
        self.assertEqual([f.bin_spacing_hz for f in (low, mid, high)], [4, 16, 64])
        self.assertNotIn(80, high.frequencies_hz)
        self.assertNotIn(88, high.frequencies_hz)
        # Independent rectangular transform between the tones: a merged broad peak.
        for frame in (mid, high):
            x = data[frame.start_sample:frame.end_sample_exclusive]
            def magnitude_at(f):
                return abs(sum(v*complex(math.cos(-2*math.pi*f*n/1024),
                                         math.sin(-2*math.pi*f*n/1024))
                               for n, v in enumerate(x)))
            self.assertGreater(magnitude_at(84), min(magnitude_at(80), magnitude_at(88)))

    def test_padding_changes_grid_but_not_observation_or_enbw(self):
        data = [math.sin(0.37*n) for n in range(64)]
        for window in ("rectangular", "hann_periodic"):
            a = analyze(config(window=window), data).composites[0]
            b = analyze(config(window=window, padding=4), data).composites[0]
            for original, padded in zip(a.contributors, b.contributors):
                self.assertEqual(original.window_properties, padded.window_properties)
                self.assertEqual(original.start_sample, padded.start_sample)
                self.assertEqual(original.center_sample_twice, padded.center_sample_twice)
                self.assertEqual(original.bin_spacing_hz, 4*padded.bin_spacing_hz)
                self.near(power(original), power(padded))

    def test_independent_existing_direct_dft_and_parseval_each_profile(self):
        rng = random.Random(2401)
        data = [0.1+rng.uniform(-0.7, 0.7) for _ in range(80)]
        for window in ("rectangular", "hann_periodic"):
            for padding in (1, 2):
                settings = config(sizes=(60, 16, 4), window=window, padding=padding)
                # C=60 aligns with H=(15,4,1).
                for frame in analyze(settings, data).profile_observations:
                    p = frame.profile
                    x = data[frame.start_sample:frame.end_sample_exclusive]
                    w = independent_window(p)
                    pad = p.nfft-p.window_samples
                    transformed = one_sided_dft(x+[0]*pad, w+[0]*pad)
                    s2 = math.fsum(v*v for v in w)
                    energy = math.fsum((a*b)**2 for a, b in zip(x, w))/s2
                    absolute = 1e-12*energy/frame.bin_spacing_hz
                    for k, (actual, z) in enumerate(zip(frame.channels[0].psd, transformed)):
                        expected = abs(z)**2/(64*s2)*(1 if k in (0, p.nfft//2) else 2)
                        self.assertTrue(math.isclose(actual, expected, rel_tol=1e-10,
                                                     abs_tol=absolute), (k, actual, expected))
                    self.near(power(frame), energy)

    def test_off_bin_leakage_remains_visible(self):
        data = [0.5*math.sin(2*math.pi*7.25*n/64) for n in range(64)]
        for window in ("rectangular", "hann_periodic"):
            low = analyze(config(window=window), data).composites[0].contributors[0]
            self.assertGreater(low.channels[0].psd[20], 1e-12)
            self.assertGreater(sum(x > 1e-12 for x in low.channels[0].psd), 4)

    def test_seeded_white_noise_uses_actual_weighted_energy(self):
        rng = random.Random(2473)
        data = [rng.gauss(0, 0.2) for _ in range(192)]
        for window in ("rectangular", "hann_periodic"):
            for frame in analyze(config(window=window), data).profile_observations:
                w = independent_window(frame.profile)
                x = data[frame.start_sample:frame.end_sample_exclusive]
                oracle = math.fsum((a*b)**2 for a, b in zip(x, w))/math.fsum(a*a for a in w)
                self.near(power(frame), oracle)
                self.assertNotEqual(power(frame), 0.2**2)

    def test_supported_amplitude_extremes_keep_closed_form_power(self):
        for exponent in (-128, 128):
            amplitude = 2.0**exponent
            data = [0, amplitude, 0, -amplitude]*16
            for frame in analyze(config(), data).composites[0].contributors:
                self.assertEqual(power(frame), 2.0**(2*exponent-1))


class OwnershipTests(unittest.TestCase):
    def test_crossover_equality_and_adjacent_floats_exact(self):
        settings = config()
        for boundary, below, at in ((8, 0, 1), (16, 1, 2)):
            self.assertEqual(multi.owner_index(settings, math.nextafter(boundary, -math.inf)), below)
            self.assertEqual(multi.owner_index(settings, boundary), at)
            self.assertEqual(multi.owner_index(settings, math.nextafter(boundary, math.inf)), at)
        for f, expected in ((0, None), (math.nextafter(1, -math.inf), None), (1, 0),
                            (32, 2), (math.nextafter(32, math.inf), None)):
            self.assertEqual(multi.owner_index(settings, f), expected)

    def test_selected_centers_are_unique_and_reference_original_observations(self):
        result = analyze(config(), [0]*64)
        composite = result.composites[0]
        frequencies = []
        for i, (frame, selection) in enumerate(zip(composite.contributors, composite.selections)):
            self.assertTrue(any(frame is original for original in result.profile_observations))
            for k in selection.bin_indices:
                self.assertEqual(multi.owner_index(config(), frame.frequencies_hz[k]), i)
                frequencies.append(frame.frequencies_hz[k])
        self.assertEqual(len(frequencies), len(set(frequencies)))
        self.assertEqual([s.bin_indices for s in composite.selections],
                         [tuple(range(1, 8)), (2, 3), (1, 2)])
        self.assertFalse(hasattr(composite, "composite_total_power"))

    def test_unavailable_range_and_exact_frequency_request_do_not_interpolate(self):
        composite = analyze(config(edges=(1, 8, 15, 15.5)), [0]*64).composites[0]
        self.assertEqual(composite.selections[2], multi.FrequencySelection("high", "unavailable", ()))
        self.assertEqual(composite.at_frequency(15.25, "L"),
                         multi.FrequencyReading("unavailable", "high"))
        composite = analyze(config(), [0]*64).composites[0]
        # 9 exists on the low grid, but ownership forbids substituting it for mid.
        self.assertEqual(composite.at_frequency(9, "L").status, "unavailable")
        for f in (math.nextafter(8, -math.inf), math.nextafter(8, math.inf), 8.25, 33):
            self.assertEqual(composite.at_frequency(f, "L").status, "unavailable")
        self.assertEqual(composite.at_frequency(8, "L").profile_name, "mid")
        with self.assertRaises(ValueError):
            composite.at_frequency(8, "missing")

    def test_above_nyquist_selection_is_unavailable(self):
        composite = analyze(config(edges=(1, 40, 80, 100)), [0]*64).composites[0]
        self.assertEqual([s.status for s in composite.selections], ["ok", "unavailable", "unavailable"])
        self.assertEqual(composite.at_frequency(90, "L").status, "unavailable")


class StreamingTests(unittest.TestCase):
    def make(self, settings=None, origin=0):
        return multi.MultiresolutionSpectrum(settings or config(), epoch_id="a", start_sample=origin)

    def snapshot(self, analyzer):
        return (analyzer.next_sample, analyzer.epoch_id, analyzer.config, analyzer._pending,
                analyzer._timeline.accepted_blocks, analyzer._epoch_count)

    def test_many_chunk_partitions_bit_identical_with_large_exact_origin(self):
        rng = random.Random(240124)
        data = [rng.uniform(-0.5, 0.5) for _ in range(192)]
        origin = 2**53+17
        settings = config(window="hann_periodic", labels=("R", "L"))
        expected = self.make(settings, origin).push(origin, (data, data[::-1]), epoch_id="a")
        for seed in range(12):
            rng = random.Random(seed)
            stream = self.make(settings, origin)
            pos, observations, composites = 0, [], []
            while pos < len(data):
                count = min(rng.randrange(1, 26), len(data)-pos)
                self.assertEqual(stream.push(origin+pos, ([], []), epoch_id="a"), multi.PushResult())
                chunk = stream.push(origin+pos, (data[pos:pos+count],
                                    data[::-1][pos:pos+count]), epoch_id="a")
                observations.extend(chunk.profile_observations)
                composites.extend(chunk.composites)
                pos += count
            self.assertEqual(multi.PushResult(tuple(observations), tuple(composites)), expected)
            self.assertEqual(stream.next_sample, origin+192)
        for composite in expected.composites:
            for frame in composite.contributors:
                self.assertEqual(frame.center_sample_twice,
                                 2*frame.start_sample+frame.profile.window_samples-1)
                self.assertEqual(frame.end_sample_exclusive, composite.end_sample_exclusive)

    def test_multichannel_independence_antiphase_and_permutation(self):
        data = [0, 0.5, 0, -0.5]*16
        planes = (data, [-x for x in data], [x/2 for x in data])
        a = analyze(config(labels=("L", "R", "Quiet")), *planes).composites[0]
        b = analyze(config(labels=("Quiet", "L", "R")), planes[2], planes[0], planes[1]).composites[0]
        for first, second in zip(a.contributors, b.contributors):
            self.assertEqual(first.channels[0].psd, first.channels[1].psd)
            self.assertEqual(second.channels, (first.channels[2], first.channels[0], first.channels[1]))
            self.assertEqual(power(first, 2), power(first, 0)/4)

    def test_profile_order_at_ties_and_independent_noncomposite_frames(self):
        result = analyze(config(), [0]*80)
        positions = {"low": 0, "mid": 1, "high": 2}
        keys = [(f.end_sample_exclusive, positions[f.profile.name]) for f in result.profile_observations]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual([f.profile.name for f in result.profile_observations
                          if f.end_sample_exclusive == 64], ["low", "mid", "high"])
        self.assertEqual([c.end_sample_exclusive for c in result.composites], [64, 80])
        self.assertEqual(result.profile_observations[0].end_sample_exclusive, 4)

    def test_lcm_common_schedule_not_assumed_longest_hop(self):
        settings = config(sizes=(24, 12, 4))
        # H=(6,3,1), then override high to H=4: common period is 12, not 6.
        settings = replace(settings, profiles=(*settings.profiles[:2],
                           replace(settings.profiles[2], hop_samples=4)))
        self.assertEqual(settings.composite_hop_samples, 12)
        result = analyze(settings, [0]*48)
        self.assertEqual([c.end_sample_exclusive for c in result.composites], [24, 36, 48])

    def test_complete_frames_only_no_tail_padding(self):
        stream = self.make()
        result = stream.push(0, ([0]*63,), epoch_id="a")
        self.assertFalse(result.composites)
        self.assertFalse(any(f.profile.name == "low" for f in result.profile_observations))
        result = stream.push(63, ([0],), epoch_id="a")
        self.assertEqual(len(result.composites), 1)
        self.assertEqual(result.composites[0].end_sample_exclusive, 64)

    def test_zero_length_push_is_no_op_but_validates_all_metadata(self):
        stream = self.make()
        before = self.snapshot(stream)
        self.assertEqual(stream.push(0, ([],), epoch_id="a"), multi.PushResult())
        self.assertEqual(self.snapshot(stream), before)
        for args in ((1, ([],), "a"), (0, ([],), "b"), (0, (), "a"), (False, ([],), "a")):
            with self.assertRaises(ValueError):
                stream.push(args[0], args[1], epoch_id=args[2])
        self.assertEqual(self.snapshot(stream), before)

    def test_invalid_late_sample_preserves_every_profile_and_future_outputs(self):
        settings = config(labels=("L", "R"))
        stream, control = self.make(settings), self.make(settings)
        prefix, data = [0.25]*43, [0, 0.5, 0, -0.5]*16
        for analyzer in (stream, control):
            analyzer.push(0, (prefix, prefix), epoch_id="a")
        before = self.snapshot(stream)
        for bad in (math.nan, math.inf, -math.inf, True, "0", complex(0), 2**1024,
                    math.nextafter(2.0**128, math.inf), math.nextafter(2.0**-128, 0),
                    math.ulp(0.0)):
            with self.subTest(bad=str(bad)), self.assertRaises(ValueError):
                stream.push(43, (data, data[:-1]+[bad]), epoch_id="a")
            self.assertEqual(self.snapshot(stream), before)
        self.assertEqual(stream.push(43, (data, data), epoch_id="a"),
                         control.push(43, (data, data), epoch_id="a"))

    def test_gap_overlap_epoch_shape_and_type_failures_atomic(self):
        stream = self.make(config(labels=("L", "R")))
        stream.push(0, ([0]*43, [1]*43), epoch_id="a")
        before = self.snapshot(stream)
        for start, planes, epoch in ((44, ([0], [0]), "a"), (42, ([0], [0]), "a"),
                                     (43, ([0], [0]), "b"), (43, ([0], []), "a"),
                                     (43, ([0],), "a"), (43, (iter([0]), [0]), "a"),
                                     (43.0, ([0], [0]), "a"), (43, ([0], [0]), True)):
            with self.subTest(start=start, epoch=epoch), self.assertRaises(ValueError):
                stream.push(start, planes, epoch_id=epoch)
            self.assertEqual(self.snapshot(stream), before)

    def test_failure_after_low_profile_processing_is_atomic(self):
        stream, control = self.make(), self.make()
        for analyzer in (stream, control):
            analyzer.push(0, ([0.25]*43,), epoch_id="a")
        before = self.snapshot(stream)
        with patch.object(stream._plans[1], "density", side_effect=ArithmeticError("injected")):
            with self.assertRaises(ArithmeticError):
                stream.push(43, ([0.5]*64,), epoch_id="a")
        self.assertEqual(self.snapshot(stream), before)
        self.assertEqual(stream.push(43, ([0.5]*64,), epoch_id="a"),
                         control.push(43, ([0.5]*64,), epoch_id="a"))

    def test_nonfinite_and_underflow_arithmetic_failures_are_reported_atomically(self):
        stream = self.make()
        before = self.snapshot(stream)
        for bad, message in ((complex(math.nan), "nonfinite"), (complex(math.inf), "nonfinite"),
                              (complex(2.0**-600), "rounded to zero"), (0j, "collapsed")):
            with patch.object(multi, "_fft", return_value=[bad]*64):
                with self.assertRaisesRegex(ArithmeticError, message):
                    stream.push(0, ([0.5]*64,), epoch_id="a")
            self.assertEqual(self.snapshot(stream), before)

    def test_reset_removes_every_prior_history_and_schedule(self):
        stream = self.make()
        stream.push(0, ([1]*79,), epoch_id="a")
        stream.reset_epoch("b", 2**53+1)
        self.assertEqual(self.snapshot(stream)[3], (((),),)*3)
        data = [0]*64
        expected = multi.MultiresolutionSpectrum(config(), epoch_id="b", start_sample=2**53+1)
        self.assertEqual(stream.push(2**53+1, (data,), epoch_id="b"),
                         expected.push(2**53+1, (data,), epoch_id="b"))
        before = self.snapshot(stream)
        with self.assertRaises(ValueError):
            stream.reset_epoch("a", 0)
        self.assertEqual(self.snapshot(stream), before)

    def test_reconfiguration_requires_reset_and_updates_labels_and_rate(self):
        stream = self.make()
        stream.push(0, ([1]*63,), epoch_id="a")
        updated = config(fs=128, labels=("R", "L"), window="hann_periodic")
        stream.reset_epoch("b", 1000, updated)
        composite = stream.push(1000, ([0]*64, [1]*64), epoch_id="b").composites[0]
        self.assertEqual([power(f, 0) for f in composite.contributors], [0, 0, 0])
        self.assertEqual([c.channel_label for c in composite.contributors[0].channels], ["R", "L"])
        self.assertEqual(composite.contributors[0].config.sample_rate_hz, 128)
        with self.assertRaises(AttributeError):
            stream.config = config()

    def test_callback_and_epoch_and_coordinate_limits_reject_before_work(self):
        stream = self.make()
        for data in ([0]*65537, [0]*204):
            before = self.snapshot(stream)
            with patch.object(multi, "_fft", side_effect=AssertionError("must not compute")):
                with self.assertRaises(ValueError):
                    stream.push(0, (data,), epoch_id="a")
            self.assertEqual(self.snapshot(stream), before)
        settings = config(sizes=(4, 4, 4), labels=("a", "b", "c", "d", "e", "f", "g", "h"),
                          padding=8192)
        costly = self.make(settings)
        with self.assertRaisesRegex(ValueError, "work/output"):
            costly.push(0, ([0]*8,)*8, epoch_id="a")
        self.assertEqual(costly.next_sample, 0)
        with patch.object(multi, "MAX_EPOCHS", 1), self.assertRaisesRegex(ValueError, "epoch limit"):
            stream.reset_epoch("b", 0)
        huge = self.make(origin=2**256-1)
        with self.assertRaises(ValueError):
            huge.push(2**256-1, ([0],), epoch_id="a")
        self.assertEqual(huge.next_sample, 2**256-1)


class ConfigurationTests(unittest.TestCase):
    def test_invalid_profiles_alignment_and_limits(self):
        for kwargs in (dict(nfft=12), dict(nfft=65536), dict(window_samples=3),
                       dict(window_samples=17), dict(hop_samples=0), dict(hop_samples=17),
                       dict(nfft=True), dict(window="hann_symmetric"), dict(name="")):
            baseline = dict(name="a", window_samples=16, hop_samples=4, nfft=16)
            baseline.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                multi.ProfileConfig(**baseline)
        settings = config()
        for kwargs in (dict(sample_rate_hz=True), dict(sample_rate_hz=384001),
                       dict(channel_labels=("L", "L")), dict(channel_labels=()),
                       dict(channel_labels=["L"]), dict(source_tap=" "),
                       dict(frequency_edges_hz=(0, 8, 16, 32)),
                       dict(frequency_edges_hz=(1, 16, 8, 32)),
                       dict(frequency_edges_hz=(1, 8, 16, math.nan)),
                       dict(frequency_edges_hz=(1, 8, 16, math.inf)),
                       dict(profiles=settings.profiles[:2]),
                       dict(profiles=settings.profiles[::-1]),
                       dict(profiles=(settings.profiles[0],)*3),
                       dict(profiles=(settings.profiles[0], replace(settings.profiles[1], hop_samples=5),
                                      settings.profiles[2]))):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(settings, **kwargs)
        profiles = tuple(multi.ProfileConfig(str(i), 32768, 32767-i, 32768) for i in range(3))
        with self.assertRaisesRegex(ValueError, "common-end hop"):
            replace(settings, profiles=profiles)

    def test_bad_reset_and_init_metadata(self):
        for epoch, origin in (("", 0), ("a"*129, 0), ("a", -1), ("a", True),
                              ("a", 0.0), ("a", 2**256)):
            with self.assertRaises(ValueError):
                multi.MultiresolutionSpectrum(config(), epoch_id=epoch, start_sample=origin)
        with self.assertRaises(ValueError):
            multi.MultiresolutionSpectrum(None, epoch_id="a", start_sample=0)
        with self.assertRaises(ValueError):
            multi.reference_config(44100)
        for frequency in (math.nan, math.inf, -1, True):
            with self.assertRaises(ValueError):
                multi.owner_index(config(), frequency)


def run_optional_studies():
    """Run the external differential and descriptive pink study, outside CI tests."""
    import json
    import statistics
    import scipy
    from scipy import signal
    import numpy as np
    mr = multi
    rng = random.Random(2401)
    worst_scaled = 0.0
    worst_relative = 0.0
    count = 0
    max_parseval_relative = 0.0
    for fs in (48000, 96000):
        for window in ('rectangular', 'hann_periodic'):
            for padding in (1, 2):
                base = mr.reference_config(fs, ('L', 'R'), 'independent differential')
                settings = replace(base, profiles=tuple(replace(p, window=window, nfft=p.nfft*padding)
                                                         for p in base.profiles))
                length = 10240*(fs//48000)
                planes = tuple([rng.uniform(-0.8, 0.8)+0.1*math.sin(2*math.pi*233.3*n/fs)
                                for n in range(length)] for _ in range(2))
                origin = 2**53+11
                analyzer = mr.MultiresolutionSpectrum(settings, epoch_id='diff', start_sample=origin)
                result = analyzer.push(origin, planes, epoch_id='diff')
                for frame in result.profile_observations:
                    p = frame.profile
                    w = (np.ones(p.window_samples) if window == 'rectangular' else
                         signal.windows.hann(p.window_samples, sym=False))
                    for c, plane in enumerate(planes):
                        x = np.asarray(plane[frame.start_sample-origin:frame.end_sample_exclusive-origin])
                        f, expected = signal.periodogram(x, fs=fs, window=w, nfft=p.nfft,
                            detrend=False, return_onesided=True, scaling='density')
                        assert np.array_equal(f, frame.frequencies_hz)
                        actual = np.asarray(frame.channels[c].psd)
                        energy = float(np.sum((x*w)**2)/np.sum(w*w))
                        abs_bound = 1e-12*energy/frame.bin_spacing_hz
                        assert np.all(np.abs(actual-expected) <= abs_bound+1e-10*np.abs(expected))
                        worst_scaled = max(worst_scaled, float(np.max(np.abs(actual-expected)))/(energy/frame.bin_spacing_hz))
                        mask = expected > np.max(expected)*1e-8
                        worst_relative = max(worst_relative, float(np.max(np.abs((actual[mask]-expected[mask])/expected[mask]))))
                        max_parseval_relative = max(max_parseval_relative, abs(math.fsum(actual)*frame.bin_spacing_hz-energy)/energy)
                        count += 1
    print(json.dumps(dict(scipy=scipy.__version__, profile_channel_comparisons=count,
        worst_absolute_error_divided_by_power_over_df=worst_scaled,
        worst_relative_error_above_1e_minus_8_peak=worst_relative,
        worst_parseval_relative_error=max_parseval_relative), indent=2))

    rng = random.Random(24012473)
    n = 1024
    profiles = tuple(mr.ProfileConfig(name, size, size//4, size, 'hann_periodic')
                     for name, size in (('low', 1024), ('mid', 256), ('high', 64)))
    settings = mr.SpectrumConfig(1024, ('L',), 'pink study', profiles, (1, 16, 64, 512))
    bands = ((8,16),(16,32),(32,64),(64,128))
    ratios = [[] for _ in bands]
    expected = [sum((1/(2*k))*sum(weight for target,weight in
                  ((k,2/3),(k-1,1/6),(k+1,1/6)) if lo<=target<hi)
                  for k in range(1,256)) for lo,hi in bands]
    for trial in range(32):
        phases = [rng.uniform(0, math.tau) for _ in range(255)]
        data = [math.fsum(math.cos(math.tau*k*j/n+phase)/math.sqrt(k)
                         for k,phase in enumerate(phases,1)) for j in range(n)]
        analyzer = mr.MultiresolutionSpectrum(settings, epoch_id='pink', start_sample=0)
        frame = analyzer.push(0, (data,), epoch_id='pink').composites[0].contributors[0]
        for b,(lo,hi) in enumerate(bands):
            measured = math.fsum(frame.channels[0].psd[lo:hi])*frame.bin_spacing_hz
            ratios[b].append(measured/expected[b])
    print(json.dumps(dict(pink_seed=24012473, independent_random_phase_trials=32,
        window='periodic Hann M=N=1024 fs=1024',
        results=[dict(band=band, expected_power=exp, mean_ratio=statistics.mean(values),
                      sample_sd_ratio=statistics.stdev(values),
                      approximate_95_percent_half_width=2.04*statistics.stdev(values)/math.sqrt(32))
                 for band,exp,values in zip(bands,expected,ratios)]), indent=2))


if __name__ == "__main__":
    if sys.argv[1:] == ["--independent-studies"]:
        run_optional_studies()
    else:
        unittest.main()
