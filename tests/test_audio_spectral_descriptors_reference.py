"""Analytic, independent, and upstream-fixture tests for skill 25."""
from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
import math
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in ("audio-spectral-descriptors", "audio-power-spectral-density",
              "audio-multiresolution-spectrum"):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))
import reference_spectral_descriptors as sd
from reference_psd import periodogram
import reference_multiresolution_spectrum as multi


def context(**updates):
    values = dict(
        clock_id="input-clock", epoch_id="capture-a", source_tap="PCM before gain",
        channel="L", amplitude_unit="V", calibration_id="voltage-v1",
        profile_id="main", window_id="rectangular", sample_rate_hz=4,
        window_samples=4, nfft=4, hop_samples=2,
    )
    values.update(updates)
    return sd.PSDContext(**values)


def frame(psd=(0, 1, 3), start=0, config=None):
    return sd.PSDFrame(context() if config is None else config, start, psd)


class DescriptorTests(unittest.TestCase):
    def close(self, actual, expected, *, rel=2e-12, abs_tol=0.0):
        self.assertIsNotNone(actual)
        self.assertTrue(math.isclose(actual, expected, rel_tol=rel, abs_tol=abs_tol),
                        (actual, expected))

    def test_two_bin_power_moments(self):
        record = sd.measure(frame(config=context(sample_rate_hz=400)))
        self.assertEqual(record.bin_indices, (1, 2))
        self.assertEqual(record.status, "ok")
        self.assertEqual(record.total_power, 400.0)
        self.assertEqual(record.centroid_hz, 175.0)
        self.close(record.spread_hz, 25 * math.sqrt(3))
        self.close(record.flatness, math.sqrt(3) / 2)
        self.close(record.crest, 1.5)
        expected_entropy = math.log(4) - 3 * math.log(3) / 4
        self.close(record.entropy_nats, expected_entropy)
        self.close(record.normalized_entropy, expected_entropy / math.log(2))

    def test_two_bin_rolloff(self):
        observation = frame(config=context(sample_rate_hz=400))
        for fraction, expected in ((Fraction(1, 4), 100), (Fraction(17, 20), 200),
                                   (Fraction(19, 20), 200)):
            with self.subTest(fraction=fraction):
                record = sd.measure(observation, sd.DescriptorOptions(rolloff_fraction=fraction))
                self.assertEqual(record.rolloff_hz, expected)

    def test_rolloff_exact_overtakes_rounded_total(self):
        fft = context(sample_rate_hz=6, nfft=6)
        cases = ((Fraction(17, 20), (9, 25, 6)),
                 (Fraction(19, 20), (47, 48, 5)),
                 (Fraction(1, 2), (2, 13, 3, 12)))
        for fraction, weights in cases:
            with self.subTest(fraction=fraction):
                if len(weights) == 4:
                    fft = replace(fft, sample_rate_hz=8, nfft=8)
                settings = sd.DescriptorOptions(rolloff_fraction=fraction)
                self.assertEqual(sd.measure(frame((0, *weights), config=fft), settings).rolloff_bin, 2)
                perturbed = (0, *weights[:-1], math.nextafter(weights[-1], math.inf))
                self.assertEqual(sd.measure(frame(perturbed, config=fft), settings).rolloff_bin, 3)

    def test_flat_and_single_occupied_bin(self):
        fft = context(sample_rate_hz=6, nfft=6)
        uniform = sd.measure(frame((0, 1, 1, 1), config=fft))
        self.assertEqual((uniform.flatness, uniform.crest), (1, 1))
        self.close(uniform.normalized_entropy, 1)
        self.close(uniform.entropy_nats, math.log(3))
        spike = sd.measure(frame((0, 1, 0, 0), config=fft))
        self.assertEqual((spike.flatness, spike.crest, spike.normalized_entropy), (0, 3, 0))
        self.assertEqual((spike.centroid_hz, spike.spread_hz, spike.entropy_nats), (1, 0, 0))

    def test_one_selected_bin_has_no_normalized_entropy(self):
        result = sd.measure(frame(), sd.DescriptorOptions(high_hz=2, include_nyquist=False))
        self.assertEqual((result.bin_indices, result.flatness, result.crest), ((1,), 1, 1))
        self.assertEqual(result.entropy_nats, 0)
        self.assertIsNone(result.normalized_entropy)
        self.assertEqual(result.underflowed, ())

    def test_empty_selection_and_silent_selection_differ(self):
        empty = sd.measure(frame(), sd.DescriptorOptions(low_hz=1.25, high_hz=1.75))
        silence = sd.measure(frame((0, 0, 0)))
        self.assertEqual((empty.status, empty.bin_indices, empty.total_power), ("empty_selection", (), None))
        self.assertEqual((silence.status, silence.bin_indices, silence.total_power), ("silent", (1, 2), 0))
        for result in (empty, silence):
            self.assertIsNone(result.centroid_hz)
            self.assertIsNone(result.flatness)
            self.assertIsNone(result.rolloff_hz)
            self.assertIsNone(result.entropy_nats)

    def test_dc_and_nyquist_are_explicit(self):
        observation = frame((4, 1, 3))
        cases = (
            (sd.DescriptorOptions(), (1, 2), 4),
            (sd.DescriptorOptions(include_dc=True), (0, 1, 2), 8),
            (sd.DescriptorOptions(high_hz=2, include_nyquist=False), (1,), 1),
            (sd.DescriptorOptions(low_hz=1.5, high_hz=2), (2,), 3),
            (sd.DescriptorOptions(high_hz=1, include_dc=True), (0,), 4),
        )
        for settings, bins, power in cases:
            with self.subTest(settings=settings):
                result = sd.measure(observation, settings)
                self.assertEqual((result.bin_indices, result.total_power), (bins, power))

    def test_half_open_edges_and_odd_terminal_bin(self):
        observation = frame((11, 1, 3), config=context(sample_rate_hz=5, nfft=5))
        self.assertEqual(sd.measure(observation, sd.DescriptorOptions(
            low_hz=1, high_hz=2, include_nyquist=True)).bin_indices, (1,))
        self.assertEqual(sd.measure(observation, sd.DescriptorOptions(
            include_nyquist=False)).bin_indices, (1, 2))

    def test_decide_internal_edge_on_the_upstream_binary64_grid(self):
        observation = frame((0, 1, 2, 3), config=context(sample_rate_hz=8, nfft=7))
        boundary = 2 * 8 / 7
        result = sd.measure(observation, sd.DescriptorOptions(low_hz=boundary))
        self.assertEqual(result.bin_indices, (2, 3))

    def test_even_psd_keeps_endpoint_mass(self):
        samples = [3/8+(-1)**n/4+(1/2)*math.cos(math.pi*n/2) for n in range(8)]
        _, density = periodogram(samples, [1.0]*8, 800, nfft=8)
        observed = frame(tuple(density), config=context(sample_rate_hz=800, nfft=8, window_samples=8))
        full = sd.measure(observed, sd.DescriptorOptions(include_dc=True))
        self.close(full.total_power, 21/64)
        self.close(sd.measure(observed).total_power, 3/16)
        self.close(density[0]*100, 9/64)
        self.close(density[2]*100, 1/8)
        self.close(density[4]*100, 1/16)

    def test_odd_psd_keeps_last_paired_bin(self):
        samples = [(5/8)*math.cos(2*math.pi*3*n/7) for n in range(7)]
        _, density = periodogram(samples, [1.0]*7, 700, nfft=7)
        result = sd.measure(frame(tuple(density), config=context(
            sample_rate_hz=700, nfft=7, window_samples=7)))
        self.assertEqual(result.rolloff_bin, 3)
        self.assertEqual(result.rolloff_hz, 300)
        self.close(result.total_power, 25/128)
        self.close(density[3]*100, 25/128)

    def test_padded_detrended_psd_matches_windowed_time_power(self):
        samples = [1/2, 1/4, -1/2, 1, 0]
        window = [1/4, 1/2, 1, 3/4, 1/2]
        mean = sum(samples)/len(samples)
        expected = math.fsum(((x-mean)*w)**2 for x, w in zip(samples, window))
        expected /= math.fsum(w*w for w in window)
        for nfft in (7, 8):
            _, density = periodogram(samples, window, 22050, nfft=nfft, detrend_mean=True)
            result = sd.measure(frame(tuple(density), config=context(
                sample_rate_hz=22050, window_samples=5, nfft=nfft, window_id="fixture-w",
                detrend="mean")), sd.DescriptorOptions(include_dc=True))
            self.close(result.total_power, expected)

    def test_flatness_and_spread_survive_ratio_underflow(self):
        hi, lo = 2.0**800, 2.0**-800
        self.assertEqual(lo/hi, 0)
        result = sd.measure(frame((0, hi, lo), config=context(sample_rate_hz=400)))
        self.close(result.flatness, 2.0**-799)
        self.close(result.spread_hz, 100*2.0**-800)
        self.assertEqual(result.centroid_hz, 100)
        self.assertIn("entropy_nats", result.underflowed)
        self.assertIsNone(result.entropy_nats)

    def test_positive_flatness_underflow_has_its_own_status(self):
        fft = context(sample_rate_hz=16, nfft=16)
        values = (0, 2.0**800, *(2.0**-800 for _ in range(7)))
        result = sd.measure(frame(values, config=fft))
        self.assertIsNone(result.flatness)
        self.assertIn("flatness", result.underflowed)
        self.assertEqual(result.status, "ok")

    def test_positive_centroid_underflow_is_not_dc(self):
        result = sd.measure(frame((2.0**800, 2.0**-800, 0)), sd.DescriptorOptions(include_dc=True))
        self.assertIsNone(result.centroid_hz)
        self.assertIn("centroid_hz", result.underflowed)
        self.close(result.spread_hz, 2.0**-800)
        self.assertEqual(result.rolloff_bin, 0)

    def test_entropy_aggregates_subnormal_terms(self):
        fft = context(sample_rate_hz=2048, nfft=2048)
        result = sd.measure(frame((0, 2.0**600, *((2.0**-486,)*1023)), config=fft))
        with localcontext() as digits:
            digits.prec = 410
            ratio = Decimal(2)**-1086
            denominator = 1 + 1023*ratio
            p, q = 1/denominator, ratio/denominator
            entropy = -(p*p.ln()+1023*q*q.ln())
            normalized = entropy/Decimal(1024).ln()
        self.assertEqual(float(q*(-q.ln())), 0.0)
        self.assertGreater(float(entropy), 0)
        self.close(result.entropy_nats, float(entropy), rel=0, abs_tol=math.ulp(0.0))
        self.close(result.normalized_entropy, float(normalized), rel=0, abs_tol=math.ulp(0.0))

    def test_seeded_comparison_with_decimal(self):
        rng = random.Random(2501)
        with localcontext() as digits:
            digits.prec = 85
            for _ in range(24):
                nfft = rng.randint(5, 24)
                fft = context(sample_rate_hz=48000, nfft=nfft)
                raw = tuple(math.ldexp(rng.uniform(.5, 1), rng.randint(-40, 40))
                            for _ in range(nfft//2+1))
                result = sd.measure(frame(raw, config=fft))
                d = tuple(Decimal.from_float(x) for x in raw[1:])
                df = Decimal(48000)/Decimal(nfft)
                centers = tuple(df*i for i in range(1, 1+len(d)))
                total = sum(d)
                mean = sum(f*w for f, w in zip(centers, d))/total
                variance = sum(w*(f-mean)**2 for f, w in zip(centers, d))/total
                entropy = -sum((v/total)*(v/total).ln() for v in d)
                geometric = (sum(v.ln() for v in d)/len(d)).exp()
                expected = (total*df, mean, variance.sqrt(), entropy, geometric/(total/len(d)))
                actual = (result.total_power, result.centroid_hz, result.spread_hz,
                          result.entropy_nats, result.flatness)
                for observed, oracle in zip(actual, expected):
                    self.close(observed, float(oracle))
                crossing = next(k for k in range(1, len(d)+1)
                                if sum(d[:k])*20 >= total*17)
                self.assertEqual(result.rolloff_bin, crossing)

    def test_maximum_transform_size(self):
        fft = context(sample_rate_hz=32768, nfft=32768)
        record = sd.measure(frame((1,)*16385, config=fft))
        self.assertEqual(len(record.bin_indices), 16384)
        self.assertEqual(record.total_power, 16384)
        self.assertEqual(record.centroid_hz, 8192.5)
        self.assertEqual(record.rolloff_bin, 13927)


class FluxTests(unittest.TestCase):
    def test_gain_only_flux(self):
        tracker = sd.DescriptorStream()
        self.assertEqual(tracker.push(frame()).flux.status, "first_frame")
        reading = tracker.push(frame((0, 2, 6), start=2)).flux
        self.assertEqual(reading.status, "ok")
        self.assertEqual(reading.previous_start_sample, 0)
        self.assertEqual(reading.shape_flux, 0)
        self.assertAlmostEqual(reading.power_flux, math.sqrt(10))

    def test_shape_redistribution(self):
        tracker = sd.DescriptorStream()
        tracker.push(frame())
        flux = tracker.push(frame((0, 3, 1), start=2)).flux
        self.assertAlmostEqual(flux.power_flux, math.sqrt(8))
        self.assertAlmostEqual(flux.shape_flux, math.sqrt(1/2))

    def test_valid_silence_in_either_flux_operand(self):
        signal, silence = (0, 1, 3), (0, 0, 0)
        for first, second in ((silence, signal), (signal, silence), (silence, silence)):
            tracker = sd.DescriptorStream()
            tracker.push(frame(first))
            result = tracker.push(frame(second, start=2)).flux
            self.assertEqual(result.status, "silence")
            self.assertIsNone(result.shape_flux)
            expected = 0 if first == second else math.sqrt(10)
            self.assertAlmostEqual(result.power_flux, expected)

    def test_empty_band_has_no_flux(self):
        tracker = sd.DescriptorStream(sd.DescriptorOptions(low_hz=1.1, high_hz=1.9))
        tracker.push(frame())
        result = tracker.push(frame(start=2))
        self.assertEqual(result.descriptors.status, "empty_selection")
        self.assertEqual(result.flux.status, "empty_selection")
        self.assertIsNone(result.flux.power_flux)
        self.assertIsNone(result.flux.shape_flux)

    def test_flux_limits_and_exact_normalization(self):
        base, delta = 2.0**600, 2.0**-470
        tracker = sd.DescriptorStream()
        tracker.push(frame((0, base, 0)))
        result = tracker.push(frame((0, base, delta), start=2)).flux
        self.assertEqual(result.power_flux, delta)
        self.assertGreater(result.shape_flux, 0)
        self.assertEqual(result.shape_flux, math.sqrt(2)*2.0**-1070)
        tracker.reset()
        tracker.push(frame((0, 2.0**800, 0)))
        result = tracker.push(frame((0, 2.0**800, 2.0**-800), start=2)).flux
        self.assertEqual(result.status, "shape_underflow")
        self.assertIsNone(result.shape_flux)
        self.assertEqual(result.power_flux, 2.0**-800)

    def test_gap_duplicate_and_late_invalid_are_atomic(self):
        origin = 2**53+7
        tracker = sd.DescriptorStream()
        first = tracker.push(frame(start=origin)).descriptors.frame
        self.assertEqual(first.end_sample_exclusive, origin+4)
        self.assertEqual(first.center_sample_twice, 2*origin+3)
        for index in (origin, origin+1, origin+3):
            with self.assertRaises(ValueError):
                tracker.push(frame(start=index))
        with self.assertRaises(ValueError):
            tracker.push(frame((0, 1, math.nan), start=origin+2))
        valid = tracker.push(frame((0, 2, 6), start=origin+2)).flux
        self.assertEqual(valid.previous_start_sample, origin)
        self.assertAlmostEqual(valid.power_flux, math.sqrt(10))
        self.assertEqual(valid.shape_flux, 0)

    def test_comparison_rejects_changed_measurement_identity(self):
        tracker = sd.DescriptorStream()
        tracker.push(frame())
        changes = dict(clock_id="different-clock", epoch_id="different-epoch", source_tap="other",
                       channel="R", amplitude_unit="Pa", calibration_id="new",
                       profile_id="short", window_id="hann", sample_rate_hz=8,
                       window_samples=3, nfft=5, hop_samples=3, detrend="mean")
        for field, value in changes.items():
            with self.subTest(field=field), self.assertRaises(ValueError):
                tracker.push(frame(start=2, config=context(**{field: value})))
        self.assertEqual(tracker.push(frame(start=2)).flux.status, "ok")

    def test_reset_primes_new_epoch(self):
        tracker = sd.DescriptorStream()
        tracker.push(frame())
        tracker.reset()
        fresh = tracker.push(frame(start=2**53+1, config=context(epoch_id="after-seek")))
        self.assertEqual(fresh.flux.status, "first_frame")
        self.assertIsNone(fresh.flux.previous_start_sample)

    def test_nonoverlapping_declared_hop(self):
        tracker = sd.DescriptorStream()
        fft = context(hop_samples=8)
        tracker.push(frame(config=fft))
        self.assertEqual(tracker.push(frame(start=8, config=fft)).flux.status, "ok")


class IntegrationTests(unittest.TestCase):
    def test_original_multiresolution_profile_can_feed_descriptors(self):
        profiles = (multi.ProfileConfig("low", 16, 4, 16, "rectangular"),
                    multi.ProfileConfig("mid", 8, 2, 8, "rectangular"),
                    multi.ProfileConfig("high", 4, 1, 4, "rectangular"))
        settings = multi.SpectrumConfig(64, ("L", "R"), "observed",
                                       profiles, (1, 5, 10, 32))
        origin = 2**53+1
        analyzer = multi.MultiresolutionSpectrum(settings, epoch_id="capture", start_sample=origin)
        left = ([1.0]*8+[0.0, 1.0, 0.0, -1.0]*3)
        right = [0.0]*20
        batch = analyzer.push(origin, (left, right), epoch_id="capture")
        self.assertEqual(len(batch.composites), 2)
        first = batch.composites[0].contributors[1]
        self.assertEqual((first.start_sample, first.end_sample_exclusive), (origin+8, origin+16))
        source = first.channels[0]
        provenance = context(sample_rate_hz=first.config.sample_rate_hz,
                             source_tap=first.config.source_tap, epoch_id=first.epoch_id,
                             channel=source.channel_label, nfft=first.profile.nfft,
                             window_samples=first.profile.window_samples,
                             window_id=first.profile.window, profile_id=first.profile.name,
                             hop_samples=first.profile.hop_samples)
        result = sd.measure(sd.PSDFrame(provenance, first.start_sample, source.psd))
        self.assertEqual(result.frame.center_sample_twice, first.center_sample_twice)
        self.assertAlmostEqual(result.total_power, 0.5)
        self.assertAlmostEqual(result.centroid_hz, 16)
        self.assertEqual(result.rolloff_hz, 16)
        with self.assertRaises(ValueError):
            sd.measure(batch.composites[0])


class ValidationTests(unittest.TestCase):
    def test_reject_bad_density_at_any_grid_index(self):
        for value in (math.nan, math.inf, -math.inf, -1, True, "0",
                      2.0**-801, 2.0**801, 1 << 1200):
            with self.subTest(value=value), self.assertRaises(ValueError):
                frame((value, 1, 3))
        for bad in ((0, 1), (0, 1, 0, 3), [0, 1, 3], iter([0, 1, 3])):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                frame(bad)

    def test_invalid_frame_clock_or_context(self):
        for position in (False, -1, 1.0, (1 << 256)-2):
            with self.subTest(position=position), self.assertRaises(ValueError):
                frame(start=position)
        with self.assertRaises(ValueError):
            sd.PSDFrame("not a context", 0, (0, 1, 3))

    def test_invalid_context(self):
        for changes in (dict(clock_id=""), dict(epoch_id=" "), dict(window_id=1),
                        dict(sample_rate_hz=4.0), dict(sample_rate_hz=384001),
                        dict(nfft=32769), dict(window_samples=5),
                        dict(hop_samples=0), dict(detrend="other")):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                context(**changes)

    def test_invalid_descriptor_options(self):
        for changes in (dict(low_hz=-1), dict(high_hz=math.nan), dict(high_hz=0),
                        dict(low_hz=1.5, high_hz=1), dict(include_dc=1),
                        dict(include_nyquist="yes"), dict(rolloff_fraction=0.85),
                        dict(rolloff_fraction=Fraction(1))):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                sd.DescriptorOptions(**changes)
        with self.assertRaises(ValueError):
            sd.measure(frame(), sd.DescriptorOptions(high_hz=3))
        with self.assertRaises(ValueError):
            sd.measure(frame(), "not options")
        with self.assertRaises(ValueError):
            sd.DescriptorStream("not options")


if __name__ == "__main__":
    unittest.main()
