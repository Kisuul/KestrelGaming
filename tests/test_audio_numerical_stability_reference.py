"""Independent analytical and metamorphic tests for the bounded audio oracle.

Expected values derive from exact rational arithmetic, signal definitions,
IEEE binary encodings, and mathematical identities—not from the oracle code.
"""
from fractions import Fraction
from pathlib import Path
import math
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                        'skills/audio-numerical-stability/scripts'))
from reference_numerical_stability import (
    RmsAccumulator, stable_rms, stable_enbw_bins, exact_psd_bin,
    exact_amplitude_bin, stable_welch_mean, stable_signed_sum,
    fixed_quantize_counts, inspect_float32, biquad_pole_radius
)


class AudioNumericalStabilityTests(unittest.TestCase):
    def test_rms_exact_silence(self):
        self.assertEqual(stable_rms([0.0, -0.0, 0, 0]), 0.0)

    def test_rms_constant_dc(self):
        self.assertEqual(stable_rms([0.25]*16), 0.25)

    def test_rms_impulse(self):
        self.assertEqual(stable_rms([1,0,0,0]), 0.5)

    def test_rms_analytic_sine_quadrature(self):
        self.assertAlmostEqual(stable_rms([0,1,0,-1]*8), math.sqrt(0.5), places=15)

    def test_rms_peak_near_float_limit(self):
        v=float(2**1023)
        self.assertEqual(stable_rms([v,v,v,v]),v)
        self.assertEqual(stable_rms([v,0,0,0]),float(2**1022))

    def test_rms_tiny_nonzero_not_silence(self):
        v=1e-200
        self.assertEqual(stable_rms([v]*4),v)
        self.assertEqual(stable_rms([5e-324]*4),5e-324)

    def test_rms_underflowing_intermediate_but_valid_result(self):
        self.assertEqual(stable_rms([1e-200, 0.0, 0.0, 0.0]),5e-201)

    def test_enbw_tiny_uniform_window(self):
        self.assertEqual(stable_enbw_bins([1e-200]*4),1.0)
        self.assertEqual(stable_enbw_bins([1e200]*4),1.0)

    def test_enbw_rectangular_and_hann(self):
        self.assertEqual(stable_enbw_bins([1.0]*8),1.0)
        self.assertAlmostEqual(stable_enbw_bins([0.5,1.0,0.5,0.0]),1.5,places=15)

    def test_enbw_zero_coherent_gain_is_not_silence(self):
        with self.assertRaisesRegex(ValueError,'coherent'):
            stable_enbw_bins([1,-1,1,-1])
        with self.assertRaises(ValueError):
            stable_enbw_bins([0,0,0])

    def test_enbw_tiny_nonzero_coherent_gain_fails_as_final_overflow(self):
        # Not a zero gain: +1 and -1 cancel, but tiny residual remains.
        # Squaring the residual in binary64 would divide by zero.
        with self.assertRaisesRegex(ValueError, 'not representable'):
            stable_enbw_bins([1.0, -1.0, 5e-324])

    def test_large_psd_bin_exact_analytic(self):
        # Rectangular x=[2^512,2^512] => X[0]=2^513.
        # Density = |X0|^2/(48000*2) = 2^1026/96000.
        expected=float(Fraction(2**1026, 96000))
        self.assertTrue(math.isfinite(expected))
        self.assertAlmostEqual(exact_psd_bin(float(2**513),0,[1,1],
                                            Fraction(48000),2,0)/expected,1.0,places=15)

    def test_psd_one_sided_interior_vs_even_nyquist(self):
        # For 4-point rectangular, sum w²=4, fs=4 Hz.
        self.assertEqual(exact_psd_bin(4,0,[1]*4,Fraction(4),4,0),1)
        self.assertEqual(exact_psd_bin(4,0,[1]*4,Fraction(4),4,1),2)
        self.assertEqual(exact_psd_bin(4,0,[1]*4,Fraction(4),4,2),1)

    def test_psd_odd_nfft_has_no_nyquist(self):
        self.assertEqual(exact_psd_bin(3,0,[1]*3,Fraction(3),3,1),2)

    def test_psd_fractional_hz_and_tiny_window(self):
        # X=2*1e-200 is a rounded binary64; expected uses its exact float bits.
        x=2e-200
        fs=Fraction(48000*1000,1001)
        expected=float(Fraction.from_float(x)**2 /
                       (fs*(Fraction.from_float(1e-200)**2)*2))
        got=exact_psd_bin(x,0,[1e-200,1e-200],fs,2,0)
        self.assertAlmostEqual(got/expected,1.0,places=15)

    def test_psd_infinite_final_result_rejected(self):
        with self.assertRaisesRegex(ValueError,'not representable'):
            exact_psd_bin(1e308,0,[1e-200,1e-200],Fraction(48000),2,0)

    def test_psd_underflow_final_nonzero_rejected(self):
        with self.assertRaisesRegex(ValueError,'underflows'):
            exact_psd_bin(5e-324,0,[1,1],Fraction(48000),2,0)

    def test_psd_zero_exact(self):
        self.assertEqual(exact_psd_bin(0,0,[1,1],Fraction(48000),2,0),0)

    def test_amplitude_overflowing_intermediate_but_finite_result(self):
        # 4-pt impulse 2^1023 -> interior factor 2 / coherent sum 4.
        self.assertEqual(exact_amplitude_bin(float(2**1023),4.0,4,1),float(2**1022))

    def test_amplitude_dc_nyquist_and_interior(self):
        self.assertEqual(exact_amplitude_bin(4,4,4,0),1)
        self.assertEqual(exact_amplitude_bin(4,4,4,1),2)
        self.assertEqual(exact_amplitude_bin(4,4,4,2),1)
        with self.assertRaisesRegex(ValueError,'coherent'):
            exact_amplitude_bin(2,0,4,1)

    def test_welch_average_does_not_sum_to_inf(self):
        self.assertEqual(stable_welch_mean([1e308,1e308]),1e308)
        self.assertEqual(stable_welch_mean([1e308,0,1e308,0]),5e307)

    def test_welch_mean_nonnegative_and_silence(self):
        self.assertEqual(stable_welch_mean([0,0,0]),0)
        self.assertEqual(stable_welch_mean([0.25]*8),0.25)
        with self.assertRaisesRegex(ValueError,'nonnegative'):
            stable_welch_mean([0.5,-0.01])

    def test_cancellation_exact_binary_input_sum(self):
        v=float(2**54)
        self.assertEqual(stable_signed_sum([v,1,-v]),1)
        self.assertEqual(stable_signed_sum([v,-v]),0)

    def test_signed_sum_random_exact_oracle(self):
        rng=random.Random(20261104)
        for _ in range(80):
            values=[float(rng.randint(-2**22,2**22)) for j in range(64)]
            self.assertEqual(stable_signed_sum(values),float(sum(int(x) for x in values)))

    def test_signed_sum_true_overflow_rejected(self):
        with self.assertRaisesRegex(ValueError,'not representable'):
            stable_signed_sum([1e308,1e308])

    def test_fixed_signed_round_ties_even(self):
        args={'bits':8,'signed':True,'policy':'error'}
        self.assertEqual(fixed_quantize_counts(Fraction(1,2),**args)['counts'],0)
        self.assertEqual(fixed_quantize_counts(Fraction(3,2),**args)['counts'],2)
        self.assertEqual(fixed_quantize_counts(Fraction(-3,2),**args)['counts'],-2)
        self.assertEqual(fixed_quantize_counts(Fraction(-5,2),**args)['counts'],-2)

    def test_fixed_signed_saturation_and_limits(self):
        v=fixed_quantize_counts(Fraction(200),8,signed=True,policy='saturate')
        self.assertEqual((v['counts'],v['saturated'],v['low'],v['high']),
                         (127,True,-128,127))
        self.assertEqual(fixed_quantize_counts(Fraction(-999),8,signed=True,policy='saturate')['counts'],-128)
        self.assertEqual(fixed_quantize_counts(Fraction(-128),8,signed=True,policy='error')['counts'],-128)
        with self.assertRaises(ValueError):
            fixed_quantize_counts(Fraction(-129),8,signed=True,policy='error')

    def test_fixed_unsigned_rejects_negative_and_clamps_explicitly(self):
        with self.assertRaises(ValueError):
            fixed_quantize_counts(Fraction(-1),8,signed=False,policy='error')
        result=fixed_quantize_counts(Fraction(-1),8,signed=False,policy='saturate')
        self.assertEqual((result['counts'],result['saturated']),(0,True))

    def test_fixed_policy_type_must_be_explicit(self):
        for kwargs in [dict(bits=8,signed=1,policy='error'),
                       dict(bits=True,signed=True,policy='error'),
                       dict(bits=8,signed=True,policy='wrap')]:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    fixed_quantize_counts(Fraction(1),**kwargs)
        with self.assertRaises(ValueError):
            fixed_quantize_counts(0.5,8,signed=True,policy='error')

    def test_f32_loses_unit_after_2to24(self):
        v=float(2**24+1)
        x=inspect_float32(v)
        self.assertEqual(x['input_binary64'],v)
        self.assertEqual(x['output_binary32'],float(2**24))
        self.assertTrue(x['changed'])

    def test_f32_exact_subnormal_and_underflow(self):
        tiny=2.0**-149
        self.assertEqual(inspect_float32(tiny)['output_binary32'],tiny)
        lost=inspect_float32(2.0**-150)
        self.assertEqual(lost['output_binary32'],0)
        self.assertTrue(lost['loss_of_nonzero'])

    def test_f32_overflow_is_not_silent_inf(self):
        with self.assertRaisesRegex(ValueError,'overflow'):
            inspect_float32(1e100)

    def test_pole_stability_change_from_quantization(self):
        # Complex poles |z| = sqrt(a2) when discr < 0.
        x=biquad_pole_radius(-1.8,0.9998)
        self.assertTrue(x['stable_strict'])
        self.assertAlmostEqual(x['radius'],math.sqrt(0.9998),places=14)
        q=biquad_pole_radius(-1.8,0.9998,quant_step=Fraction(1,1024))
        self.assertFalse(q['stable_strict'])
        self.assertEqual(q['a2'],1.0)
        self.assertEqual(q['radius'],1.0)

    def test_strict_stability_near_unit_circle(self):
        self.assertTrue(biquad_pole_radius(-1,0.25)['stable_strict'])
        self.assertFalse(biquad_pole_radius(-2,1)['stable_strict'])
        self.assertFalse(biquad_pole_radius(0,-2)['stable_strict'])

    def test_accumulator_partition_invariance_large_origin(self):
        rng=random.Random(20261104)
        data=[rng.choice((-1,1))*rng.random()*1e280 for _ in range(187)]
        expected=stable_rms(data)
        origin=2**54+7
        for schedule in [(187,), (1,), (3,11,5), (64,7,2)]:
            with self.subTest(schedule=schedule):
                acc=RmsAccumulator('record',origin)
                n=i=0
                while i<len(data):
                    size=min(schedule[n%len(schedule)],len(data)-i)
                    r=acc.push(origin+i,data[i:i+size])
                    self.assertEqual(r['end_sample_exclusive'],origin+i+size)
                    i+=size; n+=1
                self.assertEqual(acc.count,len(data))
                self.assertAlmostEqual(acc.rms()/expected,1.0,delta=2e-14)

    def test_accumulator_exact_zero_and_epoch_reset(self):
        acc=RmsAccumulator('old',100)
        self.assertEqual(acc.rms(),0.0)
        acc.push(100,[0.0,0.0])
        self.assertEqual(acc.rms(),0.0)
        acc.reset_epoch('new',0)
        self.assertEqual((acc.count,acc.next_sample),(0,0))
        acc.push(0,[3.0,4.0])
        self.assertAlmostEqual(acc.rms(),math.sqrt(12.5),places=15)
        with self.assertRaisesRegex(ValueError,'reused'):
            acc.reset_epoch('old',0)

    def test_accumulator_invalid_block_is_atomic(self):
        acc=RmsAccumulator('e',0)
        acc.push(0,[1.0,2.0])
        before=(acc.next_sample,acc.count,acc.scale,acc.sumsq)
        for index,values in [(1,[1]),(2,[math.nan]),(2,[math.inf]),
                             (2,[]),(2,[True]),(2,['1'])]:
            with self.subTest(index=index,values=str(values)):
                with self.assertRaises(ValueError):acc.push(index,values)
                self.assertEqual((acc.next_sample,acc.count,acc.scale,acc.sumsq),before)

    def test_accumulator_underflow_is_atomic(self):
        # Exact RMS = 2^-1074/sqrt(256) -> nonzero but below binary64 output range.
        # A rejected block must not consume samples or poison a running stream.
        acc = RmsAccumulator('subnormal', 70)
        before = (acc.next_sample, acc.count, acc.scale, acc.sumsq)
        with self.assertRaisesRegex(ValueError, 'accumulated RMS'):
            acc.push(70, [5e-324] + [0.0] * 255)
        self.assertEqual((acc.next_sample, acc.count, acc.scale, acc.sumsq), before)

    def test_invalid_reference_inputs(self):
        for fn,args in [(stable_rms,([True],)),(stable_rms,([math.nan],)),
                        (stable_enbw_bins,([math.inf],)),
                        (exact_psd_bin,(1,0,[1,1],48000,2,0)),
                        (exact_psd_bin,(1,0,[1,1],Fraction(48000),2,2)),
                        (exact_psd_bin,(1,0,[1,1],Fraction(48000),2,True)),
                        (exact_amplitude_bin,(1,1,4,5)),
                        (stable_welch_mean,([1,-1],))]:
            with self.subTest(fn=fn.__name__,args=str(args)):
                with self.assertRaises(ValueError):fn(*args)

    def test_fuzz_scale_invariance_for_rms(self):
        rng=random.Random(8675309)
        for _ in range(80):
            x=[rng.uniform(-1,1) for _ in range(19)]
            k=2.0**rng.randint(-400,400)
            self.assertAlmostEqual(stable_rms([v*k for v in x])/(stable_rms(x)*k),1.0,delta=5e-15)


if __name__ == '__main__':unittest.main()
