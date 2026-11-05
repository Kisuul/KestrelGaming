"""Falsifiable educational PPM tests. EBU burst values are *fitting* targets.

The historical Type IIb normal-mode burst constraints were pre-registered in
2026-11-05 research; matching them does NOT establish full EBU/IEC conformance.
"""
from fractions import Fraction
from pathlib import Path
import math
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       'skills/audio-ppm-metering/scripts'))
from reference_ppm import (PpmStream, PpmConfiguration, amplitude_db,
                           synthetic_sine_burst, PROFILE, FAST_TAU_S,
                           SLOW_TAU_S, FAST_WEIGHT, RELEASE_TAU_S,
                           test_tone_peak_voltage)

# Source: EBU Tech 3205-E, 1979, Table 2 normal-mode test.
# (duration ms, tone Hz, target level in dB relative TEST, tolerance dB).
EBU_BURST = ((100., 5000., 8., .5), (10., 5000., 6., .5),
             (5., 5000., 4., .75), (1.5, 5000., -1., 1.),
             (.5, 10000., -9., 2.))


def cfg(fs=48000,channels=1,reference=1.0):
    return PpmConfiguration(Fraction(fs),channels,reference,'normalized PCM')


def push_all(meter,channels,origin=0,pattern=(256,)):
    count=len(channels[0]);p=0;j=0;last=None;peak=[-math.inf]*len(channels)
    while p<count:
        n=min(pattern[j%len(pattern)],count-p)
        last=meter.push(origin+p,[c[p:p+n] for c in channels])
        peak=[max(a,b) for a,b in zip(peak,last['max_db_re_TEST_in_block'])]
        p+=n;j+=1
    return last,peak


class EbuPublishedAcceptanceTests(unittest.TestCase):
    def test_all_five_published_normal_mode_bursts_all_four_rates(self):
        for fs in (44100,48000,96000,192000):
            for ms,frequency,expected,tolerance in EBU_BURST:
                with self.subTest(fs=fs,ms=ms):
                    p=PpmStream(cfg(fs),epoch_id='known',start_sample=0)
                    samples=synthetic_sine_burst(
                        frequency_hz=frequency,sample_rate_hz=Fraction(fs),
                        duration_ms=ms,peak_amplitude=10**(8/20))
                    _,peaks=push_all(p,[samples],pattern=(31,7,199,256))
                    self.assertLessEqual(abs(peaks[0]-expected),tolerance,
                        f'EBU Tech 3205 Table 2 at {ms}ms / {fs}Hz: observed {peaks[0]:.3f} dB')

    def test_burst_phase_holdout_and_all_rates(self):
        for fs in (44100,48000,96000,192000):
            for phase in (0.,math.pi/5,math.pi/2,-math.pi/3):
                for ms,frequency,expected,tolerance in EBU_BURST:
                    with self.subTest(fs=fs,phase=phase,ms=ms):
                        stream=PpmStream(cfg(fs),epoch_id='a',start_sample=0)
                        tones=synthetic_sine_burst(frequency_hz=frequency,
                            sample_rate_hz=Fraction(fs),duration_ms=ms,
                            peak_amplitude=10**(8/20),phase_rad=phase)
                        _,mx=push_all(stream,[tones]);self.assertLessEqual(
                            abs(mx[0]-expected),tolerance+1e-12)

    def test_10ms_is_2db_under_steady_9db_itu_integration_definition(self):
        fs=48000;meter=PpmStream(cfg(fs),epoch_id='int',start_sample=0)
        tone=synthetic_sine_burst(frequency_hz=5000,sample_rate_hz=Fraction(fs),
                                  duration_ms=10,peak_amplitude=10**(9/20))
        _,maxes=push_all(meter,[tone]);self.assertAlmostEqual(maxes[0],7,delta=.5)

    def test_one_pole_at_10ms_predicts_wrong_short_bursts(self):
        # Independent mathematical falsification of the naively inferred tau.
        tau=-.010/math.log(1-10**(-2/20))
        self.assertAlmostEqual(tau,.006323,delta=.00002)
        for ms,expected,tolerance in ((5.,4.,.75),(1.5,-1.,1.),(.5,-9.,2.)):
            prediction=8+20*math.log10(1-math.exp(-ms/1000/tau))
            self.assertGreater(abs(prediction-expected),tolerance)

    def test_100ms_burst_indication_not_replaced_with_sample_peak(self):
        burst=synthetic_sine_burst(frequency_hz=5000,sample_rate_hz=Fraction(48000),
                                  duration_ms=1.5,peak_amplitude=10**(8/20))
        stream=PpmStream(cfg(),epoch_id='a',start_sample=0)
        _,m=push_all(stream,[burst])
        self.assertLess(m[0],0)
        self.assertGreater(20*math.log10(max(map(abs,burst))),7.5)

    def test_low_frequency_flatness_conformance_is_KNOWN_TO_FAIL(self):
        # Negative conformity assertion, not a softened tolerance: the model
        # is an honest burst fit and *does not* pass EBU 3205 section 2.3.
        def indication_at(f):
            stream=PpmStream(cfg(),epoch_id='flat',start_sample=0)
            tone=synthetic_sine_burst(frequency_hz=f,sample_rate_hz=Fraction(48000),
                duration_ms=400,peak_amplitude=1.0)
            last,mx=push_all(stream,[tone]);return mx[0],last
        at31,rec31=indication_at(31.5)
        at5,_=indication_at(5000)
        at16,_=indication_at(16000)
        self.assertGreater(abs(at31-at5),.3)  # Red conformance finding.
        self.assertGreater(abs(at16-at5),.3)
        self.assertFalse(rec31['standards_conformance'])
        self.assertIn('flatness',rec31['known_failed_requirement'])

    def test_sample_rate_specific_shortest_burst_five_cycles(self):
        for fs in (44100,48000,96000,192000):
            x=synthetic_sine_burst(frequency_hz=10000,sample_rate_hz=Fraction(fs),
                duration_ms=.5,peak_amplitude=1)
            self.assertGreaterEqual(len(x),math.ceil(fs*.0005))
            self.assertTrue(all(math.isfinite(v) for v in x))

    def test_release_24db_in_2point8s_not_an_attack_constant(self):
        # 0 dBu reference; establish 1kHz +12 for 400ms then silence.
        fs=48000;st=PpmStream(cfg(),epoch_id='release',start_sample=0)
        x=synthetic_sine_burst(frequency_hz=1000,sample_rate_hz=Fraction(fs),
                               duration_ms=400,peak_amplitude=10**(12/20))
        prior,_=push_all(st,[x])
        initial=prior['indication_db_re_TEST'][0]
        self.assertAlmostEqual(initial,12,delta=.35)
        elapsed=0.;hit=None
        zeros=[0.]*256
        for i in range(0,fs*4,256):
            n=min(256,fs*4-i)
            last=st.push(st.next_sample,[zeros[:n]])
            elapsed+=n/fs
            if hit is None and last['indication_db_re_TEST'][0] <= initial-24:
                hit=elapsed
                break
        self.assertIsNotNone(hit)
        self.assertAlmostEqual(hit,2.8,delta=.3)
        self.assertAlmostEqual(RELEASE_TAU_S,2.8/(24*math.log(10)/20),places=14)

    def test_1khz_9db_tone_crosses_8db_in_under_150ms(self):
        fs=48000;st=PpmStream(cfg(),epoch_id='delay',start_sample=0)
        x=synthetic_sine_burst(frequency_hz=1000,sample_rate_hz=Fraction(fs),
                               duration_ms=150,peak_amplitude=10**(9/20))
        first=None
        for i in range(0,len(x),256):
            result=st.push(i,[x[i:i+256]])
            for j,v in enumerate(result['indications_db_by_channel'][0]):
                if v>=8 and first is None:first=i+j
        self.assertIsNotNone(first)
        self.assertLessEqual(first/fs,.150)

    def test_1khz_9db_overswing_under_half_db(self):
        fs=48000;st=PpmStream(cfg(),epoch_id='over',start_sample=0)
        x=synthetic_sine_burst(frequency_hz=1000,sample_rate_hz=Fraction(fs),
            duration_ms=400,peak_amplitude=10**(9/20))
        _,mx=push_all(st,[x]);self.assertLessEqual(mx[0]-9,.5)

    def test_1khz_test_tone_voltage_alignment_and_reference_point(self):
        self.assertAlmostEqual(test_tone_peak_voltage(),math.sqrt(2)*.775,places=15)
        cfg_v=PpmConfiguration(Fraction(48000),1,test_tone_peak_voltage(),'V')
        st=PpmStream(cfg_v,epoch_id='V',start_sample=0)
        x=synthetic_sine_burst(frequency_hz=1000,sample_rate_hz=Fraction(48000),
                               duration_ms=400,peak_amplitude=test_tone_peak_voltage())
        last,_=push_all(st,[x]);self.assertAlmostEqual(last['indication_db_re_TEST'][0],0,delta=.35)
        self.assertEqual(last['source_units'],'V')

    def test_polarity_reversal_symmetry_on_asymmetric_clipped_signal(self):
        fs=48000
        tone=synthetic_sine_burst(frequency_hz=1000,sample_rate_hz=Fraction(fs),
                               duration_ms=200,peak_amplitude=1)
        x=[.25*y if y>=0 else y for y in tone]
        a=PpmStream(cfg(),epoch_id='x',start_sample=0)
        b=PpmStream(cfg(),epoch_id='x',start_sample=0)
        la,pa=push_all(a,[x]);lb,pb=push_all(b,[[-v for v in x]])
        self.assertEqual(la['indication_db_re_TEST'],lb['indication_db_re_TEST'])
        self.assertEqual(pa,pb)

    def test_burst_dynamic_linearity_scales_amplitude_by_db(self):
        tone=synthetic_sine_burst(frequency_hz=5000,sample_rate_hz=Fraction(48000),
            duration_ms=10,peak_amplitude=1)
        indications=[]
        for db in (-12,-3,0,9,20):
            s=PpmStream(cfg(),epoch_id='linearity',start_sample=0)
            _,peak=push_all(s,[[x*10**(db/20) for x in tone]])
            indications.append(peak[0]-db)
        self.assertLess(max(indications)-min(indications),1e-10)


class StreamAndSafetyTests(unittest.TestCase):
    def test_exact_silence_has_no_fake_display_floor(self):
        s=PpmStream(cfg(),epoch_id='a',start_sample=0)
        r=s.push(0,[[0.,-0.,0.]])
        self.assertEqual(r['indication_db_re_TEST'],[-math.inf])
        self.assertEqual(r['max_db_re_TEST_in_block'],[-math.inf])
        self.assertEqual(r['indications_db_by_channel'],[[-math.inf]*3])

    def test_reference_db_stable_extreme_ratio(self):
        self.assertEqual(amplitude_db(0.,1.),-math.inf)
        self.assertAlmostEqual(amplitude_db(1e300,1e-300),12000,places=8)
        self.assertAlmostEqual(amplitude_db(1e-300,1e300),-12000,places=8)

    def test_config_requires_explicit_physical_or_pcm_reference(self):
        with self.assertRaises(TypeError):PpmConfiguration(Fraction(48000),2)
        with self.assertRaises(ValueError):PpmConfiguration(Fraction(48000),2,1.,'')
        with self.assertRaises(ValueError):PpmConfiguration(Fraction(48000),2,1.,'V',profile='BBC')
        with self.assertRaises(ValueError):PpmConfiguration(Fraction(48000),2,1.,'V',profile='VU')
        with self.assertRaises(ValueError):PpmConfiguration(Fraction(48000),2,1.,'V',profile='IEC compliant')
        self.assertIn('PARTIAL',PROFILE)

    def test_config_rejects_rate_and_channel_ambiguity(self):
        bad=[(48000,2,1.,'PCM'),(Fraction(48000),False,1.,'PCM'),
             (Fraction(48000),0,1.,'PCM'),(Fraction(48000),9,1.,'PCM'),
             (Fraction(8000),1,1.,'PCM'),(Fraction(384000),1,1.,'PCM')]
        for args in bad:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):PpmConfiguration(*args)

    def test_bad_reference_rejected(self):
        for r in (0.,-1.,float('nan'),float('inf'),True,10**400):
            with self.subTest(value=str(r)[:30]):
                with self.assertRaises(ValueError):cfg(reference=r)

    def test_malformed_block_does_not_advance_state(self):
        st=PpmStream(cfg(channels=2),epoch_id='e',start_sample=100)
        before=(st.next_sample,st.accepted_blocks,st._fast[:],st._slow[:],st._indicated[:])
        invalid=[([[0.]],100),([[],[]],100),([[0.],[0.,0.]],100),
                 ([[0.],[float('nan')]],100),([[0.],[float('inf')]],100),
                 ([[0.],[True]],100),([[1.5e308],[0.]],100),
                 ([[0.],[0.]],101),([[0.],[0.]],99),
                 ([[0.]*257,[0.]*257],100),([[0.],[None]],100)]
        for arr,start in invalid:
            with self.subTest(data=str(arr)[:35],start=start):
                with self.assertRaises(ValueError):st.push(start,arr)
                now=(st.next_sample,st.accepted_blocks,st._fast[:],st._slow[:],st._indicated[:])
                self.assertEqual(now,before)

    def test_multichannel_atomicity_if_second_channel_overflows(self):
        st=PpmStream(cfg(channels=2),epoch_id='e',start_sample=0)
        before=(st.next_sample,st._fast[:],st._slow[:],st._indicated[:])
        with self.assertRaises(ValueError):st.push(0,[[.2,.4],[.1,1.5e308]])
        self.assertEqual((st.next_sample,st._fast,st._slow,st._indicated),before)

    def test_contiguous_history_matches_arbitrary_callback_partitions(self):
        rng=random.Random(20261105)
        x=[[rng.uniform(-1,1) for _ in range(251)] for _ in range(2)]
        start=2**54+153
        reference=PpmStream(cfg(channels=2),epoch_id='z',start_sample=start)
        full,_=push_all(reference,x,origin=start,pattern=(251,))
        for pat in ((1,),(17,3,51),(256,),(7,19,2,8,11)):
            st=PpmStream(cfg(channels=2),epoch_id='z',start_sample=start)
            p=0;n=0;hist=[[],[]]
            while p<251:
                c=min(pat[n%len(pat)],251-p)
                result=st.push(start+p,[channel[p:p+c] for channel in x])
                for ch in range(2):hist[ch].extend(result['indications_db_by_channel'][ch])
                self.assertEqual(result['end_sample_exclusive'],start+p+c)
                p+=c;n+=1
            self.assertEqual(hist,full['indications_db_by_channel'])
            self.assertEqual(st.next_sample,start+251)
            self.assertEqual(st.accepted_blocks,n)

    def test_stereo_antiphase_does_not_cancel_indication(self):
        x=synthetic_sine_burst(frequency_hz=5000,sample_rate_hz=Fraction(48000),
                duration_ms=20,peak_amplitude=.75)
        s=PpmStream(cfg(channels=2),epoch_id='a',start_sample=0)
        a,_=push_all(s,[x,[-v for v in x]])
        self.assertEqual(a['indication_db_re_TEST'][0],a['indication_db_re_TEST'][1])
        self.assertGreater(a['indication_db_re_TEST'][0],-math.inf)

    def test_large_absolute_sample_index_is_exact(self):
        start=2**53+123
        s=PpmStream(cfg(),epoch_id='large',start_sample=start)
        v=s.push(start,[[.1,-.1,0.]])
        self.assertEqual((v['start_sample'],v['end_sample_exclusive']),(start,start+3))

    def test_reset_epoch_resets_state_and_enforces_never_reuse(self):
        s=PpmStream(cfg(),epoch_id='a',start_sample=0)
        s.push(0,[[1.,1.,1.]])
        prior=(s.epoch_id,s.next_sample,s.accepted_blocks,s._indicated[:])
        for e,n,c in [('a',10,None),('b',-1,None),('',10,None),('b',10,'bad')]:
            with self.subTest(e=e,n=n):
                with self.assertRaises(ValueError):s.reset_epoch(e,n,c)
                self.assertEqual((s.epoch_id,s.next_sample,s.accepted_blocks,s._indicated),prior)
        s.reset_epoch('b',2**53+1)
        self.assertEqual(s.push(2**53+1,[[0.]])['indication_db_re_TEST'],[-math.inf])
        with self.assertRaises(ValueError):s.reset_epoch('a',1)
        s.reset_epoch('c',0)
        self.assertEqual(s.epoch_id,'c')

    def test_signed_samples_above_normalized_fullscale_not_clipped(self):
        s=PpmStream(cfg(),epoch_id='a',start_sample=0)
        a=s.push(0,[[3.0,0.0,2.0]])
        self.assertFalse(a['standards_conformance'])
        self.assertEqual(a['source_units'],'normalized PCM')
        self.assertGreater(a['max_db_re_TEST_in_block'][0],-math.inf)

    def test_synthetic_fixture_rejects_impossible_frequency_and_duration(self):
        for kw in ({'frequency_hz':30000},{'duration_ms':0},{'duration_ms':-1},
                   {'frequency_hz':math.nan},{'phase_rad':math.inf}):
            args=dict(frequency_hz=5000,sample_rate_hz=Fraction(48000),duration_ms=10,peak_amplitude=1)
            args.update(kw)
            with self.assertRaises(ValueError):synthetic_sine_burst(**args)

    def test_subnormal_nonzero_input_cannot_be_labeled_silence(self):
        st=PpmStream(cfg(),epoch_id='small',start_sample=0)
        before=(st.next_sample,st.accepted_blocks,st._fast[:],st._slow[:],st._indicated[:])
        with self.assertRaisesRegex(ValueError,'underflows detector'):
            st.push(0,[[5e-324]])
        self.assertEqual((st.next_sample,st.accepted_blocks,st._fast,st._slow,st._indicated),before)

    def test_input_planes_are_not_modified(self):
        a=[-.75,.25,0.,1.5];b=[0.,-.125,.5,-1.]
        st=PpmStream(cfg(channels=2),epoch_id='keep',start_sample=0)
        st.push(0,[a,b])
        self.assertEqual(a,[-.75,.25,0.,1.5])
        self.assertEqual(b,[0.,-.125,.5,-1.])

    def test_epoch_with_new_rate_and_new_reference_is_explicit(self):
        old=cfg(48000,reference=.25)
        stream=PpmStream(old,epoch_id='old',start_sample=0)
        stream.push(0,[[.5]])
        new=cfg(96000,reference=.5)
        stream.reset_epoch('new',2**54+7,new)
        out=stream.push(2**54+7,[[.5]])
        self.assertEqual(out['sample_rate_hz'],Fraction(96000))
        self.assertEqual(out['test_tone_peak_amplitude'],.5)
        self.assertEqual(out['epoch_id'],'new')
        self.assertEqual(out['start_sample'],2**54+7)
        with self.assertRaises(ValueError):stream.reset_epoch('new',0)

    def test_100microsecond_unidirectional_pulse_criterion(self):
        # EBU Tech 3205 section 3.4: after a 1 ms unidirectional pulse
        # has been calibrated to give TEST, the 100us pulse must read <=-10.
        fs=192000
        def pulse(duration_ms):
            st=PpmStream(cfg(fs),epoch_id='p',start_sample=0)
            count=round(fs*duration_ms/1000)
            _,mx=push_all(st,[[1.]*count])
            return mx[0]
        one_ms=pulse(1.0)
        hundred_us=pulse(.1)
        self.assertLessEqual(hundred_us-one_ms,-10.)
        # This test does not prove the entire original analog pulse procedure.

    def test_processing_tail_does_not_invent_burst_peak(self):
        fs=48000;st=PpmStream(cfg(),epoch_id='p',start_sample=0)
        tone=synthetic_sine_burst(frequency_hz=5000,sample_rate_hz=Fraction(fs),
                                 duration_ms=5.,peak_amplitude=10**(8/20))
        last,peaks=push_all(st,[tone])
        after,tail=push_all(st,[[0.]*4800],origin=len(tone))
        self.assertLessEqual(tail[0],peaks[0]+1e-10)
        self.assertEqual(after['end_sample_exclusive'],len(tone)+4800)

    def test_no_support_for_implied_timebase_discontinuity(self):
        s=PpmStream(cfg(),epoch_id='a',start_sample=100)
        s.push(100,[[.2]])
        for n in (100,102):
            with self.assertRaises(ValueError):s.push(n,[[.1]])
        s.reset_epoch('seek',100)
        self.assertEqual(s.push(100,[[.3]])['frames'],1)


if __name__=='__main__':unittest.main()
