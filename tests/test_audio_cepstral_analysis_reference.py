"""Analytical and upstream-transform checks for the real cepstrum."""
from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
import math
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-cepstral-analysis/scripts"))
sys.path.insert(0, str(ROOT / "skills/audio-fft-spectrum/scripts"))
import reference_cepstral_analysis as cep
from reference_dft import one_sided_amplitude, one_sided_dft, periodic_hann


def frame(magnitudes, nfft, **changes):
    fields = dict(clock_id="input-clock", epoch_id="a", source_tap="PCM",
                  channel="L", amplitude_unit="normalized PCM", window_id="rectangular",
                  sample_rate_hz=48000, window_samples=nfft, nfft=nfft,
                  hop_samples=nfft, start_sample=0, magnitudes=magnitudes)
    fields.update(changes)
    return cep.MagnitudeFrame(**fields)


def analyze(magnitudes, nfft, *, reference=1, floor=None, **changes):
    return cep.real_cepstrum(frame(magnitudes, nfft, **changes),
                             magnitude_reference=reference, relative_floor=floor)


def raw_magnitudes(samples, window=None):
    window = [1.0] * len(samples) if window is None else window
    return tuple(abs(value) for value in one_sided_dft(samples, window))


def echo_series(nfft, delay):
    """Periodize the signed Laurent-series coefficients using Decimal arithmetic."""
    with localcontext() as context:
        context.prec = 90
        a = Decimal("0.4")
        coefficients = [Decimal(0)] * nfft
        for order in range(1, 230):
            coefficient = (-1)**(order+1) * a**order / (2*order)
            for sign in (-1, 1):
                coefficients[sign * order * delay % nfft] += coefficient
    return tuple(float(value) for value in coefficients[:nfft//2+1])


class TransformTests(unittest.TestCase):
    def test_same_packed_values_have_different_parity(self):
        for nfft in (4, 5):
            with self.subTest(nfft=nfft):
                result = analyze((1, 1, 4), nfft)
                factor = math.log(4) / nfft
                if nfft == 4:
                    expected = [factor * (-1)**q for q in range(3)]
                else:
                    expected = [2 * factor * math.cos(4 * math.pi * q / nfft) for q in range(3)]
                self.assertEqual(result.frame.nfft, nfft)
                for actual, expected_value in zip(result.coefficients, expected):
                    self.assertAlmostEqual(actual, expected_value, delta=2e-15)

    def test_raw_impulse_and_false_component_from_folded_amplitude(self):
        for nfft in (16, 17):
            with self.subTest(nfft=nfft):
                signal = [1.0] + [0.0] * (nfft - 1)
                window = [1.0] * nfft
                raw = raw_magnitudes(signal, window)
                calibrated = one_sided_amplitude(signal, window)
                folded = tuple(value * sum(window) for value in calibrated)
                self.assertEqual(analyze(raw, nfft).coefficients, (0,) * (nfft//2+1))
                expected = -math.log(2) * (2 if nfft % 2 == 0 else 1) / nfft
                self.assertAlmostEqual(analyze(folded, nfft).coefficients[2], expected, delta=2e-15)

    def test_echo_sign_and_periodized_series_at_odd_and_even_lengths(self):
        for nfft in (255, 256):
            with self.subTest(nfft=nfft):
                samples = [0.0] * nfft
                samples[0], samples[7] = 1.0, 0.4
                result = analyze(raw_magnitudes(samples), nfft)
                for actual, expected in zip(result.coefficients, echo_series(nfft, 7)):
                    self.assertAlmostEqual(actual, expected, delta=2e-14)
                for q, expected in ((7, 0.2), (14, -0.04), (21, 0.4**3/6)):
                    self.assertAlmostEqual(result.coefficients[q], expected, delta=2e-14)

    def test_even_midpoint_echo_aliases_both_rahmonics(self):
        samples = [0.0] * 16
        samples[0], samples[8] = 1.0, 0.4
        result = analyze(raw_magnitudes(samples), 16)
        self.assertAlmostEqual(result.coefficients[8], math.atanh(0.4), delta=2e-15)
        self.assertAlmostEqual(result.coefficients[8], echo_series(16, 8)[8], delta=2e-15)

    def test_gain_and_circular_shift_of_the_prepared_frame(self):
        for nfft in (31, 32):
            samples = [0.0] * nfft
            samples[0], samples[7] = 1.0, 0.4
            base = analyze(raw_magnitudes(samples), nfft).coefficients
            gained = analyze(raw_magnitudes([3*x for x in samples]), nfft).coefficients
            rotated = analyze(raw_magnitudes(samples[-11:] + samples[:-11]), nfft).coefficients
            self.assertAlmostEqual(gained[0]-base[0], math.log(3), delta=2e-14)
            for index, value in enumerate(base):
                self.assertAlmostEqual(rotated[index], value, delta=2e-14)
                if index:
                    self.assertAlmostEqual(gained[index], value, delta=2e-14)

    def test_fft_padding_keeps_observed_support_and_exact_clock(self):
        samples = [1 / 4, -1 / 2, 1, 0.0, 1 / 4, -1 / 8, -0.05]
        window = periodic_hann(len(samples))
        nfft = 15
        padded = raw_magnitudes(samples + [0.0]*(nfft-len(samples)),
                                window + [0.0]*(nfft-len(samples)))
        start = 2**53 + 7
        result = analyze(padded, nfft, window_samples=len(samples), window_id="hann_periodic",
                         start_sample=start, hop_samples=3)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.frame.end_sample_exclusive, start + len(samples))
        self.assertEqual(result.frame.center_sample_twice, 2*start + len(samples)-1)
        self.assertEqual(len(result.coefficients), nfft//2+1)
        self.assertEqual(result.quefrency_seconds, tuple(q/48000 for q in range(nfft//2+1)))

    def test_wide_reference_ratio_stays_finite(self):
        for exponent in (-800, 800):
            magnitude, reference = 2.0**exponent, 2.0**(-exponent)
            with self.subTest(exponent=exponent):
                result = analyze((magnitude,)*3, 4, reference=reference)
                self.assertEqual(result.status, "ok")
                self.assertAlmostEqual(result.coefficients[0], 2*exponent*math.log(2), delta=3e-13)
                self.assertEqual(result.coefficients[1:], (0, 0))
                self.assertEqual(cep.spectral_envelope(result, cutoff=0).magnitudes, (magnitude,)*3)

    def test_common_large_log_offset_preserves_small_spectral_shape(self):
        top = 2.0**400
        next_smaller = math.nextafter(top, 0)
        values = (top, top, next_smaller)
        near = analyze(values, 4, reference=top)
        far = analyze(values, 4, reference=2.0**-300)
        expected = math.log1p((next_smaller-top)/top) / 4
        self.assertLess(expected, 0)
        self.assertEqual(far.coefficients[1:], near.coefficients[1:])
        self.assertEqual(far.coefficients[2], expected)
        self.assertEqual(far.coefficients[1], -expected)

    def test_seeded_direct_full_grid_oracle(self):
        rng = random.Random(2711)
        for nfft in range(2, 52):
            packed = tuple(math.exp(rng.uniform(-4, 4)) for _ in range(nfft//2+1))
            result = analyze(packed, nfft, reference=1.25)
            logs = tuple(math.log(packed[min(k,nfft-k)]/1.25) for k in range(nfft))
            for q, value in enumerate(result.coefficients):
                expected = math.fsum(ordinate * math.cos(2*math.pi*k*q/nfft)
                                     for k, ordinate in enumerate(logs)) / nfft
                self.assertAlmostEqual(value, expected, delta=2e-14)


class FloorTests(unittest.TestCase):
    def test_silence_has_own_status_under_both_policies(self):
        for floor in (None, 0.125):
            result = analyze((0, 0, 0), 4, floor=floor)
            self.assertEqual(result.status, "silent")
            self.assertIsNone(result.coefficients)
            self.assertIsNone(result.log_floor)
            self.assertEqual(result.floor_count, 0)
            envelope = cep.spectral_envelope(result, cutoff=1)
            self.assertEqual(envelope.status, "silent")
            self.assertIsNone(envelope.log_magnitudes)
            self.assertIsNone(envelope.magnitudes)

    def test_exact_spectral_nulls_and_numerical_fft_residuals(self):
        samples = [0.0] * 256
        samples[0] = samples[8] = 1.0
        raw = raw_magnitudes(samples)
        nulls = (16, 48, 80, 112)
        self.assertTrue(all(raw[k] < 2e-14 for k in nulls))
        exact = tuple(0 if k in nulls else value for k, value in enumerate(raw))
        strict = analyze(exact, 256)
        self.assertEqual(strict.status, "spectral_null")
        self.assertIsNone(strict.coefficients)
        self.assertEqual(cep.spectral_envelope(strict, cutoff=0).status, "spectral_null")
        for values in (exact, raw):
            regularized = analyze(values, 256, floor=2.0**-30)
            self.assertEqual(regularized.status, "ok")
            self.assertEqual(regularized.floored_bins, nulls)
            self.assertEqual(regularized.floor_count, len(nulls))

    def test_exact_floor_includes_only_values_below_equal_edge(self):
        border = 2.0**-10
        values = (1, math.nextafter(border, 0), border, math.nextafter(border, math.inf))
        result = analyze(values, 6, floor=border)
        self.assertEqual(result.floored_bins, (1,))
        self.assertEqual(result.floor_count, 1)
        self.assertAlmostEqual(result.log_floor, math.log(border), delta=2e-15)
        envelope = cep.spectral_envelope(result, cutoff=3)
        self.assertEqual(envelope.magnitudes, (1.0, border, border, values[3]))

    def test_rounded_linear_floor_can_hide_a_replacement(self):
        peak, ratio = 1.3, 0.1
        rounded_floor = peak * ratio
        self.assertLess(Fraction(rounded_floor), Fraction(peak)*Fraction(ratio))
        result = analyze((peak, rounded_floor, 1.0), 4, floor=ratio)
        self.assertEqual(result.floored_bins, (1,))
        self.assertEqual(cep.spectral_envelope(result, cutoff=2).magnitudes[1], rounded_floor)

    def test_underflowed_linear_floor_keeps_finite_log(self):
        peak, ratio, smallest = 2.0**-900, 2.0**-300, math.ulp(0.0)
        self.assertEqual(peak*ratio, 0)
        result = analyze((peak, smallest, 0), 4, floor=ratio)
        self.assertEqual(result.floored_bins, (2,))
        self.assertEqual(result.floor_count, 1)
        self.assertAlmostEqual(result.log_floor, -1200*math.log(2), delta=2e-13)
        self.assertTrue(all(math.isfinite(value) for value in result.coefficients))
        envelope = cep.spectral_envelope(result, cutoff=2)
        self.assertEqual(envelope.status, "partial")
        self.assertEqual(envelope.underflow_bins, (2,))
        self.assertEqual(envelope.overflow_bins, ())
        self.assertEqual(envelope.magnitudes, (peak, smallest, None))
        self.assertEqual(envelope.log_magnitudes[2], result.log_floor)

    def test_relative_floor_and_common_gain_keep_shape(self):
        shape = (0, 2.0**-8, 0.5, 1)
        base = analyze(shape, 7, floor=2.0**-5)
        gained = analyze(tuple(8 * value for value in shape), 7, floor=2.0**-5)
        self.assertEqual(base.floored_bins, gained.floored_bins)
        self.assertEqual(base.coefficients[1:], gained.coefficients[1:])
        self.assertAlmostEqual(gained.coefficients[0]-base.coefficients[0], math.log(8), delta=2e-15)


class EnvelopeTests(unittest.TestCase):
    def test_symmetric_low_lifter_selects_both_sides_of_q_one(self):
        for nfft in (32, 33):
            with self.subTest(nfft=nfft):
                expected = tuple(math.log(2) + 0.6 * math.cos(2*math.pi*k/nfft)
                                 for k in range(nfft//2+1))
                log_magnitudes = tuple(value + 0.4 * math.cos(14*math.pi*k/nfft)
                                       for k, value in enumerate(expected))
                result = analyze(tuple(math.exp(value) for value in log_magnitudes), nfft)
                envelope = cep.spectral_envelope(result, cutoff=1)
                self.assertEqual(envelope.status, "ok")
                for actual, truth in zip(envelope.log_magnitudes, expected):
                    self.assertAlmostEqual(actual, truth, delta=2e-15)
                for actual, truth in zip(envelope.magnitudes, expected):
                    self.assertAlmostEqual(actual, math.exp(truth), delta=5e-15)
                dc_envelope = cep.spectral_envelope(result, cutoff=0)
                self.assertTrue(all(abs(value-2) < 2e-15 for value in dc_envelope.magnitudes))

    def test_even_midpoint_is_discarded_by_the_preceding_cutoff(self):
        values = tuple(math.exp(0.3*(-1)**k) for k in range(9))
        result = analyze(values, 16)
        self.assertAlmostEqual(result.coefficients[8], 0.3, delta=2e-15)
        truncated = cep.spectral_envelope(result, cutoff=7)
        self.assertTrue(all(abs(value) < 2e-15 for value in truncated.log_magnitudes))
        self.assertEqual(cep.spectral_envelope(result, cutoff=8).magnitudes, values)

    def test_full_lifter_preserves_positive_binary64_endpoints(self):
        for nfft in (4, 5):
            values = (math.ulp(0.0), 1.25, sys.float_info.max)
            result = analyze(values, nfft, reference=2.0**800)
            envelope = cep.spectral_envelope(result, cutoff=2)
            self.assertEqual(envelope.status, "ok")
            self.assertEqual(envelope.magnitudes, values)
            self.assertTrue(all(math.isfinite(value) for value in envelope.log_magnitudes))

    def test_linear_envelope_can_exceed_numeric_range_after_lifter(self):
        for sign in (-1, 1):
            with self.subTest(sign=sign):
                high_log = sign*700
                values = tuple(math.exp(value) for value in (high_log, high_log, -high_log))
                result = analyze(values, 4, reference=3)
                envelope = cep.spectral_envelope(result, cutoff=1)
                self.assertEqual(envelope.status, "partial")
                self.assertIsNone(envelope.magnitudes[0])
                self.assertIsNotNone(envelope.magnitudes[1])
                self.assertIsNotNone(envelope.magnitudes[2])
                self.assertEqual(envelope.underflow_bins, (0,) if sign < 0 else ())
                self.assertEqual(envelope.overflow_bins, (0,) if sign > 0 else ())
                self.assertAlmostEqual(envelope.log_magnitudes[0], sign*1050-math.log(3), delta=2e-13)

    def test_linear_envelope_is_independent_of_magnitude_reference(self):
        values = (4.0, 0.5, 0.2, 1.0)
        a = cep.spectral_envelope(analyze(values, 7, reference=2.0**-800), cutoff=1)
        b = cep.spectral_envelope(analyze(values, 7, reference=2.0**800), cutoff=1)
        self.assertEqual(a.magnitudes, b.magnitudes)
        for left, right in zip(a.log_magnitudes, b.log_magnitudes):
            self.assertAlmostEqual(left-right, 1600*math.log(2), delta=3e-13)

    def test_long_lifter_limits_roundoff_on_a_wide_range_spectrum(self):
        nfft, cutoff, peak_bin = 1024, 417, 123
        packed = [2.0**-900] * (nfft//2+1)
        packed[peak_bin] = 2.0**900
        measured = cep.spectral_envelope(analyze(tuple(packed), nfft), cutoff=cutoff)

        def kernel(index):
            phase = index % nfft
            phase = min(phase, nfft-phase)
            if phase == 0:
                return 2*cutoff+1
            angle = math.pi*phase/nfft
            return math.sin((2*cutoff+1)*angle)/math.sin(angle)

        base = -900*math.log(2)
        step = 1800*math.log(2)/nfft
        for k, value in enumerate(measured.log_magnitudes):
            expected = base + step*(kernel(k-peak_bin)+kernel(k+peak_bin))
            self.assertAlmostEqual(value, expected, delta=3e-12)


class ValidationTests(unittest.TestCase):
    def test_reject_malformed_or_invalid_magnitudes(self):
        for value in (True, "1", -1, math.nan, math.inf, -math.inf, 2**1100):
            with self.subTest(value=value), self.assertRaises(ValueError):
                frame((1, 1, value), 4)
        with self.assertRaises(ValueError):
            frame((1, 2), 4)
        with self.assertRaises(ValueError):
            frame([1, 2, 3], 4)

    def test_validate_declared_frame_support_and_clock(self):
        original = frame((1, 2, 3), 4)
        for updates in (dict(nfft=True), dict(nfft=1), dict(nfft=cep.MAX_NFFT+1),
                        dict(window_samples=5), dict(sample_rate_hz=1),
                        dict(hop_samples=0), dict(start_sample=-1), dict(start_sample=2**256-2),
                        dict(clock_id=" "), dict(epoch_id=1), dict(window_id="")):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                replace(original, **updates)

    def test_invalid_reference_and_floor_reject_even_with_silence(self):
        for reference in (0, True, -1, math.nan, math.inf, "amplitude"):
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                analyze((0, 0, 0), 4, reference=reference)
        for floor in (0, True, 1, -0.5, math.nan, math.inf):
            with self.subTest(floor=floor), self.assertRaises(ValueError):
                analyze((0, 0, 0), 4, floor=floor)

    def test_lifter_requires_integer_supported_cutoff(self):
        result = analyze((1, 2, 3), 5)
        for cutoff in (-1, 3, True, 1.0):
            with self.subTest(cutoff=cutoff), self.assertRaises(ValueError):
                cep.spectral_envelope(result, cutoff=cutoff)
        with self.assertRaises(ValueError):
            cep.spectral_envelope(result.frame, cutoff=0)

    def test_bound_accepts_maximum_transform_size(self):
        nfft = cep.MAX_NFFT
        result = analyze((1,)*(nfft//2+1), nfft, window_samples=512, hop_samples=128)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.coefficients, (0,)*(nfft//2+1))
        self.assertEqual(cep.spectral_envelope(result, cutoff=0).magnitudes, (1,)*(nfft//2+1))


if __name__ == "__main__":
    unittest.main()
