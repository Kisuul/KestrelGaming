"""Sample-indexed STFT fixture tests with independent analytic expectations."""
import math
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/audio-spectrogram-waterfall/scripts"))
from reference_stft import stft_frames, stft_chunked

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/audio-fft-spectrum/scripts"))
from reference_dft import periodic_hann


class STFTReferenceTests(unittest.TestCase):
    def test_frame_timestamps_are_sample_accurate(self):
        frames = stft_frames([0.] * 100, [1.] * 32, 8000, 8, origin_sample=1000)
        self.assertEqual([f["start_sample"] for f in frames["frames"]],
                         [1000 + 8*i for i in range(9)])
        self.assertEqual(frames["frames"][0]["end_sample_exclusive"], 1032)
        self.assertEqual(frames["frames"][0]["center_sample"], 1015.5)
        self.assertAlmostEqual(frames["frames"][1]["center_seconds"], 1023.5/8000)
        self.assertEqual(frames["frequencies_hz"][7], 7*8000/32)

    def test_coherent_sine_ridge_amplitude(self):
        n, hop, k, amplitude, fs = 64, 16, 7, 0.6, 48000
        signal = [amplitude * math.sin(2*math.pi*k*j/n) for j in range(160)]
        data = stft_frames(signal, periodic_hann(n), fs, hop, scaling="amplitude")
        self.assertEqual(len(data["frames"]), 7)
        self.assertEqual(data["frequencies_hz"][k], k*fs/n)
        for frame in data["frames"]:
            self.assertAlmostEqual(frame["values"][k], amplitude, places=11)
            self.assertEqual(max(range(len(frame["values"])), key=lambda i: frame["values"][i]), k)

    def test_frequency_step_at_disjoint_frame_boundary(self):
        n, fs = 32, 32000
        early = [math.sin(2*math.pi*3*i/n) for i in range(n)]
        late = [math.sin(2*math.pi*8*i/n) for i in range(n)]
        data = stft_frames(early+late, [1.] * n, fs, n, scaling="amplitude")
        self.assertEqual([max(range(len(f["values"])), key=lambda k: f["values"][k])
                          for f in data["frames"]], [3, 8])
        self.assertEqual([f["start_sample"] for f in data["frames"]], [0, 32])

    def test_impulse_only_in_frames_covering_its_sample(self):
        samples = [0.] * 96
        samples[40] = 1
        data = stft_frames(samples, [1.] * 32, 8000, 16)
        actual = [f["start_sample"] for f in data["frames"]
                  if any(v > 1e-20 for v in f["values"])]
        expected = [start for start in range(0, 96-32+1, 16) if start <= 40 < start+32]
        self.assertEqual(actual, expected)

    def test_silence_is_zero_with_valid_timestamps(self):
        data = stft_frames([0.] * 64, periodic_hann(32), 16000, 16)
        self.assertEqual(len(data["frames"]), 3)
        self.assertTrue(all(all(v == 0 for v in frame["values"])
                            for frame in data["frames"]))

    def test_psd_parseval_by_independent_windowed_energy(self):
        samples = [0.5*math.cos(2*math.pi*3*i/64) + (0.25 if i == 35 else 0)
                   for i in range(128)]
        fs, m, hop = 16000, 64, 16
        for window in ([1.] * m, periodic_hann(m)):
            data = stft_frames(samples, window, fs, hop, nfft=256)
            win_energy = math.fsum(v*v for v in window)
            for frame in data["frames"]:
                start = frame["start_sample"]
                expected = math.fsum((samples[start+j]*window[j])**2
                                     for j in range(m)) / win_energy
                integrated = math.fsum(frame["values"])*fs/256
                self.assertAlmostEqual(integrated, expected, places=11)

    def test_odd_fft_last_bin_is_paired(self):
        n, fs = 63, 18900
        signal = [math.cos(2*math.pi*31*j/n) for j in range(n)]
        data = stft_frames(signal, [1.] * n, fs, n)
        f = data["frames"][0]
        self.assertEqual(len(f["values"]), 32)
        self.assertAlmostEqual(f["values"][31], (0.5)/(fs/n), places=11)
        self.assertAlmostEqual(math.fsum(f["values"])*fs/n, 0.5, places=11)

    def test_even_nyquist_not_doubled(self):
        n, fs = 64, 16000
        signal = [0.25*(-1)**j for j in range(n)]
        data = stft_frames(signal, [1.] * n, fs, n)
        self.assertAlmostEqual(data["frames"][0]["values"][32], 0.0625*n/fs, places=11)

    def test_chunk_partitions_preserve_frames_and_times(self):
        rng = random.Random(1003)
        signal = [rng.uniform(-1, 1) for _ in range(127)]
        window = periodic_hann(32)
        baseline = stft_frames(signal, window, 44100, 9, 64, origin_sample=9876)
        chunks = [signal[:1], signal[1:4], [], signal[4:31], signal[31:32],
                  signal[32:55], signal[55:79], signal[79:112], signal[112:]]
        streaming = stft_chunked(chunks, window, 44100, 9, 64, origin_sample=9876)
        self.assertEqual(baseline, streaming)

    def test_tail_not_silently_zero_padded(self):
        short = stft_frames([1.] * 31, [1.] * 32, 48000, 8)
        self.assertEqual(short["frames"], [])
        data = stft_frames([1.] * 33, [1.] * 32, 48000, 8)
        self.assertEqual(len(data["frames"]), 1)
        self.assertEqual(data["frames"][0]["end_sample_exclusive"], 32)

    def test_zero_sum_window_valid_for_psd_not_amplitude(self):
        w = [1., -1., 1., -1.]
        data = stft_frames([1.] * 4, w, 8000, 4, scaling="psd")
        self.assertAlmostEqual(math.fsum(data["frames"][0]["values"])*8000/4, 1)
        with self.assertRaises(ValueError):
            stft_frames([1.] * 4, w, 8000, 4, scaling="amplitude")

    def test_input_validation_and_oracle_limits(self):
        for signal, window, fs, hop, nfft, mode in [
            ([1.]*4, [1.]*4, 0, 2, 4, "psd"),
            ([1.]*4, [0.]*4, 8000, 2, 4, "psd"),
            ([1.]*4, [1.]*4, 8000, 0, 4, "psd"),
            ([1.]*4, [1.]*4, 8000, 5, 4, "psd"),
            ([1.]*4, [1.]*4, 8000, 2, 3, "psd"),
            ([1.]*4, [1.]*4, 8000, 2, 513, "psd"),
            ([1.]*4, [1.]*4, 8000, 2, 4, "power"),
            ([math.nan]*4, [1.]*4, 8000, 2, 4, "psd"),
            ([1.]*4, [math.inf]*4, 8000, 2, 4, "psd"),
        ]:
            with self.subTest(fs=fs,hop=hop,nfft=nfft,mode=mode,window=window[:2]):
                with self.assertRaises(ValueError):
                    stft_frames(signal, window, fs, hop, nfft, mode)
        with self.assertRaises(ValueError):
            stft_frames([0.]*132, [1.]*4, 8000, 1, 4, origin_sample=-1)
        with self.assertRaises(ValueError):
            stft_frames([0.]*132, [1.]*4, 8000, 1, 4)
        with self.assertRaises(ValueError):
            stft_chunked([[1., math.inf]], [1., 1.], 8000, 1)


if __name__ == "__main__":
    unittest.main()
