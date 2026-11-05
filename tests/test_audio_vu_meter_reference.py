"""Independent analytical, meter semantics and adversarial validation cases."""
from fractions import Fraction
from pathlib import Path
import math
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/audio-vu-metering/scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_vu_meter import (
    ToneCalibration, VUMeter, damping_ratio_for_overshoot,
    expected_unit_step, calibration_ratio_db, VU_OVERSHOOT_FRACTION,
    MAX_BLOCK_FRAMES,
)
from vu_meter_test_support import RATE, REF, meter, run, constant_step_input


class VUMeterReferenceTests(unittest.TestCase):
    def test_calibration_default_is_explicit_20dbfs_peak_tone(self):
        self.assertAlmostEqual(REF.reference_sine_peak, .1, places=15)
        self.assertIn('dBFS-peak', REF.reference_label)
        self.assertIn('PCM', REF.input_unit)

    def test_alternative_minus_18_dbfs_is_a_different_choice(self):
        cal = ToneCalibration.digital_tone_dbfs_peak(-18)
        self.assertAlmostEqual(cal.reference_sine_peak, 10**(-18/20), places=15)
        self.assertNotEqual(cal.reference_sine_peak, REF.reference_sine_peak)

    def test_analog_plus_4dbu_is_voltage_not_digital(self):
        cal = ToneCalibration.analog_tone_dbu()
        self.assertAlmostEqual(cal.reference_sine_peak/math.sqrt(2),
                               .775*10**(.2), places=13)
        self.assertEqual(cal.input_unit, 'volts')

    def test_analog_zero_dbu_is_775mv_rms(self):
        cal = ToneCalibration.analog_tone_dbu(0)
        self.assertAlmostEqual(cal.reference_sine_peak/math.sqrt(2), .775, places=15)

    def test_digital_alignment_cannot_exceed_full_scale(self):
        for db in (0.01, 2, 50, math.inf, math.nan, True, '4'):
            with self.subTest(db=db), self.assertRaises(ValueError):
                ToneCalibration.digital_tone_dbfs_peak(db)

    def test_tone_calibration_invalid_values(self):
        for value in (0, -1, math.nan, math.inf, True, '0.1', 10**500):
            with self.subTest(value=str(value)[:30]), self.assertRaises(ValueError):
                ToneCalibration(value, 'PCM', '0 VU')
        for args in ((.1, '', '0 VU'), (.1, 'PCM', ''), (.1, 17, '0 VU')):
            with self.assertRaises(ValueError):
                ToneCalibration(*args)

    def test_analog_outside_float_range_rejected(self):
        for db in (-10000, 10000):
            with self.subTest(db=db), self.assertRaises(ValueError):
                ToneCalibration.analog_tone_dbu(db)

    def test_damping_ratio_hard_numeric_reference(self):
        self.assertAlmostEqual(damping_ratio_for_overshoot(.0125),
                               .8127169864286775, places=13)
        for value in (0, 1, -1, math.inf, math.nan):
            with self.assertRaises(ValueError):
                damping_ratio_for_overshoot(value)

    def test_analytic_0_to_99_percent_in_300ms(self):
        self.assertEqual(expected_unit_step(0), 0)
        self.assertAlmostEqual(expected_unit_step(.1), .43508684911749607, delta=2e-12)
        self.assertAlmostEqual(expected_unit_step(.16), .7180364715485825, delta=2e-12)
        self.assertAlmostEqual(expected_unit_step(.2), .8452902480743435, delta=2e-12)
        self.assertLess(expected_unit_step(.299), .99)
        self.assertAlmostEqual(expected_unit_step(.3), .99, delta=2e-12)
        self.assertGreater(expected_unit_step(.301), .99)

    def test_analytic_peak_is_1point25_percent_after_300ms(self):
        tpeak = .39904222172960185
        self.assertAlmostEqual(expected_unit_step(tpeak), 1.0125, delta=1e-12)
        self.assertLess(expected_unit_step(.3), 1.0)
        self.assertLess(expected_unit_step(.55), 1.0125)
        self.assertAlmostEqual(VU_OVERSHOOT_FRACTION, .0125)

    def test_exact_zoh_sampled_step_matches_continuous_response(self):
        m = meter()
        level = constant_step_input()
        for ms in (100, 160, 200, 300, 399, 600):
            end = int(48000*ms/1000)
            previous = m.next_sample
            output=run(m, [[level]*(end-previous)])
            self.assertAlmostEqual(output['channels'][0]['deflection'],
                                   expected_unit_step(ms/1000), delta=1.5e-10)
        self.assertTrue(math.isfinite(output['channels'][0]['vu']))

    def test_1khz_tone_burst_reaches_about_99_percent_at_300ms(self):
        m = meter()
        n = 14400
        tone = [.1*math.sin(2*math.pi*(i % 48)/48) for i in range(n)]
        output = m.push(0, [tone])
        # A sampled rectified sinusoid is *not* the ideal constant detector
        # step used to set the model; this checks actual tone stimulus.
        self.assertAlmostEqual(output['channels'][0]['deflection'],.99,delta=.002)

    def test_fall_after_steady_detector_step_has_timed_response(self):
        m = meter()
        v = constant_step_input()
        run(m, [[v]*96000])
        r=run(m, [[0.0]*14400])
        # A linear second-order model with settled x=1 falls by the same
        # complement of its 300ms step response: 1-0.99 = 0.01.
        self.assertAlmostEqual(r['channels'][0]['deflection'],.01,delta=.0005)
        self.assertEqual(r['channels'][0]['sample_peak_in_input_units'],0)
        self.assertFalse(r['standards_conformance'])

    def test_tone_1khz_minus20dbfs_steady_is_near_zero_vu(self):
        m=meter()
        n=96000
        samples=[.1*math.sin(2*math.pi*(i % 48)/48) for i in range(n)]
        result=run(m,[samples])
        self.assertAlmostEqual(result['channels'][0]['vu'],0,delta=.03)
        self.assertFalse(result['channels'][0]['outside_plus_3_vu_scale'])



if __name__ == "__main__":
    unittest.main()
