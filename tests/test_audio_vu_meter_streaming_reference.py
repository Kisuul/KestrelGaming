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
    def test_chunk_partitions_preserve_final_state(self):
        samples=[.1*(.2+.8*math.sin(2*math.pi*(i%48)/48)) for i in range(10000)]
        expected=run(meter(),[samples],chunk=10000)['channels'][0]
        for chunk in (1,7,31,48,257,8192):
            actual=run(meter(),[samples],chunk=chunk)['channels'][0]
            self.assertEqual(actual['deflection'],expected['deflection'])
            self.assertEqual(actual['vu'],expected['vu'])

    def test_refresh_schedule_does_not_change_meter_state(self):
        samples=[constant_step_input() if i%5 else 0.0 for i in range(9600)]
        r1=run(meter(),[samples],chunk=96)
        r2=run(meter(),[samples],chunk=192)
        self.assertAlmostEqual(r1['channels'][0]['deflection'],r2['channels'][0]['deflection'],delta=0)

    def test_rate_and_labels_are_explicit(self):
        bad=[(48000,('FL',)),(Fraction(0),('FL',)),(Fraction(400000),('FL',)),
             (Fraction(48000),()),(Fraction(48000),('L','L')),
             (Fraction(48000),('L',)*9),(Fraction(48000),('L',False))]
        for rate, labels in bad:
            with self.subTest(rate=rate,labels=labels),self.assertRaises(ValueError):
                VUMeter(rate,labels,REF)

    def test_bad_blocks_atomic_rejection(self):
        m=meter(labels=('L','R'),start=100)
        m.push(100,[[.1]*3,[.1]*3]);before=(m.next_sample,m.accepted_blocks,tuple(m._states))
        for pos,planes in [(102,[[0.],[0.]]),(104,[[0.]]),
                          (103,[[0],[0,0]]),(103,[[],[]]),
                          (103,[[1.],[float('nan')]]),(103,[[True],[0.]]),
                          (103,[[0.],[1e309]]),(103,[[0.],[complex(0)]])]:
            with self.subTest(pos=pos,bad=repr(planes)):
                with self.assertRaises(ValueError):m.push(pos,planes)
                self.assertEqual((m.next_sample,m.accepted_blocks,tuple(m._states)),before)

    def test_nonfinite_detector_normalization_is_atomic(self):
        cal=ToneCalibration.digital_tone_dbfs_peak(-20)
        m=meter(ref=cal)
        before=(m.next_sample,tuple(m._states),m.accepted_blocks)
        with self.assertRaisesRegex(ValueError,'rectifier'):
            m.push(0,[[1e308]])
        self.assertEqual((m.next_sample,tuple(m._states),m.accepted_blocks),before)

    def test_nonzero_underflow_does_not_masquerade_as_silence(self):
        cal=ToneCalibration(1e100,'volts','very large calibration')
        m=meter(ref=cal)
        with self.assertRaisesRegex(ValueError,'underflows'):
            m.push(0,[[5e-324]])
        self.assertEqual(m.next_sample,0)

    def test_oversize_block_does_not_advance_cursor(self):
        m=meter();bad=[[0.0]*(MAX_BLOCK_FRAMES+1)]
        with self.assertRaises(ValueError):m.push(0,bad)
        self.assertEqual(m.next_sample,0)

    def test_epoch_reset_is_new_unique_and_atomic_on_failure(self):
        m=meter(start=100)
        m.push(100,[[.2]*20]);before=(m.next_sample,m.accepted_blocks,tuple(m._states),m.epoch_id)
        for eid,start,ref in [('epoch-0',100,None),('new',-1,None),('new',0,'bad'),('',10,None)]:
            with self.subTest(eid=eid,start=start),self.assertRaises(ValueError):
                m.reset_epoch(eid,start,ref)
            self.assertEqual((m.next_sample,m.accepted_blocks,tuple(m._states),m.epoch_id),before)
        new=ToneCalibration.digital_tone_dbfs_peak(-18)
        m.reset_epoch('new',2**54,new)
        self.assertEqual(m.next_sample,2**54)
        self.assertEqual(m.accepted_blocks,0)
        self.assertEqual(m._states,[(0.0,0.0)])
        self.assertEqual(m.calibration,new)
        with self.assertRaises(ValueError):m.reset_epoch('epoch-0',1)

    def test_change_calibration_requires_epoch(self):
        m=meter();self.assertEqual(m.calibration,REF)
        cal=ToneCalibration.digital_tone_dbfs_peak(-18)
        m.reset_epoch('recalibrated',0,cal)
        self.assertEqual(m.calibration,cal)
        self.assertNotEqual(m.calibration.reference_sine_peak,REF.reference_sine_peak)

    def test_equal_value_sinusoid_silent_zeros_have_distinct_semantics(self):
        m=meter()
        r=m.push(0,[[0.0,-0.0,0.0]])
        self.assertEqual(r['channels'][0]['deflection'],0)
        self.assertIsNone(r['channels'][0]['vu'])
        self.assertEqual(r['channels'][0]['sample_peak_in_input_units'],0)

    def test_reference_db_display_not_fake_silence_floor(self):
        self.assertIsNone(calibration_ratio_db(0))
        self.assertAlmostEqual(calibration_ratio_db(.5),-6.020599913279624)
        self.assertAlmostEqual(calibration_ratio_db(1),0)
        for x in (-1,math.inf,math.nan):
            with self.assertRaises(ValueError):calibration_ratio_db(x)

    def test_partial_input_channels_never_summed(self):
        m=meter(labels=('FL','FR'))
        a=[.1]*5000
        b=[-.1]*5000
        r=run(m,[a,b]);self.assertAlmostEqual(r['channels'][0]['vu'],r['channels'][1]['vu'])
        self.assertGreater(r['channels'][0]['deflection'],0)

    def test_pointer_is_not_ideal_rms_of_interval(self):
        # Same amplitude single block as RMS=1; needle is still far below 1
        # after 10ms because it has 300ms transient response.
        m=meter();v=constant_step_input()
        r=m.push(0,[[v]*480])
        self.assertLess(r['channels'][0]['deflection'],.02)
        self.assertAlmostEqual(r['channels'][0]['sample_peak_in_input_units'],v)

    def test_output_has_named_instrument_provenance(self):
        m=meter()
        r=m.push(0,[[.1]*10])
        self.assertIn('full-wave rectified',r['detector'])
        self.assertFalse(r['standards_conformance'])
        self.assertEqual(r['calibration_label'],REF.reference_label)
        self.assertEqual(r['epoch_id'],'epoch-0')
        self.assertFalse(r['clipped_audio'])



if __name__ == "__main__":
    unittest.main()
