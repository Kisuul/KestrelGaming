"""Independent geometry, power and sample-clock fixtures for Skill #23."""
from dataclasses import replace
from decimal import Decimal, localcontext
import importlib.util
import math
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_reference(name, skill):
    path = ROOT / "skills" / skill / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rta = load_reference("reference_fractional_octave_rta", "audio-fractional-octave-rta")
psd = load_reference("reference_psd", "audio-power-spectral-density")


def config(**changes):
    base = rta.RTAConfig(
        8_000, ("L",), "decoded PCM", 3, 64, 64, 64, window="rectangular",
        min_center_hz=20, max_center_hz=10_000,
    )
    return replace(base, **changes)


def spectrum(settings, *planes):
    stream = rta.FractionalOctaveRTA(settings, epoch_id="fixture", start_sample=23)
    frames = stream.push(23, planes, epoch_id="fixture")
    return frames[-1]


def reading(channel, index=0):
    return next(item for item in channel.bands if item.band.index == index)


def tone(peak, k):
    return [peak * math.cos(math.tau * k * n / 64) for n in range(64)]


class GeometryTests(unittest.TestCase):
    def test_band_frequencies_match_decimal_iec_geometry(self):
        with localcontext() as context:
            context.prec = 65
            ratio = Decimal(10) ** (Decimal(3) / 10)
            for fraction in (1, 3, 6, 12, 24):
                width = ratio ** (Decimal(1) / (2 * fraction))
                for index in (-6, -1, 0, 1, 4):
                    with self.subTest(fraction=fraction, index=index):
                        offset = Decimal("0.5") if fraction % 2 == 0 else Decimal(0)
                        center = Decimal(1000) * ratio ** ((index + offset) / fraction)
                        expected = (center, center / width, center * width)
                        band = rta.fractional_octave_band(fraction, index)
                        for actual, oracle in zip(
                            (band.center_hz, band.lower_hz, band.upper_hz), expected,
                        ):
                            self.assertTrue(math.isclose(actual, float(oracle), rel_tol=3e-15))

    def test_one_kilohertz_is_center_for_odd_and_shared_edge_for_even(self):
        for odd in (1, 3):
            self.assertEqual(rta.fractional_octave_band(odd, 0).center_hz, 1000)
        for even in (6, 12, 24):
            below = rta.fractional_octave_band(even, -1)
            above = rta.fractional_octave_band(even, 0)
            self.assertLess(below.center_hz, 1000)
            self.assertGreater(above.center_hz, 1000)
            self.assertEqual((below.upper_hz, above.lower_hz), (1000, 1000))

    def test_shared_edges_are_identical_and_nominal_labels_do_not_select(self):
        for fraction in (1, 3, 6, 12, 24):
            for index in range(-40, 40):
                lo = rta.fractional_octave_band(fraction, index)
                hi = rta.fractional_octave_band(fraction, index + 1)
                self.assertEqual(lo.upper_hz, hi.lower_hz)
        with self.assertRaisesRegex(ValueError, "do not select"):
            rta.FractionalOctaveRTA(config(min_center_hz=1249, max_center_hz=1251),
                                   epoch_id="a", start_sample=0)
        channel = spectrum(config(min_center_hz=1258, max_center_hz=1260), [0] * 64).channels[0]
        self.assertEqual([item.band.index for item in channel.bands], [1])

    def test_overlap_synthetic_cell_split_and_nyquist_half_cell(self):
        edges = (0.5, 1.5, 2.5, 3.5, 4.0)
        self.assertEqual(rta._bin_overlaps(0.75, 2.25, edges), (1, (0.75, 0.75)))
        self.assertEqual(rta._bin_overlaps(3.625, 4, edges), (4, (0.75,)))
        self.assertEqual(rta._bin_overlaps(1.5, 3.5, edges), (2, (1.0, 1.0)))

    def test_overlap_neighbors_of_exact_cell_boundary(self):
        edges = (0.5, 1.5, 2.5, 3.5, 4.0)
        before = math.nextafter(1.5, -math.inf)
        after = math.nextafter(1.5, math.inf)
        epsilon = 2.0 ** -52
        self.assertEqual(rta._bin_overlaps(before, after, edges), (1, (epsilon, epsilon)))
        self.assertEqual(rta._bin_overlaps(1.5, after, edges), (2, (epsilon,)))
        self.assertEqual(rta._bin_overlaps(before, 1.5, edges), (1, (epsilon,)))

    def test_center_range_preserves_one_ulp_differences(self):
        below, above = math.nextafter(1000, -math.inf), math.nextafter(1000, math.inf)
        frame = spectrum(config(min_center_hz=1000, max_center_hz=1000), [0] * 64)
        self.assertEqual([item.band.index for item in frame.channels[0].bands], [0])
        for edge in (below, above):
            with self.assertRaisesRegex(ValueError, "do not select"):
                rta.FractionalOctaveRTA(config(min_center_hz=edge, max_center_hz=edge),
                                       epoch_id="a", start_sample=0)


class PowerTests(unittest.TestCase):
    def assertPowerNear(self, actual, expected, tolerance=4e-14):
        self.assertTrue(math.isclose(actual, expected, rel_tol=tolerance),
                        f"{actual!r} != {expected!r} (relative tolerance {tolerance})")

    def test_one_kilohertz_tone_has_known_power_rms_and_level(self):
        frame = spectrum(config(), tone(0.5, 8))
        channel = frame.channels[0]
        band = reading(channel)
        self.assertEqual((frame.epoch_id, frame.start_sample, frame.end_sample_exclusive),
                         ("fixture", 23, 87))
        self.assertEqual((frame.config.source_tap, channel.channel_label), ("decoded PCM", "L"))
        self.assertEqual(band.status, "ok")
        self.assertPowerNear(channel.total_power, 0.125)
        self.assertPowerNear(band.power, 0.125)
        self.assertPowerNear(band.rms, 0.3535533905932738)
        self.assertAlmostEqual(band.level_dbfs, -9.030899869919436, delta=2e-13)

    def test_even_fraction_splits_one_kilohertz_bin_power_at_shared_edge(self):
        channel = spectrum(config(fraction=6), tone(0.5, 8)).channels[0]
        self.assertPowerNear(reading(channel, -1).power, 1 / 16)
        self.assertPowerNear(reading(channel, 0).power, 1 / 16)

    def test_three_tones_add_linearly_within_and_across_bands(self):
        samples = [sum(values) for values in zip(tone(0.5, 7), tone(0.25, 9), tone(0.75, 16))]
        channel = spectrum(config(fraction=1), samples).channels[0]
        self.assertPowerNear(reading(channel, 0).power, 0.15625)
        self.assertPowerNear(reading(channel, 1).power, 0.28125)
        self.assertPowerNear(channel.total_power, 0.4375)

    def test_channel_antiphase_and_permutation_keep_independent_power(self):
        pcm = tone(0.5, 8)
        inverse = [-x for x in pcm]
        settings = config(channel_labels=("L", "R", "Quiet"))
        frame = spectrum(settings, pcm, inverse, tone(0.25, 8))
        permuted = spectrum(replace(settings, channel_labels=("Quiet", "L", "R")),
                            tone(0.25, 8), pcm, inverse)
        self.assertEqual(frame.channels[0].bands, frame.channels[1].bands)
        self.assertEqual(permuted.channels, (frame.channels[2], *frame.channels[:2]))
        self.assertPowerNear(reading(frame.channels[2]).power, 1 / 32)

    def test_zero_and_rectangular_dc_have_no_fractional_power(self):
        for value in (0.0, 0.25):
            channel = spectrum(config(), [value] * 64).channels[0]
            self.assertEqual(channel.total_power, value ** 2)
            self.assertEqual((reading(channel).status, reading(channel).power,
                              reading(channel).rms, reading(channel).level_dbfs),
                             ("zero_power", 0.0, 0.0, -math.inf))

    def test_hann_dc_leakage_and_pre_window_mean_removal(self):
        settings = config(fraction=1, nfft=8, segment_samples=8, hop_samples=8,
                          window="hann_periodic")
        channel = spectrum(settings, [0.5] * 8).channels[0]
        # The Hann puts 1/3 of total one-sided power into k=1, whose cell
        # is [500, 1500]. The 1 kHz octave is inside that cell.
        width = 1412.5375446227544 - 707.9457843841379
        self.assertPowerNear(reading(channel).power, width / 12_000)
        self.assertPowerNear(channel.total_power, 0.25)
        detrended = replace(settings, segment_samples=7, hop_samples=7, detrend_mean=True)
        channel = spectrum(detrended, [0.1] * 7).channels[0]
        self.assertEqual((channel.total_power, reading(channel).power), (0.0, 0.0))

    def test_integrated_impulse_density_is_flat_including_nyquist_half_cell(self):
        settings = config(sample_rate_hz=2000, nfft=128, fraction=6)
        channel = spectrum(settings, [1] + [0] * 63).channels[0]
        self.assertPowerNear(channel.total_power, 1 / 64)
        band = reading(channel, -1)
        self.assertPowerNear(band.power, 2 * (1000 - 891.2509381337456) / (2000 * 64))

    def test_nyquist_equal_upper_edge_includes_unique_bin_and_larger_bands_are_marked(self):
        alternating = [1, -1] * 32
        channel = spectrum(config(sample_rate_hz=2000, fraction=6), alternating).channels[0]
        self.assertEqual((channel.total_power, reading(channel, -1).power), (1, 1))
        for item in (reading(channel, 0), reading(channel, 1)):
            self.assertEqual((item.status, item.power, item.rms, item.level_dbfs),
                             ("unavailable", None, None, None))
        for rate, status, power in ((1999, "truncated_nyquist", None),
                                    (2000, "ok", 1),
                                    (2001, "ok", 1 - 0.5 / (2001 / 128))):
            with self.subTest(rate=rate):
                band = reading(spectrum(config(sample_rate_hz=rate, fraction=6),
                                        alternating).channels[0], -1)
                self.assertEqual(band.status, status)
                if power is None:
                    self.assertIsNone(band.power)
                else:
                    self.assertPowerNear(band.power, power)

    def test_excluded_dc_cell_is_not_reported_as_silence(self):
        channel = spectrum(config(sample_rate_hz=48000), [0] * 64).channels[0]
        for index in (-5, -4):  # Near 316 and 398 Hz, below and across df/2=375 Hz.
            band = reading(channel, index)
            self.assertEqual((band.status, band.power, band.level_dbfs),
                             ("unresolved_dc", None, None))
        self.assertEqual(reading(channel, -3).status, "zero_power")

    def test_adjacent_third_bands_partition_covered_octave(self):
        rng = random.Random(901)
        pcm = [rng.uniform(-1, 1) for _ in range(60)]
        settings = config(segment_samples=60, hop_samples=60, nfft=128, window="hann_periodic")
        octave = spectrum(replace(settings, fraction=1), pcm).channels[0]
        thirds = spectrum(settings, pcm).channels[0]
        total = math.fsum(reading(thirds, i).power for i in (-1, 0, 1))
        self.assertPowerNear(reading(octave).power, total)

    def test_synthetic_inverse_frequency_density_has_equal_ideal_band_power(self):
        settings = config(sample_rate_hz=8192, nfft=8192, min_center_hz=600,
                          max_center_hz=1800)
        # With df=1 these PSD values also give the interior bin powers.
        bin_powers = (0.0, *(1.0 / k for k in range(1, 4096)), 0.5 / 4096)
        expected = math.log(10) / 10
        for projection in rta._make_projections(settings):
            band = projection.band
            low, high = band.lower_hz, band.upper_hz
            # On each cell |1/f - 1/k| <= 0.5 / (low * (low - 0.5)).
            bound = (high - low) * 0.5 / (low * (low - 0.5))
            self.assertAlmostEqual(projection.power(bin_powers), expected, delta=bound)

    def test_fft_matches_independent_direct_dft_and_parseval(self):
        rng = random.Random(1809)
        pcm = tuple(0.15 + rng.uniform(-0.7, 0.7) for _ in range(60))
        for name, detrend in (("rectangular", False), ("hann_periodic", True)):
            with self.subTest(window=name):
                settings = config(segment_samples=60, hop_samples=31, nfft=128,
                                  window=name, detrend_mean=detrend)
                window = [1.0] * 60 if name == "rectangular" else [
                    0.5 - 0.5 * math.cos(math.tau * n / 60) for n in range(60)
                ]
                _, density = psd.periodogram(pcm, window, settings.sample_rate_hz, 128, detrend)
                step = 62.5
                plan = rta._AnalysisPlan(settings)
                for actual, expected in zip(plan._bin_powers(pcm), density):
                    self.assertPowerNear(actual, expected * step, tolerance=5e-12)
                mean = sum(pcm) / len(pcm) if detrend else 0.0
                oracle = sum((w * (x - mean)) ** 2 for x, w in zip(pcm, window))
                oracle /= sum(w ** 2 for w in window)
                self.assertPowerNear(spectrum(settings, pcm).channels[0].total_power, oracle)
                self.assertEqual(settings.bin_spacing_hz, step)
                self.assertEqual(settings.segment_spacing_hz, 8000 / 60)

    def test_frozen_amplitude_bounds_preserve_small_and_large_power(self):
        settings = config(sample_rate_hz=4000)
        for exponent in (-128, 128):
            peak = 2.0 ** exponent
            channel = spectrum(settings, [peak, 0, -peak, 0] * 16).channels[0]
            self.assertEqual(reading(channel).power, 2.0 ** (2 * exponent - 1))
            self.assertEqual(reading(channel).status, "ok")

    def test_unrepresentable_positive_power_is_rejected(self):
        minimum = math.ulp(0.0)
        projection = rta._BandProjection(rta.fractional_octave_band(3, 0),
                                         first_bin=1, weights=(0.25,))
        with self.assertRaisesRegex(ArithmeticError, "band power rounded to zero"):
            projection.power((0.0, minimum))
        with self.assertRaisesRegex(ArithmeticError, "Welch power rounded to zero"):
            rta._mean_power([minimum, 0.0, 0.0])

    def test_averaging_keeps_quiet_history_after_loud_segment_leaves(self):
        settings = config(sample_rate_hz=4000, welch_segments=2)
        loud, quiet = 2.0 ** 80, 2.0 ** -80
        stream = rta.FractionalOctaveRTA(settings, epoch_id="a", start_sample=0)
        pcm = [loud, 0, -loud, 0] * 16 + [quiet, 0, -quiet, 0] * 32
        first, second = stream.push(0, (pcm,), epoch_id="a")
        self.assertEqual((first.start_sample, second.start_sample), (0, 64))
        self.assertEqual((first.end_sample_exclusive, second.end_sample_exclusive), (128, 192))
        self.assertEqual(reading(first.channels[0]).power, 2.0 ** 158)
        self.assertEqual(reading(second.channels[0]).power, 2.0 ** -161)


class StreamTests(unittest.TestCase):
    def test_rolling_overlap_and_partitions_preserve_integer_sample_grid(self):
        rng = random.Random(1287)
        pcm = [rng.uniform(-1, 1) for _ in range(203)]
        start = 2 ** 53 + 17
        settings = config(segment_samples=60, hop_samples=17, nfft=128, welch_segments=3,
                          window="hann_periodic", detrend_mean=True)
        whole = rta.FractionalOctaveRTA(settings, epoch_id="a", start_sample=start)
        split = rta.FractionalOctaveRTA(settings, epoch_id="a", start_sample=start)
        samples = 0
        actual = []
        for count in (0, 21, 39, 33, 1, 18, 71, 20):
            payload = pcm[samples:samples + count]
            actual.extend(split.push(start + samples, (payload,), epoch_id="a"))
            samples += count
        self.assertEqual(tuple(actual), whole.push(start, (pcm,), epoch_id="a"))
        self.assertEqual(split.next_sample, start + 203)
        self.assertEqual([(f.start_sample, f.end_sample_exclusive) for f in actual],
                         [(start + i, start + i + 94) for i in range(0, 110, 17)])

    def test_welch_means_power_over_exact_contributing_segments(self):
        settings = config(sample_rate_hz=4000, welch_segments=2)
        samples = [x for peak in (0.25, 0.5, 1.0) for x in [peak, 0, -peak, 0] * 16]
        stream = rta.FractionalOctaveRTA(settings, epoch_id="a", start_sample=0)
        self.assertEqual(stream.push(0, (samples[:127],), epoch_id="a"), ())
        frames = stream.push(127, (samples[127:],), epoch_id="a")
        self.assertEqual([reading(f.channels[0]).power for f in frames], [5 / 64, 5 / 16])

    def test_late_bad_input_and_clock_errors_leave_overlap_and_history_intact(self):
        settings = config(channel_labels=("L", "R"), hop_samples=32, welch_segments=2)
        control = rta.FractionalOctaveRTA(settings, epoch_id="a", start_sample=0)
        stream = rta.FractionalOctaveRTA(settings, epoch_id="a", start_sample=0)
        prefix = [0.25, 0, -0.25, 0] * 19
        data = [0, 0.5, 0, -0.5] * 25
        cursor = len(prefix)
        for analyzer in (control, stream):
            self.assertEqual(analyzer.push(0, (prefix, prefix), epoch_id="a"), ())
        for bad in (math.nan, math.inf, -math.inf, 2.0 ** -129, 2.0 ** 129, True, "0"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                stream.push(cursor, (data, data[:-1] + [bad]), epoch_id="a")
        for offset, epoch, payload in (
            (-1, "a", (data, data)), (1, "a", (data, data)), (0, "b", (data, data)),
            (0, "a", (data,)), (0, "a", (data, data[:-1])),
        ):
            with self.subTest(offset=offset, epoch=epoch), self.assertRaises(ValueError):
                stream.push(cursor + offset, payload, epoch_id=epoch)
        self.assertEqual(stream.next_sample, cursor)
        self.assertEqual(stream.push(cursor, (data, data), epoch_id="a"),
                         control.push(cursor, (data, data), epoch_id="a"))

    def test_failure_after_first_segment_is_atomic(self):
        stream = rta.FractionalOctaveRTA(config(), epoch_id="a", start_sample=8)
        samples = tone(0.5, 8)
        original = stream._plan.segment
        with patch.object(stream._plan, "segment", side_effect=[original(tuple(samples)),
                                                                 ArithmeticError("test")]):
            with self.assertRaises(ArithmeticError):
                stream.push(8, (samples * 2,), epoch_id="a")
        self.assertEqual(stream.next_sample, 8)
        frames = stream.push(8, (samples * 2,), epoch_id="a")
        self.assertEqual([frame.start_sample for frame in frames], [8, 72])

    def test_reset_drops_overlap_and_history_and_rejects_epoch_reuse(self):
        settings = config(hop_samples=32, welch_segments=2)
        stream = rta.FractionalOctaveRTA(settings, epoch_id="old", start_sample=0)
        stream.push(0, ([1.0] * 80,), epoch_id="old")
        stream.reset_epoch("new", 500)
        self.assertEqual(stream.push(500, ([0.0] * 95,), epoch_id="new"), ())
        with self.assertRaisesRegex(ValueError, "already been used"):
            stream.reset_epoch("old", 0)
        (frame,) = stream.push(595, ([0.0],), epoch_id="new")
        self.assertEqual((frame.start_sample, frame.end_sample_exclusive), (500, 596))
        self.assertEqual(frame.channels[0].total_power, 0.0)

    def test_reset_can_change_configuration_and_channel_labels(self):
        stream = rta.FractionalOctaveRTA(config(), epoch_id="mono", start_sample=0)
        stream.push(0, ([1.0] * 63,), epoch_id="mono")
        updated = config(channel_labels=("L", "R"), sample_rate_hz=4000, fraction=6)
        stream.reset_epoch("stereo", 8, updated)
        (frame,) = stream.push(8, ([1.0] * 64, [0.0] * 64), epoch_id="stereo")
        self.assertEqual(frame.config, updated)
        self.assertEqual([channel.channel_label for channel in frame.channels], ["L", "R"])
        self.assertEqual([channel.total_power for channel in frame.channels], [1.0, 0.0])

    def test_config_and_push_limits_reject_without_advancing(self):
        for invalid in (dict(fraction=True), dict(fraction=2), dict(nfft=1000),
                        dict(window="hann_symmetric"), dict(min_center_hz=math.nan),
                        dict(hop_samples=65), dict(sample_rate_hz=384001),
                        dict(welch_segments=65), dict(channel_labels=("L", "L"))):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                config(**invalid)
        settings = config(segment_samples=4, hop_samples=1)
        stream = rta.FractionalOctaveRTA(settings, epoch_id="a", start_sample=0)
        with self.assertRaisesRegex(ValueError, "more than 128 segments"):
            stream.push(0, ([0.0] * 132,), epoch_id="a")
        self.assertEqual(stream.next_sample, 0)
        self.assertEqual(len(stream.push(0, ([0.0] * 131,), epoch_id="a")), 128)


if __name__ == "__main__":
    unittest.main()
