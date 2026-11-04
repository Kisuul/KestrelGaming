"""Small independent mathematical fixtures for Kestrel's math curriculum.

These tests exercise published arithmetic claims, not agent skill activation,
production solvers, external library APIs or standards conformance.
Python 3.9+ standard library only.
"""

import cmath
from decimal import Decimal, localcontext
from fractions import Fraction
import itertools
import math
import statistics
import sys
import unittest


def dimension_vector(value):
    """Test-local SI representation guard, not an exported units API."""
    if len(value) != 7:
        raise ValueError("dimension vector must have seven components")
    return tuple(value)


def multiply_dimensions(left, right):
    left, right = dimension_vector(left), dimension_vector(right)
    return tuple(x + y for x, y in zip(left, right))


class NumericalAnalysisFixtures(unittest.TestCase):
    def test_binary64_prerequisites(self):
        # These floating examples target binary64 with round-to-nearest.
        self.assertEqual((sys.float_info.radix, sys.float_info.mant_dig,
                          sys.float_info.max_exp, sys.float_info.rounds),
                         (2, 53, 1024, 1))

    def test_num01_cancellation_and_accurate_summation(self):
        # Independent reference: exact rational sum of the represented integers is 1.
        expected = sum((Fraction(10**16), Fraction(1), Fraction(-10**16)), Fraction(0))
        self.assertEqual(expected, Fraction(1))
        self.assertEqual((1e16 + 1.0) - 1e16, 0.0)
        self.assertEqual(math.fsum((1e16, 1.0, -1e16)), float(expected))

    def test_num02_scaled_norm_avoids_spurious_overflow(self):
        self.assertTrue(math.isfinite(math.hypot(1e308, 1e308)))
        self.assertTrue(math.isclose(math.hypot(1e308, 1e308),
                                     math.sqrt(2) * 1e308, rel_tol=2e-15, abs_tol=0))
        self.assertTrue(math.isinf(1e308 * 1e308))

    def test_absolute_floor_is_required_near_zero(self):
        self.assertFalse(math.isclose(1e-12, 0.0, rel_tol=1e-6, abs_tol=0))
        self.assertTrue(math.isclose(1e-12, 0.0, rel_tol=1e-6, abs_tol=1e-11))
        self.assertFalse(math.isclose(math.nan, math.nan, rel_tol=1e-9, abs_tol=0))

    def test_num03_log1p_expm1_preserve_tiny_increments(self):
        # Both naive expressions round to zero for this binary64 input.
        x = 1e-16
        self.assertEqual(math.log(1.0 + x), 0.0)
        self.assertEqual(math.exp(x) - 1.0, 0.0)
        # Taylor expansion: true results are x + O(x*x).
        self.assertTrue(math.isclose(math.log1p(x), x, rel_tol=1e-15, abs_tol=0))
        self.assertTrue(math.isclose(math.expm1(x), x, rel_tol=1e-15, abs_tol=0))

    def test_decimal_reference_is_not_binary_float(self):
        with localcontext() as ctx:
            ctx.prec = 30
            self.assertEqual(Decimal('0.1') + Decimal('0.2'), Decimal('0.3'))
        self.assertNotEqual(0.1 + 0.2, 0.3)

    def test_num04_rationalization_avoids_small_difference_cancellation(self):
        x = 1e-16
        with localcontext() as ctx:
            ctx.prec = 80
            represented_x = Decimal.from_float(x)
            reference = (1 + represented_x).sqrt() - 1
        naive = math.sqrt(1 + x) - 1
        stable = x / (math.sqrt(1 + x) + 1)
        self.assertEqual(naive, 0.0)
        self.assertGreater(reference, 0)
        self.assertTrue(math.isclose(stable, float(reference),
                                     rel_tol=1e-15, abs_tol=0))

    def test_num05_underflow_and_subnormal_rounding(self):
        self.assertEqual((1e-200 * 1e-200) * 1e200, 0.0)
        regrouped = 1e-200 * (1e-200 * 1e200)
        self.assertTrue(math.isclose(regrouped, 1e-200,
                                     rel_tol=1e-15, abs_tol=0))
        smallest = math.ulp(0.0)
        self.assertEqual(Fraction(smallest), Fraction(1, 2**1074))
        self.assertEqual(smallest / 2, 0.0)
        self.assertEqual(smallest + smallest, 2 * smallest)


class DimensionalAnalysisFixtures(unittest.TestCase):
    # Dimension order: L, M, T, I, temperature, amount, luminous intensity.
    def test_dim01_sample_rate_conversion_is_rational(self):
        samples = Fraction(1000)
        rate = Fraction(48000)  # samples / second
        self.assertEqual(samples / rate, Fraction(1, 48))
        self.assertTrue(math.isclose(float(samples / rate), 0.0208333333333333,
                                     rel_tol=0, abs_tol=4e-17))

    def test_dim02_acceleration_times_mass_is_force(self):
        acceleration = (1, 0, -2, 0, 0, 0, 0)
        mass = (0, 1, 0, 0, 0, 0, 0)
        force = multiply_dimensions(acceleration, mass)
        self.assertEqual(force, (1, 1, -2, 0, 0, 0, 0))
        self.assertNotEqual(force, acceleration)

    def test_incompatible_dimensions_rejected_in_reference_gate(self):
        length = (1, 0, 0, 0, 0, 0, 0)
        duration = (0, 0, 1, 0, 0, 0, 0)

        def add_canonical_quantities(left, right):
            # Test-local contract example, not a production units API.
            # The two values must already use the same canonical unit scale.
            left_dimension = dimension_vector(left[1])
            right_dimension = dimension_vector(right[1])
            if left_dimension != right_dimension:
                raise ValueError("incompatible dimensions")
            return (left[0] + right[0], left[1])

        self.assertEqual(add_canonical_quantities((Fraction(2), length),
                                                  (Fraction(3), length)),
                         (Fraction(5), length))
        with self.assertRaisesRegex(ValueError, "incompatible dimensions"):
            add_canonical_quantities((Fraction(2), length),
                                     (Fraction(3), duration))
        with self.assertRaisesRegex(ValueError, "seven components"):
            add_canonical_quantities((Fraction(2), (1, 0)),
                                     (Fraction(3), (1, 0)))

    def test_malformed_dimension_vectors_rejected_before_zip(self):
        valid = (1, 0, 0, 0, 0, 0, 0)
        for malformed in ((), valid[:-1], valid + (0,)):
            for left, right in ((valid, malformed), (malformed, valid),
                                (malformed, malformed)):
                with self.subTest(left=left, right=right):
                    with self.assertRaisesRegex(ValueError, "seven components"):
                        multiply_dimensions(left, right)

    def test_dim03_affine_temperature_conversion(self):
        offset = Decimal('273.15')
        self.assertEqual(Decimal('0') + offset, Decimal('273.15'))
        self.assertEqual(Decimal('100') + offset, Decimal('373.15'))
        self.assertEqual(Decimal('373.15') - Decimal('273.15'),
                         Decimal('100'))

    def test_dim04_consistent_logarithmic_ratios(self):
        # Referenced amplitude ratio 2, associated power ratio 4.
        amplitude_db = 20 * math.log10(2.0)
        power_db = 10 * math.log10(4.0)
        self.assertTrue(math.isclose(amplitude_db, power_db, rel_tol=1e-15, abs_tol=0))
        self.assertTrue(math.isclose(amplitude_db, 6.020599913279624,
                                     rel_tol=0, abs_tol=2e-15))


class LinearAlgebraFixtures(unittest.TestCase):
    def test_lin01_cramers_exact_solution_and_independent_residual(self):
        a, b, c, d = map(Fraction, (3, 1, 1, 2))
        rhs0, rhs1 = Fraction(9), Fraction(8)
        determinant = a * d - b * c
        x = (rhs0 * d - b * rhs1) / determinant
        y = (a * rhs1 - rhs0 * c) / determinant
        self.assertEqual(determinant, Fraction(5))
        self.assertEqual((x, y), (Fraction(2), Fraction(3)))
        self.assertEqual((a * x + b * y, c * x + d * y), (rhs0, rhs1))

    def test_lin02_singular_matrix(self):
        self.assertEqual(Fraction(1) * 4 - Fraction(2) * 2, 0)

    def test_lin03_small_residual_can_hide_large_forward_error(self):
        # A=diag(1,eps), b=(1,eps); all norms here are infinity norms.
        eps = Fraction(1, 10**12)
        exact = (Fraction(1), Fraction(1))
        candidate = (Fraction(1), Fraction(0))
        rhs = (Fraction(1), eps)
        residual = (rhs[0] - candidate[0], rhs[1] - eps * candidate[1])
        residual_norm = max(map(abs, residual))
        forward_error = max(abs(x - y) for x, y in zip(exact, candidate))
        condition = 1 / eps  # ||A||=1, ||A^-1||=1/eps.
        self.assertEqual(residual_norm, eps)
        self.assertEqual(forward_error, 1)
        self.assertEqual(condition * residual_norm, forward_error)
        backward_residual = residual_norm / (1 * max(map(abs, candidate)) + 1)
        self.assertEqual(backward_residual, Fraction(1, 2 * 10**12))

    def test_transform_order_is_not_interchangeable(self):
        # A scales x by 2; B turns vectors anticlockwise 90 degrees.
        vector = (1, 0)
        def a(p):
            return (2 * p[0], p[1])
        def b(p):
            return (-p[1], p[0])
        self.assertEqual(a(b(vector)), (0, 1))
        self.assertEqual(b(a(vector)), (0, 2))
        self.assertNotEqual(a(b(vector)), b(a(vector)))


class ComplexNumbersFixtures(unittest.TestCase):
    def assert_euler_components(self, computed):
        # Shared by the real example and deliberately wrong candidates below.
        for actual, expected, absolute in ((computed.real, -1.0, 1e-14),
                                            (computed.imag, 0.0, 2e-15)):
            self.assertTrue(math.isfinite(actual))
            self.assertTrue(math.isclose(actual, expected,
                                         rel_tol=0, abs_tol=absolute))

    def test_cmp01_magnitude_conjugate_product(self):
        z = complex(3, 4)
        self.assertEqual(abs(z), 5.0)
        self.assertEqual(z * z.conjugate(), complex(25, 0))
        rebuilt = cmath.rect(abs(z), cmath.phase(z))
        self.assertTrue(math.isclose(rebuilt.real, z.real, rel_tol=1e-14, abs_tol=0))
        self.assertTrue(math.isclose(rebuilt.imag, z.imag, rel_tol=1e-14, abs_tol=0))

    def test_cmp02_euler_identity_is_approximate_in_binary_float(self):
        computed = cmath.exp(1j * math.pi)
        self.assert_euler_components(computed)

    def test_euler_absolute_budget_rejects_default_relative_tolerance_trap(self):
        wrong_real = complex(-1 + 5e-10, 0)
        # The old omitted rel_tol silently admitted this real-component error.
        self.assertTrue(math.isclose(wrong_real.real, -1.0, abs_tol=1e-14))
        for wrong in (wrong_real, complex(-1, 3e-15),
                      complex(math.nan, 0), complex(-1, math.inf)):
            with self.subTest(wrong=wrong):
                with self.assertRaises(AssertionError):
                    self.assert_euler_components(wrong)

    def test_phase_of_zero_not_used_as_measurement(self):
        # Python cmath.phase(0) returns a convention, not a defined physical phase.
        def phase_or_none(z):
            return None if abs(z) == 0 else cmath.phase(z)

        self.assertIsNone(phase_or_none(0j))
        self.assertTrue(math.isclose(phase_or_none(3 + 4j),
                                     math.atan2(4, 3), rel_tol=1e-15, abs_tol=0))

    def test_cmp03_branch_cut_signed_zero(self):
        self.assertEqual(cmath.phase(complex(-1.0, 0.0)), math.pi)
        self.assertEqual(cmath.phase(complex(-1.0, -0.0)), -math.pi)


class ProbabilityStatisticsFixtures(unittest.TestCase):
    def test_sta01_sample_variance_and_assumption_labeled_sem(self):
        sample = [1, 2, 3, 4, 5]
        self.assertEqual(statistics.mean(sample), 3)
        self.assertEqual(sum((value - 3)**2 for value in sample), 10)
        self.assertEqual(statistics.variance(sample), 2.5)
        self.assertEqual(statistics.pvariance(sample), 2)
        assumed_iid_sem = math.sqrt(statistics.variance(sample) / len(sample))
        self.assertTrue(math.isclose(assumed_iid_sem, math.sqrt(0.5), rel_tol=0, abs_tol=1e-15))

    def test_sta02_complete_enumeration_unbiased_sample_variance(self):
        universe = list(itertools.product((Fraction(0), Fraction(1)), repeat=2))
        self.assertEqual(len(universe), 4)
        enumerated_variances = [statistics.variance(pair) for pair in universe]
        self.assertEqual(enumerated_variances,
                         [Fraction(0), Fraction(1, 2), Fraction(1, 2), Fraction(0)])
        expectation = sum(enumerated_variances, Fraction(0)) / len(universe)
        self.assertEqual(expectation, Fraction(1, 4))

    def test_sta03_identical_dependent_samples_do_not_establish_zero_uncertainty(self):
        # X1=X2=Y, with equiprobable Y=-1 or +1. No random trials required.
        samples = [(Fraction(-1),) * 2, (Fraction(1),) * 2]
        self.assertEqual([statistics.variance(sample) for sample in samples], [0, 0])
        means = [statistics.mean(sample) for sample in samples]
        self.assertEqual(statistics.pvariance(means), Fraction(1))
        assumed_iid_variance_of_mean = Fraction(1, 2)
        self.assertNotEqual(statistics.pvariance(means), assumed_iid_variance_of_mean)

    def test_sample_variance_requires_two_observations(self):
        with self.assertRaises(statistics.StatisticsError):
            statistics.variance([7])


class VerificationFixtures(unittest.TestCase):
    def test_ver01_exact_rational_oracle(self):
        self.assertEqual(Fraction(1, 3) + Fraction(1, 6), Fraction(1, 2))

    def test_ver02_rotation_preserves_norm_metamorphically(self):
        original = (3.0, 4.0)
        angle = math.pi / 2
        rotated = (original[0] * math.cos(angle) - original[1] * math.sin(angle),
                   original[0] * math.sin(angle) + original[1] * math.cos(angle))
        for actual, expected in zip(rotated, (-4.0, 3.0)):
            self.assertTrue(math.isfinite(actual))
            self.assertTrue(math.isclose(actual, expected, rel_tol=0, abs_tol=2e-15))
        self.assertTrue(math.isclose(math.hypot(*rotated), math.hypot(*original),
                                     rel_tol=2e-15, abs_tol=0))

    def test_near_singular_rounding_is_distinct_from_exact_math(self):
        delta = 2.0 ** -53  # Half a binary64 ULP at 1, rounds to 1 on a common runtime.
        self.assertEqual(1.0 + delta, 1.0)
        floating_determinant = 1.0 * (1.0 + delta) - 1.0 * 1.0
        self.assertEqual(floating_determinant, 0.0)
        exact_determinant = Fraction(1) * (Fraction(1) + Fraction(1, 2**53)) - 1
        self.assertEqual(exact_determinant, Fraction(1, 2**53))

    def test_explicit_nonfinite_comparison_gate(self):
        def checked_close(actual, expected, *, relative, absolute):
            # Test-local policy example, not a production verifier.
            if not (math.isfinite(actual) and math.isfinite(expected)):
                raise ValueError("nonfinite comparison")
            return math.isclose(actual, expected,
                                rel_tol=relative, abs_tol=absolute)

        self.assertTrue(checked_close(1.0, 1.0, relative=1e-12, absolute=0))
        for bad in (math.nan, math.inf, -math.inf):
            with self.subTest(value=bad):
                with self.assertRaisesRegex(ValueError, "nonfinite"):
                    checked_close(bad, 0.0, relative=1e-12, absolute=1e-12)


if __name__ == '__main__':
    unittest.main()
