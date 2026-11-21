"""Analytical, direct-DFT, and decision tests for harmonic analysis."""
from cmath import exp
from dataclasses import replace
from fractions import Fraction
import math
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-harmonic-analysis/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-fft-spectrum/scripts"))
import reference_harmonic_analysis as harmonic
from reference_dft import one_sided_amplitude, one_sided_dft, periodic_hann


def frame(values, **changes):
    nfft = changes.get("nfft", 2 * (len(values) - 1))
    fields = dict(
        clock_id="input", epoch_id="a", source_tap="PCM", channel="L",
        amplitude_unit="V", amplitude_reference="calibrated peak",
        window_id="rectangular", sample_rate_hz=nfft, window_samples=nfft,
        nfft=nfft, hop_samples=2, start_sample=0, amplitudes=values,
    )
    fields.update(changes)
    return harmonic.AmplitudeFrame(**fields)


def detect(values, *, min_amplitude=0, **changes):
    measured = frame(values, **changes)
    return harmonic.find_peaks(measured, harmonic.SearchBand(0, measured.sample_rate_hz / 2),
                               min_amplitude=min_amplitude)


def known_peak(index, frequency, amplitude=1):
    return harmonic.Peak(index, frequency, amplitude)


def assign(peaks, *, fundamental=100, orders=(1,), tolerance=Fraction(1, 10), band=(50, 505)):
    return harmonic.assign_harmonics(tuple(peaks), harmonic.SearchBand(*band),
                                     fundamental_hz=fundamental, orders=orders, tolerance=tolerance)


def dirichlet(length, cycles):
    """Closed-form sum of length unit complex exponentials."""
    cycles = math.remainder(cycles, length)
    if cycles == 0:
        return complex(length)
    if cycles.is_integer():
        return 0j
    angle = math.pi * cycles / length
    return exp(1j * angle * (length - 1)) * math.sin(math.pi * cycles) / math.sin(angle)


def hann_transform(length, cycles):
    return (dirichlet(length, cycles) / 2
            - (dirichlet(length, cycles - 1) + dirichlet(length, cycles + 1)) / 4)


def analytical_hann_amplitudes(length, nfft, fs, tones):
    """Evaluate the windowed DTFT directly from frequency, phase, and amplitude."""
    components = tuple((hz * length / fs, amp * exp(1j * phase) / 2)
                       for hz, amp, phase in tones)
    values = []
    for k in range(nfft // 2 + 1):
        coordinate = k * length / nfft
        transform = sum(phasor * hann_transform(length, cycles - coordinate)
                        + phasor.conjugate() * hann_transform(length, -cycles - coordinate)
                        for cycles, phasor in components)
        fold = 1 if k == 0 or 2 * k == nfft else 2
        values.append(fold * abs(transform) / (length / 2))
    return tuple(values)


class PeakTests(unittest.TestCase):
    def test_analytic_log_parabola_both_offset_directions(self):
        for offset in (-0.37, 0, 0.37):
            with self.subTest(offset=offset):
                flank = tuple(math.exp(-1.75 * (k - offset)**2) for k in (-1, 0, 1))
                peak, = detect((0, 0, 0, *flank, 0)).peaks
                self.assertEqual(peak.bin_index, 4)
                self.assertEqual(peak.bin_frequency_hz, 4)
                self.assertEqual(peak.bin_amplitude, flank[1])
                self.assertEqual(peak.refinement, "refined")
                self.assertAlmostEqual(peak.interpolated_hz, 4 + offset, delta=2e-15)

    def test_equal_height_peak_stays_unresolved(self):
        max_value = math.exp(-1.75 / 4)
        values = (0, 0.01, max_value, max_value, 0.01, 0)
        result = detect(values)
        self.assertEqual(result.peaks, ())
        self.assertEqual(result.plateaus, (harmonic.Plateau(2, 3, max_value),))

    def test_plateau_preserves_extent_when_band_cuts_it(self):
        result = harmonic.find_peaks(frame((0, 1, 1, 1, 0.4, 0)),
                                     harmonic.SearchBand(2.25, 3.75), min_amplitude=0)
        self.assertEqual(result.peaks, ())
        self.assertEqual(result.plateaus, (harmonic.Plateau(1, 3, 1),))

    def test_endpoint_scale_shift_with_actual_kestrel_fft(self):
        window = [1.0] * 8
        signal = [(0.5 + 2 * math.cos(2 * math.pi * i / 8) + math.cos(4 * math.pi * i / 8)) / 8
                  for i in range(8)]
        sets = ((signal, 1, 1/6), ([x * (-1)**i for i, x in enumerate(signal)], 3, -1/6))
        for samples, bin_index, wrong_offset in sets:
            with self.subTest(bin_index=bin_index):
                amplitude = one_sided_amplitude(samples, window)
                raw = one_sided_dft(samples, window)
                self.assertAlmostEqual(abs(raw[bin_index - 1]), abs(raw[bin_index + 1]), delta=2e-15)
                left, center, right = map(math.log, amplitude[bin_index - 1:bin_index + 2])
                naive = (left - right) / (2 * (left - 2 * center + right))
                self.assertAlmostEqual(naive, wrong_offset, delta=2e-15)
                peak, = detect(tuple(amplitude), min_amplitude=0.01).peaks
                self.assertEqual((peak.bin_index, peak.frequency_hz), (bin_index, bin_index))
                self.assertEqual(peak.refinement, "unpaired_flank")
                self.assertIsNone(peak.interpolated_hz)

    def test_last_odd_bin_is_paired_for_its_neighbor(self):
        values = (0, 0, 0.8, 1, 0.6)
        even, = detect(values, nfft=8).peaks
        odd, = detect(values, nfft=9).peaks
        self.assertEqual(even.refinement, "unpaired_flank")
        self.assertEqual(odd.refinement, "refined")
        self.assertLess(odd.frequency_hz, 3)

    def test_terminal_bin_has_no_right_neighbor(self):
        values = (0, 0, 0.5, 0.6, 1)
        self.assertEqual(detect(values, nfft=8).peaks, ())
        peak, = detect(values, nfft=9).peaks
        self.assertEqual((peak.bin_index, peak.frequency_hz), (4, 4))
        self.assertEqual(peak.refinement, "missing_flank")
        self.assertIsNone(peak.interpolated_hz)

    def test_near_equal_magnitudes_keep_log_curvature(self):
        for center in (2.0**-40, 2.0**40):
            with self.subTest(center=center):
                left = math.nextafter(center, 0)
                right = math.nextafter(left, 0)
                peak, = detect((0, 0, left, center, right, 0)).peaks
                self.assertEqual(peak.refinement, "refined")
                self.assertAlmostEqual(peak.frequency_hz, 3 - 1/6, delta=2e-15)

    def test_wide_log_ratio_without_forming_underflowed_quotient(self):
        low, high = 2.0**-800, 2.0**800
        self.assertEqual(low / high, 0)
        peak, = detect((0, 0, low, high, low, 0)).peaks
        self.assertEqual(peak.interpolated_hz, 3)
        self.assertEqual(peak.bin_amplitude, high)

    def test_zero_flank_and_closed_amplitude_floor(self):
        values = (0, 0, 0, 0.5, 0.2, 0)
        peak, = detect(values, min_amplitude=0.5).peaks
        self.assertEqual(peak.refinement, "zero_flank")
        self.assertEqual(peak.frequency_hz, 3)
        self.assertEqual(detect(values, min_amplitude=math.nextafter(0.5, math.inf)).peaks, ())

    def test_silence_and_dc_have_no_positive_peaks(self):
        for values in ((0, 0, 0, 0, 0), (2, 0, 0, 0, 0)):
            with self.subTest(values=values):
                observation = detect(values)
                self.assertEqual((observation.peaks, observation.plateaus), ((), ()))

    def test_band_uses_the_selected_frequency(self):
        values = (0, 0, 0, *[math.exp(-(k - 0.3)**2) for k in (-1, 0, 1)], 0)
        observation = frame(values)
        peak, = harmonic.find_peaks(observation, harmonic.SearchBand(4.1, 4.5),
                                    min_amplitude=0).peaks
        self.assertEqual(peak.bin_frequency_hz, 4)
        self.assertAlmostEqual(peak.frequency_hz, 4.3)
        excluded = harmonic.find_peaks(observation, harmonic.SearchBand(3, peak.frequency_hz),
                                       min_amplitude=0)
        self.assertEqual(excluded.peaks, ())

    def test_frame_keeps_large_sample_coordinates(self):
        index = 2**53 + 7
        measured = frame((0, 1, 2, 1, 0), start_sample=index, window_samples=5)
        observation = harmonic.find_peaks(measured, harmonic.SearchBand(0, 4), min_amplitude=0)
        self.assertIs(observation.frame, measured)
        self.assertEqual(observation.frame.end_sample_exclusive, index + 5)
        self.assertEqual(observation.frame.center_sample_twice, 2 * index + 4)


class ResolutionTests(unittest.TestCase):
    def test_isolated_hann_frequency_with_fourfold_padding(self):
        fs, length, nfft = 48000, 2048, 8192
        for offset, phase in ((0, 0), (0.37, 0.7), (-0.49, 1.9)):
            with self.subTest(offset=offset, phase=phase):
                frequency = (173 + offset) * fs / length
                values = analytical_hann_amplitudes(length, nfft, fs, ((frequency, 1, phase),))
                peak, = detect(values, nfft=nfft, window_samples=length, sample_rate_hz=fs,
                               min_amplitude=0.5).peaks
                self.assertAlmostEqual(peak.frequency_hz, frequency, delta=0.005)
                if offset == 0:
                    self.assertAlmostEqual(peak.bin_amplitude, 1, delta=2e-14)

    def test_equal_peak_counts_do_not_establish_two_tone_resolution(self):
        fs, nfft = 48000, 16384
        tones = ((4054.6875, 1, 0), (4062.890625, 1, 0.65 * math.pi))
        true_hz = [tone[0] for tone in tones]
        for length, expected_errors in (
            (2048, (18.096646, 18.097616)),
            (16384, (0.009617, 0.040635)),
        ):
            with self.subTest(length=length):
                values = analytical_hann_amplitudes(length, nfft, fs, tones)
                measured = detect(values, nfft=nfft, window_samples=length, sample_rate_hz=fs,
                                  min_amplitude=max(values) / 2)
                self.assertEqual(len(measured.peaks), 2)
                for peak, truth, error in zip(measured.peaks, true_hz, expected_errors):
                    self.assertAlmostEqual(abs(peak.frequency_hz - truth), error, delta=1e-6)

    def test_padding_preserves_the_zero_phase_merge(self):
        fs, length = 48000, 2048
        for nfft in (2048, 16384):
            tones = ((4054.6875, 1, 0), (4062.890625, 1, 0))
            values = analytical_hann_amplitudes(length, nfft, fs, tones)
            result = detect(values, nfft=nfft, window_samples=length, sample_rate_hz=fs,
                            min_amplitude=max(values) / 2)
            self.assertEqual(len(result.peaks), 1)

    def test_declared_floor_preserves_the_weak_tone(self):
        fs, length, nfft = 48000, 2048, 8192
        tones = ((4054.6875, 1, 0), (4195.3125, 0.1, 0.7))
        values = analytical_hann_amplitudes(length, nfft, fs, tones)
        options = dict(nfft=nfft, window_samples=length, sample_rate_hz=fs)
        both = detect(values, min_amplitude=0.05, **options)
        loud_only = detect(values, min_amplitude=max(values) / 2, **options)
        self.assertEqual(len(both.peaks), 2)
        self.assertEqual(len(loud_only.peaks), 1)
        self.assertAlmostEqual(both.peaks[1].bin_amplitude, 0.1, delta=2e-14)
        self.assertAlmostEqual(abs(both.peaks[1].frequency_hz - tones[1][0]), 0.641642, delta=1e-6)


class AssignmentTests(unittest.TestCase):
    def test_rank_and_coverage_work_order(self):
        peaks = [known_peak(index, hz, amp) for index, (hz, amp) in enumerate(
            ((90, .4), (110, .7), (198, .9), (201, .2), (299, .6), (301, .6), (411, 1)), 1)]
        result = assign(peaks, orders=(1, 2, 3, 4, 5, 6))
        signature = [(x.status, x.peak.frequency_hz if x.peak else None) for x in result.harmonics]
        self.assertEqual(signature, [("matched", 110), ("matched", 201), ("matched", 299),
                                     ("missing", None), ("partial_band", None), ("out_of_band", None)])
        self.assertEqual([x.residual_hz for x in result.harmonics], [10, 1, -1, None, None, None])
        self.assertEqual((result.matched_count, result.eligible_count, result.full_gate_count), (3, 5, 4))
        self.assertEqual([p.frequency_hz for p in result.unassigned_peaks], [90, 198, 301, 411])
        self.assertEqual(result, assign(reversed(peaks), orders=(6, 5, 4, 3, 2, 1)))

    def test_lower_bin_index_breaks_an_exact_frequency_and_amplitude_tie(self):
        a, b = known_peak(8, 101), known_peak(9, 101)
        result = assign((b, a))
        self.assertEqual(result.harmonics[0].peak, a)
        self.assertEqual(result.unassigned_peaks, (b,))

    def test_gate_includes_both_edges_and_excludes_the_outer_adjacent_floats(self):
        for edge, direction in ((90, -math.inf), (110, math.inf)):
            for point, status in ((edge, "matched"),
                                  (math.nextafter(edge, -direction), "matched"),
                                  (math.nextafter(edge, direction), "missing")):
                with self.subTest(point=point):
                    result = assign((known_peak(1, point),))
                    self.assertEqual(result.harmonics[0].status, status)

    def test_rounded_binary64_residual_can_reverse_gate_membership(self):
        for f0, hz, inside in ((442.1, 1304.1950000000002, True),
                               (110.1, 324.79499999999996, False)):
            with self.subTest(f0=f0, hz=hz):
                self.assertNotEqual(abs(hz - 3 * f0) <= 0.05 * f0, inside)
                result = assign((known_peak(1, hz),), fundamental=f0, orders=(3,),
                                tolerance=Fraction(1, 20), band=(50, 2000))
                self.assertEqual(result.harmonics[0].status, "matched" if inside else "missing")

    def test_exact_halfway_peak_cannot_fill_two_disjoint_gates(self):
        peak = known_peak(1, 150)
        result = assign((peak,), orders=(1, 2), tolerance=Fraction(499, 1000))
        self.assertEqual(result.matched_count, 0)
        self.assertEqual(result.unassigned_peaks, (peak,))

    def test_partially_observed_gate_can_match(self):
        result = assign((known_peak(1, 495),), orders=(5,))
        match, = result.harmonics
        self.assertEqual(match.status, "matched")
        self.assertFalse(match.full_gate)
        self.assertEqual(match.target_hz, 500)
        self.assertEqual(match.residual_hz, -5)

    def test_closed_gate_at_exclusive_band_end_is_partial(self):
        peak = known_peak(1, 110)
        result = assign((peak,), band=(90, 110))
        self.assertEqual(result.harmonics[0].status, "partial_band")
        self.assertEqual(result.unassigned_peaks, (peak,))
        self.assertEqual(assign((), band=(50, 100)).harmonics[0].status, "out_of_band")

    def test_fitted_frequency_supersedes_coarse_bin_position(self):
        refined = harmonic.Peak(1, 90, 0.2, "refined", 99)
        coarse = harmonic.Peak(2, 98, 0.9, "zero_flank")
        match, = assign((coarse, refined)).harmonics
        self.assertEqual(match.peak, refined)
        self.assertEqual(match.residual_hz, -1)
        self.assertEqual(assign((coarse,)).harmonics[0].peak.refinement, "zero_flank")

    def test_missing_fundamental_supports_multiple_series(self):
        peaks = tuple(known_peak(index, hz) for index, hz in enumerate((440, 660, 880), 1))
        for f0, wanted in ((220, (2, 3, 4)), (110, (4, 6, 8))):
            report = assign(peaks, fundamental=f0, orders=tuple(range(1, 10)), band=(50, 1000),
                            tolerance=Fraction(1, 20))
            matches = [x for x in report.harmonics if x.status == "matched"]
            self.assertEqual(tuple(x.order for x in matches), wanted)
            self.assertEqual([x.residual_hz for x in matches], [0, 0, 0])
            self.assertEqual(report.fundamental_hz, f0)
            self.assertEqual(report.harmonics[0].status, "missing")

    def test_seeded_exact_gate_oracle(self):
        rng = random.Random(2601)
        band = (50, 1650)
        orders = (1, 2, 3, 4, 5, 6, 7, 8)
        fraction = Fraction(7, 40)
        for _ in range(30):
            f0 = rng.uniform(90, 250)
            peaks = tuple(known_peak(i, rng.uniform(40, 1750), rng.uniform(0.001, 2))
                          for i in range(1, 45))
            result = assign(peaks, fundamental=f0, tolerance=fraction, orders=orders, band=band)
            f0_exact = Fraction(f0)
            for match in result.harmonics:
                target = match.order * f0_exact
                candidates = [peak for peak in peaks if band[0] <= peak.frequency_hz < band[1]
                              and abs(Fraction(peak.frequency_hz) - target) <= f0_exact * fraction]
                if not band[0] <= target < band[1] or not candidates:
                    self.assertIsNone(match.peak)
                    continue
                oracle = min(candidates, key=lambda peak: (abs(Fraction(peak.frequency_hz) - target),
                                                           -peak.bin_amplitude, peak.frequency_hz,
                                                           peak.bin_index))
                self.assertEqual(match.peak, oracle)
                self.assertEqual(match.residual_hz, float(Fraction(oracle.frequency_hz) - target))


class IntegrationTests(unittest.TestCase):
    def test_calibrated_fft_frame_through_assignment(self):
        length, fs = 96, 960
        samples = [sum(amplitude * math.cos(2 * math.pi * hz * n / fs)
                       for hz, amplitude in ((200, 1), (300, 0.5), (400, 0.25)))
                   for n in range(length)]
        amplitudes = one_sided_amplitude(samples, periodic_hann(length))
        measured = frame(tuple(amplitudes), nfft=length, sample_rate_hz=fs, window_id="hann_periodic")
        found = harmonic.find_peaks(measured, harmonic.SearchBand(50, 470), min_amplitude=0.1)
        result = harmonic.assign_harmonics(found.peaks, found.band, fundamental_hz=100,
                                           orders=(1, 2, 3, 4, 5), tolerance=Fraction(1, 20))
        self.assertEqual(tuple(item.status for item in result.harmonics),
                         ("missing", "matched", "matched", "matched", "out_of_band"))
        self.assertEqual(found.frame.amplitude_unit, "V")
        for match, expected in zip(result.harmonics[1:4], (1, 0.5, 0.25)):
            self.assertAlmostEqual(match.residual_hz, 0, delta=2e-12)
            self.assertAlmostEqual(match.peak.bin_amplitude, expected, delta=2e-12)


class ValidationTests(unittest.TestCase):
    def test_entire_frame_is_validated_before_search(self):
        for value in (math.inf, -math.inf, math.nan, -0.5, True, "1", 2**1100):
            with self.subTest(value=value), self.assertRaises(ValueError):
                frame((0, 1, 2, 1, value), nfft=8)
        for changes in (dict(nfft=5), dict(sample_rate_hz=0), dict(window_samples=9),
                        dict(hop_samples=0), dict(start_sample=2**256), dict(clock_id=" ")):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                frame((0, 1, 2, 1, 0), **changes)
        with self.assertRaises(ValueError):
            frame([0, 1, 2, 1, 0])

    def test_search_band_and_amplitude_floor_validation(self):
        for low, high in ((0, 0), (3, 2), (-1, 4), (0, math.inf)):
            with self.subTest(low=low, high=high), self.assertRaises(ValueError):
                harmonic.SearchBand(low, high)
        for floor in (-1, math.nan, True, math.inf):
            with self.subTest(floor=floor), self.assertRaises(ValueError):
                detect((0, 1, 2, 1, 0), min_amplitude=floor)
        with self.assertRaises(ValueError):
            harmonic.find_peaks(frame((0, 1, 2, 1, 0)), harmonic.SearchBand(0, 4.1), min_amplitude=0)

    def test_assignment_rejects_invalid_inputs_and_duplicate_bin_identity(self):
        peak = known_peak(1, 100)
        cases = (dict(fundamental=0), dict(fundamental=math.inf), dict(tolerance=0.1),
                 dict(tolerance=Fraction(1, 2)), dict(orders=(0,)),
                 dict(orders=(1, 1)), dict(orders=()))
        for options in cases:
            with self.subTest(options=options), self.assertRaises(ValueError):
                assign((peak,), **options)
        with self.assertRaises(ValueError):
            assign((peak, replace(peak, bin_frequency_hz=101)))
        with self.assertRaises(ValueError):
            harmonic.Peak(1, 100, 1, "refined")
        with self.assertRaises(ValueError):
            harmonic.Peak(1, 100, 0)


if __name__ == "__main__":
    unittest.main()
