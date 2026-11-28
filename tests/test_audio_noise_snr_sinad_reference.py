"""Analytic noise accounting on coherent and quiet-input fixtures."""

from dataclasses import replace
from fractions import Fraction as F
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in (
    "audio-noise-snr-sinad", "audio-thd-thdn", "audio-oscilloscope",
    "audio-power-spectral-density", "audio-test-signals", "audio-dsp-test-fixtures",
):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from fixture_bank import make_fixture
from reference_noise_snr_sinad import measure_driven_noise, measure_quiet_noise
from reference_oscilloscope import CaptureWindow, ScopeEpoch
from reference_psd import welch_mean
from reference_test_signals import ChannelSignal, SignalPlan, Tone, render_signal
from reference_thd_thdn import ThdProfile, measure_thd_thdn


RATE = 48_000
FRAMES = 480
ORIGIN = 2**60 + 37
EPOCH = ScopeEpoch("settled", ORIGIN, F(RATE), "adc", "output", "FS", ("M",))
PROFILE = ThdProfile(10)
TONES = ((10, 0.5, 0), (30, 0.005, 0), (17, 0.002, F(1, 4)))


def capture(samples, epoch=EPOCH):
    return CaptureWindow(epoch, ORIGIN, (tuple(samples),))


def rendered(tones=TONES, dc=0.05, frames=FRAMES):
    recipe = ChannelSignal(tuple(Tone(F(index * RATE, frames), level, phase)
                                 for index, level, phase in tones), dc=dc)
    block = render_signal(SignalPlan(EPOCH, ORIGIN, frames, (recipe,)))
    return CaptureWindow(EPOCH, ORIGIN, block.planes)


def seeded_noise():
    return make_fixture(
        "seeded_noise", 256, sample_rate_hz=RATE, amplitude=0.05,
        seed=470047, origin_sample=ORIGIN,
    )["planar_samples"][0]


class PowerTests(unittest.TestCase):
    def assertPower(self, actual, expected, relative=1e-10):
        self.assertTrue(math.isclose(actual, expected, rel_tol=relative), (float(actual), expected))


class DrivenNoiseTests(PowerTests):
    @classmethod
    def setUpClass(cls):
        cls.response = rendered()
        cls.report = measure_driven_noise(cls.response, PROFILE)

    def test_measured_powers_and_support(self):
        report = self.report
        self.assertEqual((report.epoch, report.channel_id), (EPOCH, "M"))
        self.assertEqual((report.start_sample, report.end_sample_exclusive), (ORIGIN, ORIGIN + FRAMES))
        self.assertEqual(report.bin_width_hz, 100)
        self.assertEqual(report.band_hz, (0, 24_000))
        self.assertEqual(report.signal_status, "qualified")
        self.assertPower(report.signal_power, 0.125)
        self.assertPower(report.distortion_power, 0.0000125)
        self.assertPower(report.noise_power, 0.000002)
        self.assertPower(report.residual_power, 0.0000145)
        self.assertPower(report.band_power, 0.1250145)
        self.assertEqual(report.excluded_spur_power, 0)
        self.assertEqual(report.band_power, report.signal_power + report.residual_power)

    def test_snr_and_sinad_use_distinct_denominators(self):
        self.assertAlmostEqual(self.report.snr_db, 47.95880017344075, places=8)
        self.assertAlmostEqual(self.report.sinad_db, 39.35542010773081, places=8)
        self.assertEqual(self.report.residual_power, self.report.noise_power + self.report.distortion_power)
        self.assertGreater(self.report.snr_db, self.report.sinad_db)

    def test_bin_roles_and_disjoint_sums(self):
        report = self.report
        self.assertEqual(report.bins[0].role, "excluded")
        self.assertFalse(report.bins[0].admitted)
        self.assertPower(report.bins[0].power, 0.0025)
        self.assertEqual(report.bins[10].role, "signal")
        self.assertEqual(report.bins[30].role, "harmonic")
        self.assertEqual(report.bins[17].role, "noise")
        for role, expected in (
            ("signal", report.signal_power), ("harmonic", report.distortion_power),
            ("noise", report.noise_power), ("snr_excluded_spur", report.excluded_spur_power),
        ):
            self.assertEqual(sum(entry.power for entry in report.bins if entry.role == role), expected)

    def test_sinad_inverts_fundamental_relative_thdn(self):
        thd = measure_thd_thdn(self.response, PROFILE)
        self.assertEqual(self.report.sinad_db, -thd.thdn_fundamental.decibels)
        self.assertNotEqual(self.report.sinad_db, -thd.thdn_total.decibels)
        equal = rendered(((10, .5, 0), (17, .5, F(1, 4))), dc=0)
        self.assertAlmostEqual(measure_driven_noise(equal, PROFILE).sinad_db, 0, places=12)
        self.assertAlmostEqual(measure_thd_thdn(equal, PROFILE).thdn_total.decibels, -3.01029995664, places=10)

    def test_spur_mask_changes_snr_and_retains_the_full_residual(self):
        data = rendered(TONES + ((21, 0.001, 0),))
        full = measure_driven_noise(data, PROFILE)
        masked = measure_driven_noise(data, PROFILE, snr_excluded_bins=(17,))
        self.assertEqual(masked.bins[17].role, "snr_excluded_spur")
        self.assertTrue(masked.bins[17].admitted)
        self.assertEqual(masked.bins[21].role, "noise")
        self.assertPower(full.noise_power, 0.0000025)
        self.assertPower(masked.noise_power, 0.0000005)
        self.assertEqual(masked.excluded_spur_power, masked.bins[17].power)
        self.assertEqual(masked.distortion_power, full.distortion_power)
        self.assertEqual(masked.residual_power, full.residual_power)
        self.assertEqual(masked.residual_power, masked.noise_power + masked.distortion_power + masked.excluded_spur_power)
        self.assertEqual(masked.sinad_db, full.sinad_db)
        self.assertAlmostEqual(masked.sinad_db, 39.20818753952378, places=8)
        self.assertAlmostEqual(full.snr_db, 46.98970004336018, places=8)
        self.assertAlmostEqual(masked.snr_db, 53.97940008672035, places=8)

    def test_band_excludes_large_spur_and_keeps_its_raw_power(self):
        data = rendered(TONES + ((125, 0.2, F(1, 4)),))
        full = measure_driven_noise(data, PROFILE)
        limited = measure_driven_noise(data, replace(PROFILE, band_hz=(400, 5000)))
        self.assertEqual(limited.bins[125].role, "excluded")
        self.assertPower(limited.bins[125].power, 0.02)
        self.assertPower(limited.noise_power, 0.000002)
        self.assertPower(full.noise_power, 0.020002)
        self.assertAlmostEqual(limited.sinad_db, self.report.sinad_db, places=8)

    def test_band_centers_are_inclusive_and_mask_outside_is_diagnostic(self):
        data = rendered(TONES + ((21, 0.001, 0),))
        profile = replace(PROFILE, band_hz=(1000, 1700))
        report = measure_driven_noise(data, profile, snr_excluded_bins=(21, 17))
        self.assertEqual(report.snr_excluded_bins, (17, 21))
        self.assertEqual(report.bins[10].role, "signal")
        self.assertEqual(report.bins[17].role, "snr_excluded_spur")
        self.assertEqual(report.bins[21].role, "excluded")
        self.assertEqual(report.excluded_spur_power, report.bins[17].power)
        self.assertPower(report.bins[21].power, 0.0000005)
        self.assertEqual(report.harmonics[1].status, "out_of_band")
        self.assertEqual(report.distortion_power, 0)
        self.assertPower(report.residual_power, 0.000002)

    def test_explicit_dc_is_residual_power(self):
        report = measure_driven_noise(self.response, replace(PROFILE, include_dc=True))
        self.assertEqual(report.bins[0].role, "noise")
        self.assertEqual(report.noise_power - self.report.noise_power, report.bins[0].power)
        self.assertEqual(report.residual_power - self.report.residual_power, report.bins[0].power)
        self.assertEqual(report.distortion_power, self.report.distortion_power)

    def test_unassigned_harmonic_bin_is_in_the_noise_term(self):
        report = measure_driven_noise(self.response, replace(PROFILE, harmonic_orders=(2,)))
        self.assertEqual(report.bins[30].role, "noise")
        self.assertEqual(report.noise_power, self.report.residual_power - report.distortion_power)
        self.assertEqual(report.residual_power, self.report.residual_power)
        self.assertEqual(report.sinad_db, self.report.sinad_db)
        self.assertAlmostEqual(report.snr_db, report.sinad_db, places=10)

    def test_above_nyquist_order_is_diagnostic(self):
        response = rendered(((80, .5, 0), (160, .003, 0), (240, .002, F(1, 4))), dc=0)
        report = measure_driven_noise(response, ThdProfile(80, (3, 4)))
        nyquist, above = report.harmonics
        self.assertEqual(nyquist.status, "admitted")
        self.assertPower(nyquist.admitted_power, .002**2)
        self.assertEqual(above.status, "above_nyquist")
        self.assertEqual(above.possible_fold_bin, 160)
        self.assertIsNone(above.admitted_power)
        self.assertEqual(report.bins[160].role, "noise")
        self.assertPower(report.noise_power, .003**2/2)

    def test_weak_noise_survives_rounded_band_total(self):
        data = rendered(((10, .5, 0), (17, 2.0**-32, F(1, 4))), dc=0)
        report = measure_driven_noise(data, PROFILE)
        self.assertEqual(float(report.band_power), float(report.signal_power))
        self.assertPower(report.noise_power, 2.0**-65, relative=2e-5)
        self.assertGreater(report.snr_db, 180)

    def test_zero_denominators_with_a_qualified_signal(self):
        report = measure_driven_noise(self.response, replace(PROFILE, band_hz=(1000, 1000)))
        self.assertEqual(report.signal_status, "qualified")
        self.assertEqual((report.noise_power, report.residual_power), (0, 0))
        self.assertEqual((report.snr_db, report.sinad_db), (math.inf, math.inf))
        self.assertEqual(report.noise_level_db(F(1, 2)), -math.inf)

    def test_no_noise_with_a_nonzero_harmonic(self):
        data = capture((.55, -.05, -.45, -.05))
        report = measure_driven_noise(data, ThdProfile(1, harmonic_orders=(2,)))
        self.assertEqual(report.noise_power, 0)
        self.assertPower(report.distortion_power, .05**2)
        self.assertEqual(report.snr_db, math.inf)
        self.assertAlmostEqual(report.sinad_db, 10*math.log10(.125/.0025), places=10)

    def test_out_of_band_signal_keeps_its_measured_power(self):
        profile = replace(PROFILE, band_hz=(1700, 3000))
        report = measure_driven_noise(self.response, profile)
        self.assertEqual(report.signal_status, "out_of_band")
        self.assertPower(report.signal_power, .125)
        self.assertEqual(report.residual_power, report.band_power)
        self.assertIsNone(report.snr_db)
        self.assertIsNone(report.sinad_db)

    def test_floor_equality_and_rejection(self):
        floor = self.report.signal_power
        equality = measure_driven_noise(self.response, replace(PROFILE, minimum_fundamental_power=floor))
        weak = measure_driven_noise(self.response, replace(PROFILE, minimum_fundamental_power=floor + 1))
        self.assertEqual(equality.signal_status, "qualified")
        self.assertEqual(equality.snr_db, self.report.snr_db)
        self.assertEqual(weak.signal_status, "below_floor")
        self.assertEqual(weak.residual_power, self.report.residual_power)
        self.assertIsNone(weak.snr_db)
        self.assertIsNone(weak.sinad_db)

    def test_zero_signal_has_unavailable_ratios(self):
        report = measure_driven_noise(capture((0,) * FRAMES), PROFILE)
        self.assertEqual(report.signal_status, "zero_power")
        self.assertEqual(report.signal_power, 0)
        self.assertEqual(report.noise_power, 0)
        self.assertEqual((report.snr_db, report.sinad_db), (None, None))

    def test_invalid_spur_masks(self):
        for mask in ((0,), (10,), (30,), (241,), (-1,), (True,), (17, 17), [17], ((17,),)):
            with self.subTest(mask=mask), self.assertRaisesRegex(ValueError, "SNR exclusion"):
                measure_driven_noise(self.response, PROFILE, snr_excluded_bins=mask)
        with self.assertRaisesRegex(ValueError, "declared harmonic"):
            measure_driven_noise(self.response, replace(PROFILE, band_hz=(900, 1200)), snr_excluded_bins=(30,))

    def test_power_of_two_gain_preserves_ratios(self):
        boosted = capture(8 * x for x in self.response.planes[0])
        report = measure_driven_noise(boosted, PROFILE)
        self.assertEqual(report.signal_power, 64 * self.report.signal_power)
        self.assertEqual(report.noise_power, 64 * self.report.noise_power)
        self.assertEqual((report.snr_db, report.sinad_db), (self.report.snr_db, self.report.sinad_db))

    def test_sub_step_quantization_loses_the_measured_signal(self):
        ideal = rendered(((10, .2, 0),), dc=0)
        quantized = tuple(round(x) for x in ideal.planes[0])
        error = tuple(y-x for y, x in zip(quantized, ideal.planes[0]))
        self.assertTrue(all(y == 0 for y in quantized))
        self.assertTrue(all(e == -x for e, x in zip(error, ideal.planes[0])))
        self.assertAlmostEqual(math.fsum(e**2 for e in error)/FRAMES, .02, places=15)
        report = measure_driven_noise(capture(quantized), PROFILE)
        self.assertEqual(report.signal_status, "zero_power")
        self.assertIsNone(report.sinad_db)


class QuietNoiseTests(PowerTests):
    def test_quiet_input_measures_noise_without_a_signal(self):
        data = capture(seeded_noise())
        report = measure_quiet_noise(data)
        dc_enabled = measure_quiet_noise(data, include_dc=True)
        self.assertEqual(report.signal_status, "no_stimulus")
        self.assertIsNone(report.signal_power)
        self.assertIsNone(report.profile)
        self.assertEqual((report.snr_db, report.sinad_db), (None, None))
        self.assertPower(report.noise_power, 0.0008062456564285143)
        self.assertPower(dc_enabled.noise_power, 0.0008130940426452365)
        self.assertEqual(report.band_power, report.noise_power)
        self.assertEqual(report.residual_power, report.noise_power)
        self.assertEqual(dc_enabled.noise_power - report.noise_power, report.bins[0].power)
        self.assertAlmostEqual(report.noise_level_db(F(1, 2)),
                               10 * math.log10(.0008062456564285143/.5), places=11)

    def test_quiet_silence_has_negative_infinite_noise_level_and_no_ratios(self):
        report = measure_quiet_noise(capture((0,) * FRAMES))
        self.assertEqual(report.noise_power, 0)
        self.assertEqual(report.noise_level_db(1), -math.inf)
        self.assertEqual((report.snr_db, report.sinad_db), (None, None))

    def test_constant_and_even_nyquist_are_unpaired(self):
        for samples, index, dc in (((.25,) * 64, 0, True), ((.25, -.25) * 32, 32, False)):
            with self.subTest(bin=index):
                report = measure_quiet_noise(capture(samples), include_dc=dc)
                self.assertPower(report.noise_power, .25**2)
                self.assertPower(report.bins[index].power, .25**2)

    def test_highest_odd_bin_is_paired(self):
        signal = rendered(((31, .25, F(1, 4)),), frames=63, dc=0)
        top = F(RATE * 31, 63)
        report = measure_quiet_noise(signal, band_hz=(top, top))
        self.assertEqual(report.bins[-1].frequency_hz, top)
        self.assertTrue(report.bins[-1].admitted)
        self.assertPower(report.noise_power, .25**2/2)

    def test_flat_density_doubles_power_when_the_band_doubles(self):
        # A one-sample impulse gives a flat density across the interior bins.
        peak = math.sqrt(1e-7 * FRAMES**2 / 2)
        data = capture((peak,) + (0,) * (FRAMES-1))
        narrow = measure_quiet_noise(data, band_hz=(50, 1050))
        wide = measure_quiet_noise(data, band_hz=(50, 2050))
        self.assertEqual(sum(bin.admitted for bin in narrow.bins), 10)
        self.assertEqual(sum(bin.admitted for bin in wide.bins), 20)
        self.assertPower(narrow.noise_power, 1e-6)
        self.assertPower(wide.noise_power, 2e-6)
        self.assertAlmostEqual(wide.noise_level_db(1) - narrow.noise_level_db(1), 3.01029995664, places=10)

    def test_normalized_welch_and_time_power_agree_at_two_dft_lengths(self):
        samples = seeded_noise()
        window = [.5-.5*math.cos(math.tau*j/128) for j in range(128)]
        window_energy = math.fsum(w*w for w in window)
        powers = [math.fsum((x*w)**2 for x, w in zip(samples[i:i+128], window))/window_energy
                  for i in (0, 64, 128)]
        expected = math.fsum(powers)/len(powers)
        self.assertAlmostEqual(expected, 0.000796486372634173, places=16)
        for nfft in (128, 256):
            with self.subTest(nfft=nfft):
                _, density, count = welch_mean(samples, window, RATE, 64, nfft=nfft)
                self.assertEqual(count, len(powers))
                self.assertAlmostEqual(math.fsum(density)*RATE/nfft, expected, places=15)

    def test_linear_power_pooling(self):
        measurements = [
            measure_quiet_noise(capture((amp,) * 16), include_dc=True)
            for amp in (.001, .01)
        ]
        mean_power = sum(report.noise_power for report in measurements)/2
        self.assertPower(mean_power, 5.05e-5)
        self.assertAlmostEqual(10*math.log10(mean_power), -42.96708621881338, places=10)
        self.assertAlmostEqual(sum(report.noise_level_db(1) for report in measurements)/2, -50, places=10)

    def test_extreme_pcm_and_exact_rates_are_supported(self):
        rate = F(2**2048, 1001)
        frequency = rate / 4
        epoch = replace(EPOCH, rate_hz=rate)
        for amplitude in (math.ulp(0.0), sys.float_info.max):
            with self.subTest(amplitude=amplitude):
                data = capture((amplitude, 0, -amplitude, 0), epoch)
                report = measure_quiet_noise(data, band_hz=(frequency, frequency))
                expected = F(amplitude)**2/2
                self.assertEqual(report.bin_width_hz, frequency)
                self.assertEqual(report.bins[1].frequency_hz, frequency)
                self.assertPower(report.noise_power/expected, 1)
                self.assertAlmostEqual(report.noise_level_db(expected), 0, places=12)

    def test_channel_selection_uses_the_capture_epoch(self):
        stereo = replace(EPOCH, channel_ids=("L", "R"))
        data = capture(seeded_noise())
        stereo_data = CaptureWindow(stereo, ORIGIN, (data.planes[0], (0,) * data.frame_count))
        self.assertEqual(measure_quiet_noise(stereo_data, channel_id="L").noise_power,
                         measure_quiet_noise(data).noise_power)
        self.assertEqual(measure_quiet_noise(stereo_data, channel_id="R").noise_power, 0)
        with self.assertRaisesRegex(ValueError, "channel"):
            measure_quiet_noise(stereo_data)

    def test_invalid_quiet_inputs_and_level_references(self):
        data = capture((0, 0))
        for band in ((0, 24001), (1, 0), (-1, 1), (0.0, 4), [0, 1], (1,)):
            with self.subTest(band=band), self.assertRaisesRegex(ValueError, "band"):
                measure_quiet_noise(data, band_hz=band)
        with self.assertRaisesRegex(ValueError, "include_dc"):
            measure_quiet_noise(data, include_dc=1)
        with self.assertRaisesRegex(ValueError, "capture length"):
            measure_quiet_noise(capture((0,)))
        report = measure_quiet_noise(data)
        for ref in (0, -1, True, math.inf, math.nan, "unit"):
            with self.subTest(reference=ref), self.assertRaisesRegex(ValueError, "reference power"):
                report.noise_level_db(ref)


if __name__ == "__main__":
    unittest.main()
