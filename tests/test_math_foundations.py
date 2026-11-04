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
import unittest


class NumericalAnalysisFixtures(unittest.TestCase):
    def test_num01_cancellation_and_accurate_summation(self):
        # Independent reference: exact rational sum of the represented integers is 1.
        expected = sum((Fraction(10**16), Fraction(1), Fraction(-10**16)), Fraction(0))
        self.assertEqual(expected, Fraction(1))
        self.assertEqual((1e16 + 1.0) - 1e16, 0.0)
        self.assertEqual(math.fsum((1e16, 1.0, -1e16)), float(expected))

    def test_num02_scaled_norm_avoids_spurious_overflow(self):
        self.assertTrue(math.isfinite(math.hypot(1e308, 1e308)))
        self.assertTrue(math.isclose(math.hypot(1e308, 1e308),
                                     math.sqrt(2) * 1e308, rel_tol=2e-15))
        self.assertTrue(math.isinf(1e308 * 1e308))

    def test_absolute_floor_is_required_near_zero(self):
        self.assertFalse(math.isclose(1e-12, 0.0, rel_tol=1e-6))
        self.assertTrue(math.isclose(1e-12, 0.0, rel_tol=1e-6, abs_tol=1e-11))
        self.assertFalse(math.isclose(math.nan, math.nan))

    def test_decimal_reference_is_not_binary_float(self):
        with localcontext() as ctx:
            ctx.prec = 30
            self.assertEqual(Decimal('0.1') + Decimal('0.2'), Decimal('0.3'))
        self.assertNotEqual(0.1 + 0.2, 0.3)


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
        force = tuple(x + y for x, y in zip(acceleration, mass))
        self.assertEqual(force, (1, 1, -2, 0, 0, 0, 0))
        self.assertNotEqual(force, acceleration)

    def test_incompatible_dimensions_rejected_in_contract(self):
        length = (1, 0, 0, 0, 0, 0, 0)
        duration = (0, 0, 1, 0, 0, 0, 0)
        self.assertNotEqual(length, duration)  # Never add them as one quantity.


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
    def test_cmp01_magnitude_conjugate_product(self):
        z = complex(3, 4)
        self.assertEqual(abs(z), 5.0)
        self.assertEqual(z * z.conjugate(), complex(25, 0))
        rebuilt = cmath.rect(abs(z), cmath.phase(z))
        self.assertTrue(math.isclose(rebuilt.real, z.real, rel_tol=1e-14))
        self.assertTrue(math.isclose(rebuilt.imag, z.imag, rel_tol=1e-14))

    def test_cmp02_euler_identity_is_approximate_in_binary_float(self):
        computed = cmath.exp(1j * math.pi)
        self.assertTrue(math.isclose(computed.real, -1.0, abs_tol=1e-14))
        self.assertTrue(math.isclose(computed.imag, 0.0, abs_tol=2e-15))

    def test_phase_of_zero_not_used_as_measurement(self):
        self.assertEqual(abs(0j), 0.0)
        # Do not assert that the implementation's conventional phase(0) has meaning.


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
                                     rel_tol=2e-15))

    def test_near_singular_rounding_is_distinct_from_exact_math(self):
        delta = 2.0 ** -53  # Half a binary64 ULP at 1, rounds to 1 on a common runtime.
        self.assertEqual(1.0 + delta, 1.0)
        exact_determinant = Fraction(1) * (Fraction(1) + Fraction(1, 2**53)) - 1
        self.assertEqual(exact_determinant, Fraction(1, 2**53))


if __name__ == '__main__':
    unittest.main()
