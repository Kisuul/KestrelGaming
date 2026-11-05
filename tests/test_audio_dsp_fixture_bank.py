"""Independent and metamorphic checks for the reusable audio fixture bank."""
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-dsp-test-fixtures/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-rms-crest-factor/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-fft-spectrum/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-power-spectral-density/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-spectrogram-waterfall/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-sample-peak/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-true-peak/scripts"))

from fixture_bank import make_fixture, partition_contiguous, KINDS, CHANNEL_MODES
from reference_dft import one_sided_amplitude, periodic_hann
from reference_psd import periodogram
from reference_levels import sample_levels
from reference_stft import stft_frames, stft_chunked
from reference_peak import RollingPeakMeter
from reference_true_peak import experimental_peak_estimate


class AudioFixtureBankTests(unittest.TestCase):
    def test_shapes_metadata_and_finite_planar_channels(self):
        for kind in KINDS:
            for mode in CHANNEL_MODES:
                with self.subTest(kind=kind, mode=mode):
                    f = make_fixture(kind, channel_mode=mode, sample_count=64,
                                     origin_sample=2**54)
                    self.assertEqual(f["schema_version"], 1)
                    self.assertEqual(f["sample_count"], 64)
                    self.assertEqual(f["origin_sample"], 2**54)
                    self.assertEqual(f["provenance"], "synthetic_deterministic_lcg_v1")
                    self.assertEqual(len(f["planar_samples"]), 1 if mode == "mono" else 2)
                    self.assertTrue(all(len(a) == 64 and all(math.isfinite(x) for x in a)
                                        for a in f["planar_samples"]))

    def test_uint32_noise_sequence_and_seed_reproducibility(self):
        f = make_fixture("seeded_noise", sample_count=8, amplitude=1., seed=0)
        first = (1013904223 / 2**32) * 2 - 1
        self.assertEqual(f["planar_samples"][0][0], first)
        self.assertEqual(f, make_fixture("seeded_noise", sample_count=8,
                                         amplitude=1., seed=0))
        self.assertNotEqual(f["planar_samples"], make_fixture(
            "seeded_noise", sample_count=8, amplitude=1., seed=1)["planar_samples"])

    def test_noise_scale_metamorphism(self):
        a = make_fixture("seeded_noise", amplitude=0.25, seed=1234)["planar_samples"][0]
        b = make_fixture("seeded_noise", amplitude=0.5, seed=1234)["planar_samples"][0]
        self.assertEqual([2*x for x in a], b)
        self.assertAlmostEqual(2*sample_levels(a)["rms"], sample_levels(b)["rms"])

    def test_dc_and_alternating_known_rms(self):
        for kind in ("dc", "alternating"):
            with self.subTest(kind=kind):
                signal = make_fixture(kind, amplitude=0.25)["planar_samples"][0]
                r = sample_levels(signal)
                self.assertEqual(r["sample_peak"], 0.25)
                self.assertEqual(r["rms"], 0.25)
                self.assertEqual(r["mean_square"], 0.0625)

    def test_impulse_rms_and_psd_integral(self):
        n, fs = 64, 8000
        signal = make_fixture("impulse", sample_count=n, amplitude=1.,
                              impulse_index=17)["planar_samples"][0]
        self.assertAlmostEqual(sample_levels(signal)["rms"], 1/math.sqrt(n))
        frequencies, power = periodogram(signal, [1.] * n, fs)
        self.assertEqual(frequencies[1] - frequencies[0], fs/n)
        self.assertAlmostEqual(math.fsum(power)*fs/n, 1/n, places=13)

    def test_coherent_tone_and_offbin_leakage(self):
        n, amp, k = 64, 0.7, 7
        window = periodic_hann(n)
        coherent = make_fixture("coherent_sine", sample_count=n,
                                bin_index=k, amplitude=amp)["planar_samples"][0]
        offbin = make_fixture("offbin_sine", sample_count=n,
                              bin_index=k, amplitude=amp)["planar_samples"][0]
        exact = one_sided_amplitude(coherent, window)
        spread = one_sided_amplitude(offbin, window)
        self.assertAlmostEqual(exact[k], amp, places=11)
        self.assertLess(spread[k], exact[k])
        self.assertTrue(any(v > 1e-4 for i, v in enumerate(spread)
                            if i not in (k, k-1, k+1)))

    def test_two_tap_analytical_intersample_overshoot(self):
        x = make_fixture("adjacent_pair", sample_count=128,
                         amplitude=1., impulse_index=63)["planar_samples"][0]
        r = experimental_peak_estimate(x, oversample_factor=8, radius=32)
        expected = (4/math.pi)*(math.sin(math.pi/(2*32))/(math.pi/(2*32)))
        self.assertEqual(r["sample_peak_amplitude"], 1.)
        self.assertAlmostEqual(r["estimated"]["peak_amplitude"], expected, places=11)
        self.assertFalse(r["peak_in_boundary_region"])
        self.assertEqual(r["maturity"], "experimental_not_bs1770_compliant")

    def test_antiphase_channels_must_not_cancel_energy(self):
        f = make_fixture("coherent_sine", channel_mode="stereo_antiphase",
                         sample_count=64, amplitude=0.75, bin_index=3)
        left, right = f["planar_samples"]
        self.assertEqual(right, [-v for v in left])
        self.assertAlmostEqual(sample_levels(left)["rms"], sample_levels(right)["rms"])
        self.assertTrue(any(abs(v) > 0.01 for v in left))
        self.assertTrue(all(math.isclose(a+b, 0, abs_tol=1e-15)
                            for a, b in zip(left, right)))

    def test_partition_preserves_exact_clock_and_data(self):
        origin = 2**54 + 19
        f = make_fixture("seeded_noise", channel_mode="stereo_antiphase",
                         sample_count=67, origin_sample=origin)
        for pattern in ([1], [2, 3, 9, 7], [128]):
            parts = partition_contiguous(f["planar_samples"], origin, pattern)
            positions = []
            reconstructed = [[], []]
            for chunk in parts:
                positions.extend(range(chunk["start_sample"],
                                       chunk["start_sample"]+len(chunk["planar_samples"][0])))
                for idx in (0, 1):
                    reconstructed[idx].extend(chunk["planar_samples"][idx])
            self.assertEqual(positions, list(range(origin, origin+67)))
            self.assertEqual(reconstructed, f["planar_samples"])

    def test_stft_values_and_time_are_chunk_invariant(self):
        f = make_fixture("seeded_noise", sample_count=73, seed=17,
                         origin_sample=2**54 + 17)
        samples = f["planar_samples"][0]
        window = periodic_hann(32)
        baseline = stft_frames(samples, window, 48000, hop=8, nfft=64,
                               origin_sample=f["origin_sample"])
        for pattern in ([1], [2, 5, 11, 3], [73]):
            chunks = partition_contiguous([samples], f["origin_sample"], pattern)
            actual = stft_chunked([c["planar_samples"][0] for c in chunks],
                                  window, 48000, hop=8, nfft=64,
                                  origin_sample=f["origin_sample"])
            self.assertEqual(baseline, actual)

    def test_sample_peak_program_and_roll_are_chunk_invariant(self):
        f = make_fixture("seeded_noise", sample_count=73,
                         channel_mode="stereo_antiphase", seed=23)
        base = RollingPeakMeter(2, 9).update(f["planar_samples"], 1234)
        for pattern in ([1], [5, 17, 2], [73]):
            meter = RollingPeakMeter(2, 9)
            for block in partition_contiguous(f["planar_samples"], 1234, pattern):
                state = meter.update(block["planar_samples"], block["start_sample"])
            for left, right in zip(base["channels"], state["channels"]):
                self.assertEqual(left["program_peak"], right["program_peak"])
                self.assertEqual(left["rolling_peak"], right["rolling_peak"])

    def test_invalid_fixtures_and_partitions_fail(self):
        cases = [
            dict(kind="not_a_signal"), dict(kind="impulse", sample_count=7),
            dict(kind="impulse", sample_count=257), dict(kind="impulse", amplitude=-1),
            dict(kind="impulse", amplitude=math.nan), dict(kind="impulse", seed=True),
            dict(kind="impulse", origin_sample=-1), dict(kind="impulse", sample_rate_hz=0),
            dict(kind="coherent_sine", bin_index=999),
            dict(kind="offbin_sine", phase_rad=math.inf),
            dict(kind="adjacent_pair", sample_count=8, impulse_index=7),
            dict(kind="silence", channel_mode="multichannel_unknown"),
        ]
        for args in cases:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    make_fixture(**args)
        for channels, sizes in [([[]], [1]), ([[1., 2.], [1.]], [1]),
                                ([[1., math.inf]], [1]), ([[1.]], []),
                                ([[1.]], [0]), ([[1.]], [True])]:
            with self.subTest(channels=channels, sizes=sizes):
                with self.assertRaises(ValueError):
                    partition_contiguous(channels, 0, sizes)


if __name__ == "__main__":
    unittest.main()
