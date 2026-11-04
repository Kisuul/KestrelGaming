"""Analytic, adversarial, frozen independent SciPy and streaming filter tests."""
from fractions import Fraction
from pathlib import Path
import math
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-filter-design/scripts"))
from reference_filter_design import (
    FIRDesign, SOSDesign, Biquad, FilterStream, design_fir, design_biquad,
    quantize_biquad, frequency_response, group_delay_samples, sampled_band_check,
    MAX_TAPS, MAX_FRAMES,
)

FS = Fraction(48000)
F = lambda x: Fraction(x)
DB = lambda x: 20*math.log10(abs(x)) if abs(x) != 0 else -math.inf

# Generated outside the Kestrel implementation with scipy.signal.firwin and
# scipy.signal.butter, SciPy 1.17.0 and NumPy 2.3.5; see provenance record.
GOLDENS = {
    'lowpass': (-0.0006479603817522975, -0.0014439790529392961,
                -0.0027022579652495864, -0.0044407447476883695,
                -0.006191484537174384, 0.1246722937474823),
    'highpass': (0.0006498831967555345, 0.0014482640442219845,
                 0.002710276884776917, 0.004453922606808806,
                 0.0062098576965458835, 0.8752958014476521),
    'bandpass': (-0.0006871589955078122, -0.0014082524143321342,
                 -0.0018797404136403947, -0.0018274939332741903,
                 -0.0011290553867157737, 0.16618247322398538),
    'bandstop': (0.0006865094549125035, 0.00140692125645234,
                 0.001877963579290142, 0.0018257664851797951,
                 0.0011279881412706615, 0.8301269419073869),
}
BUTTER2_3K = (0.02995458, 0.05990916, 0.02995458, -1.45424359, 0.57406192)


class FilterDesignTests(unittest.TestCase):
    def test_fir_exact_sample_rate_and_causal_delay(self):
        p = design_fir('lowpass', FS, (F(3000),), 31)
        self.assertEqual(p.sample_rate_hz, FS)
        self.assertEqual(p.cutoff_hz, (F(3000),))
        self.assertEqual(p.delay_samples, F(15))
        self.assertEqual(p.delay_seconds, Fraction(1, 3200))
        self.assertEqual(len(p.taps), 31)

    def test_fir_symmetry_and_dc_gain(self):
        p = design_fir('lowpass', FS, (F(3000),), 65)
        self.assertEqual(p.taps, p.taps[::-1])
        self.assertAlmostEqual(math.fsum(p.taps), 1.0, delta=3e-15)
        self.assertAlmostEqual(abs(frequency_response(p, F(0))), 1.0, delta=3e-15)

    def test_fir_highpass_nyquist_gain_zero_dc(self):
        p = design_fir('highpass', FS, (F(3000),), 65)
        self.assertAlmostEqual(abs(frequency_response(p, FS/2)), 1.0, delta=3e-15)
        self.assertLess(abs(frequency_response(p, F(0))), 0.005)  # finite window leakage
        self.assertEqual(p.delay_samples, F(32))

    def test_fir_bandpass_edges_and_midpoint(self):
        p = design_fir('bandpass', FS, (F(2000),F(6000)), 65)
        self.assertAlmostEqual(abs(frequency_response(p, F(4000))), 1.0, delta=2e-14)
        self.assertLess(abs(frequency_response(p, F(0))), 0.01)
        self.assertLess(abs(frequency_response(p, FS/2)), 0.001)

    def test_fir_bandstop_dc_and_notch_region(self):
        p = design_fir('bandstop', FS, (F(2000),F(6000)), 65)
        self.assertAlmostEqual(abs(frequency_response(p, F(0))), 1.0, delta=1e-14)
        self.assertLess(abs(frequency_response(p, F(4000))), 0.05)

    def test_fir_cutoff_is_half_amplitude_not_three_db(self):
        p = design_fir('lowpass', FS, (F(3000),), 129)
        at = abs(frequency_response(p, F(3000)))
        self.assertAlmostEqual(at, 0.5, delta=0.01)
        self.assertAlmostEqual(DB(at), -6.020599913, delta=0.25)
        self.assertGreater(abs(DB(at)+3.010299956), 2.0)

    def test_hann_hamming_blackman_windows_differ(self):
        p = [design_fir('lowpass', FS, (F(3000),), 65, w)
             for w in ('hann','hamming','blackman')]
        self.assertTrue(all(z.taps == z.taps[::-1] for z in p))
        self.assertNotEqual(p[0].taps, p[1].taps)
        self.assertNotEqual(p[1].taps, p[2].taps)
        self.assertLess(abs(p[0].taps[0]), 1e-15)
        self.assertNotEqual(p[1].taps[0], 0.0)

    def test_fir_half_amplitude_property_other_kinds(self):
        high = design_fir('highpass', FS, (F(5000),), 129)
        at = abs(frequency_response(high, F(5000)))
        self.assertAlmostEqual(at, 0.5, delta=0.01)

    def test_fir_bad_specs_and_coefficient_validation(self):
        invalid = [
            ('lowpass', FS, (F(3000),), 4, 'hamming'),
            ('lowpass', FS, (F(3000),), 6, 'hamming'),
            ('lowpass', FS, (F(3000),), 131, 'hamming'),
            ('lowpass', F(48000), (F(0),), 31, 'hamming'),
            ('lowpass', FS, (F(24000),), 31, 'hamming'),
            ('lowpass', FS, (F(25000),), 31, 'hamming'),
            ('lowpass', FS, (3000,), 31, 'hamming'),
            ('bandpass', FS, (F(8000),F(1000)), 31, 'hamming'),
            ('bandpass', FS, (F(3000),), 31, 'hamming'),
            ('lowpass', FS, (F(3000),), 31, 'kaiser'),
            ('shelf', FS, (F(3000),), 31, 'hamming'),
            ('lowpass', 48000, (F(3000),), 31, 'hamming'),
        ]
        for spec in invalid:
            with self.subTest(spec=spec):
                with self.assertRaises(ValueError):
                    design_fir(*spec)
        p=design_fir('lowpass',FS,(F(3000),),31)
        with self.assertRaises(ValueError):
            FIRDesign(FS,'lowpass',(F(3000),),'hamming',p.taps[:-1]+(math.inf,))

    def test_frozen_scipy_firwin_goldens(self):
        cases=[('lowpass',(F(3000),),31),('highpass',(F(3000),),31),
               ('bandpass',(F(2000),F(6000)),65),('bandstop',(F(2000),F(6000)),65)]
        for kind, edges, n in cases:
            with self.subTest(kind=kind):
                taps=design_fir(kind,FS,edges,n).taps
                ref=GOLDENS[kind]
                for a,b in zip(taps[:5]+(taps[n//2],),ref):
                    self.assertAlmostEqual(a,b,delta=3e-13)

    def test_butterworth_biquad_lowpass_corner_minus_3db(self):
        p=design_biquad('lowpass',FS,F(3000))
        self.assertAlmostEqual(abs(frequency_response(p,F(0))),1,delta=1e-13)
        self.assertAlmostEqual(abs(frequency_response(p,F(3000))),2**-0.5,delta=1e-12)
        self.assertLess(abs(frequency_response(p,FS/2)),1e-12)
        self.assertAlmostEqual(DB(frequency_response(p,F(3000))),-3.0102999566,delta=1e-9)

    def test_butterworth_biquad_highpass_corner_minus_3db(self):
        p=design_biquad('highpass',FS,F(3000))
        self.assertLess(abs(frequency_response(p,F(0))),1e-12)
        self.assertAlmostEqual(abs(frequency_response(p,F(3000))),2**-0.5,delta=1e-12)
        self.assertAlmostEqual(abs(frequency_response(p,FS/2)),1,delta=1e-12)

    def test_biquad_notch_center_and_side_response(self):
        p=design_biquad('notch',FS,F(4000),q=4)
        self.assertLess(abs(frequency_response(p,F(4000))),1e-12)
        self.assertAlmostEqual(abs(frequency_response(p,F(0))),1,delta=1e-12)
        self.assertAlmostEqual(abs(frequency_response(p,FS/2)),1,delta=1e-12)

    def test_biquad_peaking_positive_and_negative_gain(self):
        for gain in [-12.,0.,6.,24.]:
            with self.subTest(gain=gain):
                p=design_biquad('peaking',FS,F(5000),q=1,gain_db=gain)
                self.assertAlmostEqual(DB(frequency_response(p,F(5000))),gain,delta=1e-11)
                self.assertAlmostEqual(abs(frequency_response(p,F(0))),1,delta=1e-12)
                self.assertAlmostEqual(abs(frequency_response(p,FS/2)),1,delta=1e-12)

    def test_biquad_frozen_scipy_butter_2pole(self):
        b=design_biquad('lowpass',FS,F(3000)).sections[0]
        for a,ref in zip((b.b0,b.b1,b.b2,b.a1,b.a2),BUTTER2_3K):
            self.assertAlmostEqual(a,ref,delta=1e-8)

    def test_biquad_q_is_not_bandwidth_or_automatic_gain(self):
        p=design_biquad('lowpass',FS,F(4000),q=3)
        self.assertAlmostEqual(abs(frequency_response(p,F(4000))),3,delta=1e-12)
        self.assertGreater(abs(frequency_response(p,F(4000))),1)
        self.assertLess(p.sections[0].max_pole_radius,1)

    def test_sos_composition_frequency_response(self):
        a=design_biquad('lowpass',FS,F(3000))
        b=design_biquad('notch',FS,F(4000),q=3)
        both=SOSDesign(FS,a.sections+b.sections,'explicit cascade')
        for freq in [F(0),F(2000),F(5000),F(16000)]:
            with self.subTest(f=freq):
                expected=frequency_response(a,freq)*frequency_response(b,freq)
                self.assertAlmostEqual(abs(frequency_response(both,freq)-expected),0,delta=1e-14)
        self.assertEqual(len(both.sections),2)

    def test_biquad_stable_poles_and_reject_unstable(self):
        for kind in ('lowpass','highpass','notch','peaking'):
            p=design_biquad(kind,FS,F(5000),q=10,gain_db=(6 if kind=='peaking' else 0))
            self.assertGreater(p.sections[0].max_pole_radius,0)
            self.assertLess(p.sections[0].max_pole_radius,1)
        for section in [(1,0,0,2,1),(1,0,0,-2,1),(1,0,0,0,1.1),
                        (1,0,0,0,math.nan),(True,0,0,0,0)]:
            with self.subTest(section=section):
                with self.assertRaises(ValueError):
                    Biquad(*section)

    def test_biquad_invalid_parameters(self):
        cases = [
            ('lowpass',FS,F(0),1,0),('lowpass',FS,F(24000),1,0),
            ('lowpass',FS,F(3000),0,0),('lowpass',FS,F(3000),25,0),
            ('lowpass',FS,F(3000),math.nan,0),('lowpass',FS,F(3000),1,3),
            ('peaking',FS,F(3000),1,25),('peaking',FS,F(3000),1,math.inf),
            ('shelf',FS,F(3000),1,0),('lowpass',F(1000),F(300),1,0),
        ]
        for spec in cases:
            with self.subTest(spec=spec):
                with self.assertRaises(ValueError):
                    design_biquad(*spec)

    def test_coefficient_quantization_changes_response_and_checks_poles(self):
        p=design_biquad('lowpass',FS,F(3000)).sections[0]
        q,err=quantize_biquad(p,12)
        self.assertGreater(err,0)
        self.assertLessEqual(err,0.5/4096)
        self.assertLess(q.max_pole_radius,1)
        self.assertNotEqual((q.b0,q.a1),(p.b0,p.a1))
        for bits in [0,3,31,True]:
            with self.subTest(bits=bits):
                with self.assertRaises(ValueError):
                    quantize_biquad(p,bits)
        with self.assertRaises(ValueError):
            quantize_biquad(Biquad(1,0,0,-1.999,0.999001),4)

    def test_group_delay_fir_is_constant_away_from_nulls(self):
        for kind,edges in [('lowpass',(F(3000),)),('highpass',(F(3000),)),
                           ('bandpass',(F(2000),F(6000)))]:
            p=design_fir(kind,FS,edges,65)
            f=F(1500) if kind=='lowpass' else (F(14000) if kind=='highpass' else F(4000))
            self.assertAlmostEqual(group_delay_samples(p,f),32,delta=1e-8)

    def test_group_delay_iir_varies_with_frequency(self):
        p=design_biquad('lowpass',FS,F(3000))
        low=group_delay_samples(p,F(1000))
        high=group_delay_samples(p,F(12000))
        self.assertGreater(low,0)
        self.assertGreater(high,0)
        self.assertGreater(low,high)
        self.assertNotAlmostEqual(low,high,delta=0.01)

    def test_group_delay_rejects_endpoint_and_response_null(self):
        p=design_biquad('notch',FS,F(4000),q=4)
        for freq in (F(0),F(4000),FS/2):
            with self.subTest(freq=freq):
                with self.assertRaises(ValueError):
                    group_delay_samples(p,freq)

    def test_response_invalid_frequencies_and_plan(self):
        p=design_fir('lowpass',FS,(F(3000),),31)
        for freq in (-1, F(-1),F(24001), 3000, Fraction(1,0) if False else '3'):
            with self.subTest(freq=freq):
                with self.assertRaises(ValueError):
                    frequency_response(p,freq)
        with self.assertRaises(ValueError):
            frequency_response('not a filter',F(2000))

    def test_sampled_band_specification_pass_and_fail(self):
        p=design_fir('lowpass',FS,(F(3000),),129)
        good=sampled_band_check(p,((F(0),F(1500)),),((F(8000),F(23000)),),
                                passband_tolerance_db=0.5,stopband_min_attenuation_db=40,
                                samples_per_band=65)
        self.assertTrue(good.meets_sampled_targets)
        self.assertEqual(good.samples_examined,130)
        bad=sampled_band_check(p,((F(0),F(2900)),),((F(3100),F(6000)),),
                               passband_tolerance_db=0.1,stopband_min_attenuation_db=80)
        self.assertFalse(bad.meets_sampled_targets)
        self.assertGreater(bad.stopband_max_db,-80)

    def test_sampled_band_screen_rejects_malformed_domains(self):
        p=design_fir('lowpass',FS,(F(3000),),31)
        for pb,sb,db,rej,n in [
            ((),((F(8000),F(24000)),),0.5,40,81),
            (((F(1000),F(0)),),((F(8000),F(24000)),),0.5,40,81),
            (((F(0),F(1000)),),((F(24000),F(25000)),),0.5,40,81),
            (((F(0),F(1000)),),((F(8000),F(24000)),),-1,40,81),
            (((F(0),F(1000)),),((F(8000),F(24000)),),0.5,math.inf,81),
            (((F(0),F(1000)),),((F(8000),F(24000)),),0.5,40,2),
        ]:
            with self.subTest(pb=pb, sb=sb):
                with self.assertRaises(ValueError):
                    sampled_band_check(p,pb,sb,db,rej,n)

    def test_fir_impulse_and_zero_initial_state(self):
        p=design_fir('lowpass',FS,(F(3000),),31)
        stream=FilterStream(p,'epoch',0,1)
        result=stream.push(0,[[1.]+[0.]*30])
        for a,b in zip(result['planar_samples'][0],p.taps):
            self.assertAlmostEqual(a,b,delta=1e-15)
        self.assertEqual(result['end_sample_exclusive'],31)

    def test_fir_step_response_approaches_declared_dc_gain(self):
        p=design_fir('lowpass',FS,(F(3000),),31)
        out=FilterStream(p,'e',0,1).push(0,[[1.]*96])['planar_samples'][0]
        self.assertAlmostEqual(out[-1],1.0,delta=1e-14)
        self.assertTrue(any(abs(y-1)>0.01 for y in out[:20]))
        hp=design_fir('highpass',FS,(F(3000),),31)
        h=FilterStream(hp,'e',0,1).push(0,[[1.]*96])['planar_samples'][0]
        self.assertLess(abs(h[-1]),0.005)  # finite window stopband leakage

    def test_biquad_first_impulse_matches_closed_form_difference_equation(self):
        design=design_biquad('lowpass',FS,F(3000))
        b=design.sections[0]
        r=FilterStream(design,'e',0,1).push(0,[[1,0,0,0,0]])['planar_samples'][0]
        self.assertAlmostEqual(r[0],b.b0,delta=1e-15)
        self.assertAlmostEqual(r[1],b.b1-b.a1*r[0],delta=1e-15)
        self.assertAlmostEqual(r[2],b.b2-b.a1*r[1]-b.a2*r[0],delta=1e-15)

    def test_streaming_chunk_invariance_fir_and_sos(self):
        designs=[design_fir('lowpass',FS,(F(3500),),31),
                 SOSDesign(FS,design_biquad('lowpass',FS,F(4500)).sections+
                                design_biquad('peaking',FS,F(2200),gain_db=6).sections,
                           'two-stage test chain')]
        x=[math.sin(math.tau*7*i/97)+0.2*math.cos(math.tau*3*i/97)
           for i in range(97)]
        origin=2**54+123
        for plan in designs:
            whole=FilterStream(plan,'e',origin,2).push(origin,[x,[-v for v in x]])['planar_samples']
            for pattern in ((97,), (1,), (7,13,3), (31,10)):
                with self.subTest(plan=type(plan).__name__, pattern=pattern):
                    stream=FilterStream(plan,'e',origin,2)
                    out=[[],[]]
                    n=0;i=0
                    while i<len(x):
                        size=min(pattern[n%len(pattern)],len(x)-i)
                        block=stream.push(origin+i,[x[i:i+size],[-v for v in x[i:i+size]]])
                        for k in range(2):out[k].extend(block['planar_samples'][k])
                        i+=size;n+=1
                    self.assertEqual(out,whole)
                    self.assertEqual(stream.next_sample,origin+97)
                    self.assertEqual(stream.accepted_blocks,n)

    def test_stereo_channel_state_is_independent(self):
        p=design_biquad('lowpass',FS,F(3000))
        r=FilterStream(p,'e',0,2)
        first=r.push(0,[[1.]+[0.]*31,[0.]*32])['planar_samples']
        self.assertTrue(any(abs(v)>0 for v in first[0]))
        self.assertEqual(first[1],[0.]*32)
        second=r.push(32,[[0.]*32,[1.]+[0.]*31])['planar_samples']
        self.assertTrue(any(abs(v)>0 for v in second[1]))

    def test_no_silent_clamping_or_reference_fullscale_assumption(self):
        fir=design_fir('lowpass',FS,(F(3000),),31)
        vals=FilterStream(fir,'e',0,1).push(0,[[100.]*31])
        self.assertTrue(any(abs(v)>1 for v in vals['planar_samples'][0]))
        self.assertFalse(vals['clipped'])
        self.assertGreater(vals['over_reference_by_channel'][0],0)

    def test_gap_overlap_and_invalid_data_fail_atomically(self):
        p=design_biquad('lowpass',FS,F(3000))
        stream=FilterStream(p,'e',100,1)
        stream.push(100,[[0.5]*8]);before=(stream.next_sample,stream.accepted_blocks)
        cases=[(107,[[0.]]),(109,[[0.]]),(108,[[]]),(108,[[math.nan]]),
               (108,[[math.inf]]),(108,[[True]]),(108,[[0.]* (MAX_FRAMES+1)]),
               (108,[[10**400]])]
        for at,samples in cases:
            with self.subTest(start=at,samples=repr(samples)[:20]):
                with self.assertRaises(ValueError):stream.push(at,samples)
                self.assertEqual((stream.next_sample,stream.accepted_blocks),before)

    def test_numeric_overflow_rejects_atomic_fir(self):
        p=design_fir('lowpass',FS,(F(3000),),31)
        stream=FilterStream(p,'a',0,1)
        pattern = [1.7e308 * (1 if v >= 0 else -1) for v in p.taps]
        with self.assertRaises(ValueError):stream.push(0,[pattern])
        self.assertEqual((stream.next_sample,stream.accepted_blocks),(0,0))
        self.assertEqual(stream.push(0,[[0.1]])['frames'],1)

    def test_numeric_overflow_rejects_atomic_sos(self):
        p=design_biquad('peaking',FS,F(5000),q=0.3,gain_db=24)
        stream=FilterStream(p,'a',0,1)
        with self.assertRaises(ValueError):stream.push(0,[[1e308]*64])
        self.assertEqual((stream.next_sample,stream.accepted_blocks),(0,0))
        self.assertEqual(stream.push(0,[[0.1]])['frames'],1)

    def test_reconfiguration_resets_state_and_uses_unique_epoch(self):
        p=design_fir('lowpass',FS,(F(3000),),31)
        q=design_biquad('highpass',FS,F(3000))
        stream=FilterStream(p,'old',2**54+3,1)
        stream.push(2**54+3,[[0.5]*30])
        before=(stream.next_sample,stream.epoch_id,stream.accepted_blocks)
        for epoch,origin,plan,ch in [('old',0,q,1),('new',-1,q,1),
                                     ('new',100,'unknown',1),('new',100,q,9)]:
            with self.subTest(epoch=epoch,origin=origin):
                with self.assertRaises(ValueError):stream.reset_epoch(epoch,origin,plan,ch)
                self.assertEqual((stream.next_sample,stream.epoch_id,stream.accepted_blocks),before)
        stream.reset_epoch('new',100,q,2)
        self.assertEqual(stream.push(100,[[1],[0]])['start_sample'],100)
        self.assertEqual(stream.channels,2)
        with self.assertRaises(ValueError):stream.reset_epoch('old',400)
        stream.reset_epoch('final',50,p)
        self.assertEqual(stream.accepted_blocks,0)
        self.assertEqual(stream.next_sample,50)

    def test_filterstream_validation_and_rate_preservation(self):
        p=design_fir('lowpass',FS,(F(3000),),31)
        for plan,epoch,start,channels in [(p,'',0,1),(p,'e',-1,1),(p,'e',0,0),
                                          (p,'e',0,9),(p,'e',0,True),('fake','e',0,1)]:
            with self.subTest(epoch=epoch,start=start,channels=channels):
                with self.assertRaises(ValueError):FilterStream(plan,epoch,start,channels)
        res=FilterStream(p,'e',2**54+1,1).push(2**54+1,[[1.]])
        self.assertEqual(res['start_sample'],2**54+1)
        self.assertEqual(res['sample_rate_hz'],FS)
        self.assertEqual(res['end_sample_exclusive'],2**54+2)


if __name__=='__main__':unittest.main()
