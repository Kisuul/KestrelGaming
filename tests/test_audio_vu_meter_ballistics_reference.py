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
    def test_48khz_sampled_frequency_sanity_is_not_iec_certification(self):
        readings=[]
        for frequency in (25, 1000, 10000):
            m=meter()
            # Exactly 2 s; deliberate 48 kHz 1 kHz reference and meaningful
            # LF/HF checks, NOT a full IEC bandwidth/tone burst sweep.
            samples=[.1*math.sin(2*math.pi*frequency*i/48000)
                     for i in range(96000)]
            val=run(m,[samples])['channels'][0]['vu']
            readings.append(val)
            self.assertLess(abs(val),.2)
        self.assertLess(max(readings)-min(readings),.2)

    def test_16khz_at_48khz_not_guaranteed_flat(self):
        # The physical SVI frequency specification does not follow from a
        # rectified-sample simulation. At 16 kHz, three points/cycle strongly
        # alias mean-absolute rectification in the simple model.
        m=meter()
        samples=[.1*math.sin(2*math.pi*16000*i/48000) for i in range(96000)]
        val=run(m,[samples])['channels'][0]['vu']
        self.assertLess(val,-.5)

    def test_tone_minus26dbfs_reads_minus6_vu(self):
        m=meter()
        n=96000
        peak=.1*10**(-6/20)
        samples=[peak*math.sin(2*math.pi*(i % 48)/48) for i in range(n)]
        output=run(m,[samples]);self.assertAlmostEqual(output['channels'][0]['vu'],-6,delta=.04)

    def test_same_tone_different_reference_moves_pointer_by_2db(self):
        samples=[.1*math.sin(2*math.pi*(i%48)/48) for i in range(96000)]
        a=run(meter(),[samples])['channels'][0]['vu']
        b=run(meter(ref=ToneCalibration.digital_tone_dbfs_peak(-18)),[samples])['channels'][0]['vu']
        self.assertAlmostEqual(b-a,-2,delta=.00001)

    def test_digital_and_analog_calibration_both_read_zero_for_own_tone(self):
        a=ToneCalibration.analog_tone_dbu(4)
        m=meter(ref=a)
        samples=[a.reference_sine_peak*math.sin(2*math.pi*(i%48)/48) for i in range(96000)]
        r=run(m,[samples])
        self.assertAlmostEqual(r['channels'][0]['vu'],0,delta=.03)
        self.assertEqual(r['input_unit'],'volts')
        self.assertIsNone(r['channels'][0]['sample_peak_above_input_unit_one'])

    def test_dc_is_not_a_sine_at_same_rms_vu_offset(self):
        # A sine has mean abs 2*sqrt(2)/pi * RMS. A constant/DC with same
        # RMS has mean abs RMS, and thus reads +0.912 dB on this meter.
        rms=REF.reference_sine_peak/math.sqrt(2)
        r=run(meter(),[[rms]*96000])
        want=20*math.log10(math.pi/(2*math.sqrt(2)))
        self.assertAlmostEqual(r['channels'][0]['vu'],want,delta=.002)
        self.assertGreater(want, .9)

    def test_opposite_polarities_yield_same_vu(self):
        n=48000
        tone=[.1*math.sin(2*math.pi*(i%48)/48) for i in range(n)]
        m=meter(labels=('L','R'))
        r=run(m,[tone,[-s for s in tone]])
        self.assertAlmostEqual(r['channels'][0]['deflection'],r['channels'][1]['deflection'],delta=1e-14)
        self.assertAlmostEqual(r['channels'][0]['vu'],r['channels'][1]['vu'],delta=1e-14)
        self.assertEqual(r['channel_labels'],('L','R'))

    def test_two_channel_independence(self):
        m=meter(labels=('L','R'))
        level=constant_step_input()
        r=run(m,[[level]*24000,[0.0]*24000])
        self.assertGreater(r['channels'][0]['deflection'],1)
        self.assertEqual(r['channels'][1]['deflection'],0)
        self.assertIsNone(r['channels'][1]['vu'])

    def test_impulse_is_not_shown_as_peak(self):
        m=meter()
        level=REF.reference_sine_peak
        # Keep the whole transient in ONE block: the peak diagnostic is
        # explicitly per-block, not a historical/program peak hold.
        r=m.push(0, [[level]+[0.0]*14399])
        # A one-sample impulse may produce a brief deflection, but less than
        # one-thousandth of the steady reference needle excursion.
        self.assertLess(r['channels'][0]['max_block_deflection'],.001)
        self.assertEqual(r['channels'][0]['sample_peak_in_input_units'],level)
        self.assertFalse(r['standards_conformance'])

    def test_short_burst_underrides_steady_tone_and_rms(self):
        a=meter(); b=meter()
        v=constant_step_input()
        burst=[v]*480 + [0]*23520
        steady=[v]*24000
        ra=run(a,[burst])['channels'][0]
        rb=run(b,[steady])['channels'][0]
        self.assertLess(ra['deflection'],rb['deflection'])
        self.assertLess(ra['max_block_deflection'],rb['max_block_deflection'])

    def test_0_vu_needle_is_not_0_dbfs_sample_peak(self):
        r=run(meter(),[[.1*math.sin(2*math.pi*(i%48)/48) for i in range(96000)]])
        self.assertAlmostEqual(r['channels'][0]['vu'],0,delta=.03)
        self.assertAlmostEqual(r['channels'][0]['sample_peak_in_input_units'],.1,delta=1e-14)
        self.assertFalse(r['channels'][0]['sample_peak_above_input_unit_one'])

    def test_plus_three_display_scale_not_a_clipper(self):
        m=meter()
        a=constant_step_input()*2
        r=run(m,[[a]*96000])['channels'][0]
        self.assertGreater(r['vu'],3)
        self.assertTrue(r['outside_plus_3_vu_scale'])
        self.assertFalse(run(m,[[a]*1])['clipped_audio'])

    def test_exact_sample_clock_at_origin_beyond_double_integer_limit(self):
        start=2**54+237
        m=meter(start=start)
        r=m.push(start,[[.1]*17])
        self.assertEqual(r['start_sample'],start)
        self.assertEqual(r['end_sample_exclusive'],start+17)
        self.assertEqual(m.next_sample,start+17)
        self.assertEqual(r['rate_hz'],Fraction(48000))

    def test_fractional_sample_rate_time_correct(self):
        rate=Fraction(48000*1000,1001)
        m=meter(rate=rate)
        n=round(float(rate)*.3)
        r=run(m,[[constant_step_input()]*n]);self.assertAlmostEqual(r['channels'][0]['deflection'],.99,delta=.001)
        self.assertEqual(r['rate_hz'],rate)



if __name__ == "__main__":
    unittest.main()
