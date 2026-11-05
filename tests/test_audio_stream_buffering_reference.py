"""Adversarial, analytic and independent producer-consumer FIFO fixtures."""
import math
import random
import sys
from collections import deque
from fractions import Fraction
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/audio-stream-buffering/scripts"))
from reference_stream_buffer import FrameRing, TraceSpan, MAX_CAPACITY


class RingTests(unittest.TestCase):
    def ring(self, **kw):
        return FrameRing(capacity_frames=kw.pop("capacity_frames", 4),
                         channels=kw.pop("channels", 2), rate_hz=kw.pop("rate_hz", Fraction(48000)),
                         epoch_id=kw.pop("epoch_id", "epoch0"),
                         origin_sample=kw.pop("origin_sample", 100), **kw)

    def test_initial_capacity_and_clock(self):
        r = self.ring()
        self.assertEqual((r.buffered_frames, r.free_frames, r.read_cursor, r.write_cursor), (0, 4, 100, 100))
        self.assertEqual(r.storage_latency_seconds, 0)
        self.assertEqual(r.playable_frames, 0)

    def test_exact_full_queue_and_release(self):
        r = self.ring()
        report = r.push(100, [[1, 2, 3, 4], [-1, -2, -3, -4]])
        self.assertEqual(report["buffered_frames_after"], 4)
        self.assertEqual(r.free_frames, 0)
        self.assertEqual(r.storage_latency_seconds, Fraction(4, 48000))
        result = r.pull(100, 4)
        self.assertEqual(result["planar_samples"], [[1, 2, 3, 4], [-1, -2, -3, -4]])
        self.assertEqual(result["source_frames"], 4)
        self.assertEqual(result["spans"], (TraceSpan("input", 100, 4),))
        self.assertEqual(r.buffered_frames, 0)
        self.assertEqual(r.write_cursor, 104)
        self.assertEqual(r.read_cursor, 104)

    def test_ring_wrap_does_not_rotate_channels(self):
        r = self.ring(capacity_frames=3)
        r.push(100, [[10, 11], [20, 21]])
        self.assertEqual(r.pull(100, 1)["planar_samples"], [[10], [20]])
        r.push(102, [[12, 13], [22, 23]])
        self.assertEqual(r.pull(101, 3)["planar_samples"], [[11, 12, 13], [21, 22, 23]])
        self.assertEqual(r.free_frames, 3)

    def test_chunk_partition_invariance(self):
        a = self.ring(capacity_frames=64)
        b = self.ring(capacity_frames=64)
        x = [[i/16 for i in range(40)], [-i/16 for i in range(40)]]
        a.push(100, x)
        whole = a.pull(100, 40)
        i = 0
        for chunk in (1, 3, 2, 7, 5, 10, 12):
            b.push(100+i, [p[i:i+chunk] for p in x])
            i += chunk
        self.assertEqual(i, 40)
        results = [[], []]
        at = 100
        for n in (3, 1, 8, 4, 10, 14):
            block = b.pull(at, n)
            at += n
            for j in range(2):
                results[j].extend(block["planar_samples"][j])
        self.assertEqual(at, 140)
        self.assertEqual(results, whole["planar_samples"])
        self.assertEqual(b.storage_latency_seconds, Fraction(0))

    def test_output_reject_underflow_is_atomic(self):
        r = self.ring()
        r.push(100, [[1, 2], [3, 4]])
        before = r.snapshot()
        with self.assertRaises(ValueError):
            r.pull(100, 3)
        self.assertEqual(r.snapshot(), before)
        self.assertEqual(r.pull(100, 2)["planar_samples"], [[1, 2], [3, 4]])

    def test_full_queue_overflow_reject_is_atomic(self):
        r = self.ring()
        r.push(100, [[1, 2, 3], [4, 5, 6]])
        before = r.snapshot()
        with self.assertRaises(ValueError):
            r.push(103, [[7, 8], [9, 10]])
        self.assertEqual(r.snapshot(), before)
        self.assertEqual(r.pull(100, 3)["planar_samples"], [[1, 2, 3], [4, 5, 6]])

    def test_overrun_drop_oldest_reports_gap_and_silence(self):
        r = self.ring(capacity_frames=4,overflow_policy="drop_oldest",underflow_policy="silence")
        r.push(100, [[1, 2, 3, 4],[11, 12, 13, 14]])
        p = r.push(104, [[5, 6],[15, 16]])
        self.assertEqual(p["dropped_oldest_frames"], 2)
        self.assertEqual(p["dropped_span"], (100, 102))
        self.assertEqual(r.pending_overrun_gap, 2)
        self.assertEqual(r.playable_frames, 0)
        out = r.pull(100, 6)
        self.assertEqual(out["planar_samples"], [[0, 0, 3, 4, 5, 6], [0, 0, 13, 14, 15, 16]])
        self.assertEqual(out["overrun_gap_frames"], 2)
        self.assertEqual(out["underrun_silence_frames"], 0)
        self.assertEqual(out["spans"], (TraceSpan("overrun_gap", 100, 2), TraceSpan("input", 102, 4)))
        self.assertEqual(r.total_dropped, 2)
        self.assertEqual(r.total_overrun_gap_silence, 2)
        self.assertEqual(r.total_underrun_silence, 0)

    def test_overrun_drop_oldest_can_be_rejected_at_consumer(self):
        r = self.ring(overflow_policy="drop_oldest")
        r.push(100, [[1, 2, 3, 4],[1, 2, 3, 4]])
        r.push(104, [[5],[5]])
        snapshot = r.snapshot()
        with self.assertRaises(ValueError):
            r.pull(100, 2)
        self.assertEqual(r.snapshot(), snapshot)
        # A layout/recovery policy change requires new epoch, not silent skipping.

    def test_underrun_fills_exact_number_of_frames(self):
        r = self.ring(underflow_policy="silence")
        r.push(100, [[1, 2],[10, 20]])
        block=r.pull(100, 4)
        self.assertEqual(block["planar_samples"], [[1, 2, 0, 0],[10, 20, 0, 0]])
        self.assertEqual(block["spans"], (TraceSpan("input",100,2),TraceSpan("underrun_silence",102,2)))
        self.assertEqual(block["underrun_silence_frames"],2)
        self.assertEqual(block["next_required_input_sample"],104)
        self.assertEqual((r.read_cursor,r.write_cursor,r.stored_start),(104,104,104))

    def test_empty_read_concealment_propagates_time(self):
        r = self.ring(underflow_policy="silence")
        x = r.pull(100, 3)
        self.assertEqual(x["planar_samples"], [[0,0,0],[0,0,0]])
        self.assertEqual(x["spans"], (TraceSpan("underrun_silence",100,3),))
        self.assertEqual(r.total_underrun_silence,3)
        r.push(103, [[9],[99]])
        self.assertEqual(r.pull(103, 1)["planar_samples"],[[9],[99]])

    def test_late_arrival_after_concealment_rejected(self):
        r = self.ring(underflow_policy="silence")
        r.pull(100,4)
        s=r.snapshot()
        for at in (100,101,103,105):
            with self.subTest(at=at):
                with self.assertRaises(ValueError):
                    r.push(at, [[1],[2]])
                self.assertEqual(r.snapshot(), s)
        r.push(104, [[1],[2]])

    def test_pending_gap_can_span_callbacks(self):
        r = self.ring(capacity_frames=3,overflow_policy="drop_oldest",underflow_policy="silence")
        r.push(100, [[1,2,3],[1,2,3]])
        r.push(103, [[4,5,6],[4,5,6]])
        self.assertEqual(r.pending_overrun_gap,3)
        part=r.pull(100,2)
        self.assertEqual(part["overrun_gap_frames"],2)
        self.assertEqual(r.pending_overrun_gap,1)
        self.assertEqual(r.pull(102,4)["planar_samples"],[[0,4,5,6],[0,4,5,6]])
        self.assertEqual(r.pending_overrun_gap,0)

    def test_mixed_overrun_gap_input_and_future_underrun(self):
        r=self.ring(capacity_frames=3,overflow_policy="drop_oldest",underflow_policy="silence")
        r.push(100, [[1,2,3],[10,20,30]])
        r.push(103, [[4],[40]])
        out=r.pull(100,6)
        self.assertEqual(out["planar_samples"],[[0,2,3,4,0,0],[0,20,30,40,0,0]])
        self.assertEqual(out["spans"],(TraceSpan("overrun_gap",100,1),TraceSpan("input",101,3),TraceSpan("underrun_silence",104,2)))
        self.assertEqual((r.stored_start,r.write_cursor,r.read_cursor),(106,106,106))
        r.push(106, [[7],[70]])

    def test_drop_oldest_only_drops_required_frames(self):
        r=self.ring(capacity_frames=5,overflow_policy="drop_oldest",underflow_policy="silence")
        r.push(100, [[0,1,2],[0,1,2]])
        self.assertEqual(r.push(103,[[3,4],[3,4]])["dropped_oldest_frames"],0)
        self.assertEqual(r.push(105,[[5,6],[5,6]])["dropped_oldest_frames"],2)
        self.assertEqual(r.total_dropped,2)
        self.assertEqual(r.pull(100,7)["planar_samples"],[[0,0,2,3,4,5,6]]*2)

    def test_bad_push_gaps_and_overlaps_atomic(self):
        r=self.ring()
        r.push(100,[[1],[2]])
        s=r.snapshot()
        for at in (99,100,102,300):
            with self.subTest(at=at):
                with self.assertRaises(ValueError):r.push(at,[[1],[2]])
                self.assertEqual(r.snapshot(),s)

    def test_bad_pull_gaps_and_overlaps_atomic(self):
        r=self.ring(underflow_policy="silence")
        s=r.snapshot()
        for at in (99,101,10**20):
            with self.subTest(at=at):
                with self.assertRaises(ValueError):r.pull(at,1)
                self.assertEqual(r.snapshot(),s)

    def test_wrong_channel_shapes_rejected(self):
        bad=[[],[[1]],[[1,2],[3]],[[1],[]],"bad",[[1],"bad"]]
        for x in bad:
            r=self.ring()
            with self.subTest(x=repr(x)):
                with self.assertRaises(ValueError):r.push(100,x)
                self.assertEqual(r.snapshot()["accepted_pushes"],0)

    def test_nonfinite_and_nonreal_inputs_are_rejected(self):
        bad=[math.nan,math.inf,-math.inf,complex(1),True,None,"1",10**400]
        for x in bad:
            r=self.ring()
            with self.subTest(x=repr(x)):
                with self.assertRaises(ValueError):r.push(100,[[x],[0]])
                self.assertEqual(r.snapshot()["accepted_pushes"],0)

    def test_accepts_over_reference_values_without_clamping(self):
        r=self.ring()
        r.push(100,[[2.5,-2.0],[-3.5,4.0]])
        self.assertEqual(r.pull(100,2)["planar_samples"],[[2.5,-2],[-3.5,4]])

    def test_preserves_signed_zero_values(self):
        r=self.ring()
        r.push(100,[[-0.0],[0.0]])
        v=r.pull(100,1)["planar_samples"]
        self.assertEqual(math.copysign(1,v[0][0]),-1)
        self.assertEqual(math.copysign(1,v[1][0]),1)

    def test_large_indices_exact_without_float_timestamps(self):
        origin=2**61+19
        r=self.ring(origin_sample=origin,rate_hz=Fraction(44100,1))
        r.push(origin,[[10,20],[0,0]])
        first=r.pull(origin,1)
        second=r.pull(origin+1,1)
        self.assertEqual(first["start_seconds_from_epoch"],Fraction(0))
        self.assertEqual(second["start_seconds_from_epoch"],Fraction(1,44100))
        self.assertEqual(second["end_sample_exclusive"],origin+2)

    def test_exact_rational_buffer_latency(self):
        r=self.ring(rate_hz=Fraction(48000*1000,1001))
        r.push(100,[[1,2],[3,4]])
        self.assertEqual(r.storage_latency_seconds,Fraction(2*1001,48000*1000))

    def test_epoch_reset_discards_old_without_data_leakage(self):
        r=self.ring()
        r.push(100,[[1,2],[3,4]])
        r.reset_epoch("next",0)
        self.assertEqual((r.buffered_frames,r.read_cursor,r.write_cursor),(0,0,0))
        r.push(0,[[7],[70]])
        self.assertEqual(r.pull(0,1)["planar_samples"],[[7],[70]])
        self.assertEqual(r.total_dropped,0)

    def test_reconfigured_epoch_changes_channel_count_and_rate(self):
        r=self.ring()
        r.reset_epoch("new",123,channels=1,capacity_frames=8,rate_hz=Fraction(96000))
        r.push(123,[[0.75]])
        self.assertEqual(r.pull(123,1)["planar_samples"],[[0.75]])
        self.assertEqual(r.rate_hz,96000)

    def test_reset_invalid_id_and_reuse_reject_atomically(self):
        r=self.ring()
        r.push(100,[[1],[1]])
        for ep in ("epoch0","",None,True):
            before=r.snapshot()
            with self.subTest(ep=ep):
                with self.assertRaises(ValueError):r.reset_epoch(ep,0)
                self.assertEqual(r.snapshot(),before)
        r.reset_epoch("new",10)
        with self.assertRaises(ValueError):r.reset_epoch("epoch0",5)
        with self.assertRaises(ValueError):r.reset_epoch("new",5)

    def test_reset_bad_configuration_is_atomic(self):
        r=self.ring()
        r.push(100,[[1],[1]])
        before=r.snapshot()
        for config in ({"capacity_frames":0},{"capacity_frames":257},{"channels":9},{"channels":True},{"rate_hz":48000},{"rate_hz":Fraction(1)},{"overflow_policy":"discard_newest"},{"underflow_policy":"loop"}):
            with self.subTest(config=config):
                with self.assertRaises(ValueError):r.reset_epoch("next",300,**config)
                self.assertEqual(r.snapshot(),before)
        r.reset_epoch("next",200)

    def test_policy_invalid_in_initial_config(self):
        for kw in ({"capacity_frames":0},{"capacity_frames":257},{"channels":0},{"channels":True},{"rate_hz":48000},{"rate_hz":Fraction(1000)},{"overflow_policy":"overwrite"},{"underflow_policy":"conceal"},{"origin_sample":-1},{"origin_sample":True},{"epoch_id":""}):
            with self.subTest(kwargs=kw):
                with self.assertRaises(ValueError):self.ring(**kw)

    def test_pull_bounds_validation(self):
        r=self.ring(underflow_policy="silence")
        for size in (0,-1,True,257,1.25,"4"):
            with self.subTest(size=size):
                with self.assertRaises(ValueError):r.pull(100,size)
                self.assertEqual(r.read_cursor,100)

    def test_push_bigger_than_capacity_fails_even_with_drop_policy(self):
        r=self.ring(capacity_frames=2,overflow_policy="drop_oldest")
        with self.assertRaises(ValueError):r.push(100,[[1,2,3],[4,5,6]])
        self.assertEqual(r.snapshot()["accepted_pushes"],0)

    def test_cannot_replay_already_consumed_coordinates(self):
        r=self.ring()
        r.push(100,[[1],[2]])
        r.pull(100,1)
        snap=r.snapshot()
        with self.assertRaises(ValueError):r.pull(100,1)
        with self.assertRaises(ValueError):r.push(100,[[1],[2]])
        self.assertEqual(r.snapshot(),snap)

    def test_source_count_plus_synthetic_equals_requested(self):
        r=self.ring(overflow_policy="drop_oldest",underflow_policy="silence")
        r.push(100,[[1,2,3,4],[1,2,3,4]])
        r.push(104,[[5,6],[5,6]])
        for start,count in ((100,1),(101,2),(103,4),(107,3)):
            v=r.pull(start,count)
            self.assertEqual(v["source_frames"]+v["synthetic_frames"],count)
            self.assertEqual(sum(x.frames for x in v["spans"]),count)
            self.assertEqual(sum(x.kind=="input" for x in v["spans"]),int(v["source_frames"]>0))

    def test_callback_size_can_exceed_ring_capacity_on_silence_policy(self):
        r=self.ring(capacity_frames=2,underflow_policy="silence")
        r.push(100,[[1,2],[3,4]])
        s=r.pull(100,7)
        self.assertEqual(s["planar_samples"],[[1,2,0,0,0,0,0],[3,4,0,0,0,0,0]])
        self.assertEqual(r.write_cursor,107)

    def test_zero_written_frames_not_permitted(self):
        r=self.ring()
        with self.assertRaises(ValueError):r.push(100,[[],[]])

    def test_short_float_finite_values_and_precise_alignment(self):
        r=self.ring(channels=1,capacity_frames=1)
        r.push(100,[[1e-300]])
        self.assertEqual(r.pull(100,1)["planar_samples"],[[1e-300]])

    def test_independent_deque_oracle_for_wrap_and_backpressure(self):
        """Separate simple FIFO model without modulo indexing for rejection policy."""
        rnd=random.Random(20261104)
        r=self.ring(capacity_frames=23,channels=1,origin_sample=0)
        oracle=deque()
        next_producer=0;next_consumer=0
        for _ in range(400):
            produce=not oracle or (rnd.random()<0.58)
            if produce:
                n=rnd.randint(1,4)
                if len(oracle)+n>23:
                    snap=r.snapshot()
                    with self.assertRaises(ValueError):r.push(next_producer,[[float(i) for i in range(next_producer,next_producer+n)]])
                    self.assertEqual(r.snapshot(),snap)
                else:
                    values=[float(i) for i in range(next_producer,next_producer+n)]
                    r.push(next_producer,[values]);oracle.extend(values);next_producer+=n
            else:
                n=rnd.randint(1,5)
                if n>len(oracle):
                    snap=r.snapshot()
                    with self.assertRaises(ValueError):r.pull(next_consumer,n)
                    self.assertEqual(r.snapshot(),snap)
                else:
                    expected=[oracle.popleft() for _ in range(n)]
                    received=r.pull(next_consumer,n)
                    self.assertEqual(received["planar_samples"],[expected])
                    next_consumer+=n
            self.assertEqual(r.buffered_frames,len(oracle))
            self.assertEqual(r.free_frames,23-len(oracle))
            self.assertEqual(r.read_cursor,next_consumer)
            self.assertEqual(r.write_cursor,next_producer)

    def test_independent_dictionary_oracle_for_drop_and_silence(self):
        """Index-keyed oracle independently chooses retains/drops; not ring math."""
        rnd=random.Random(20261104)
        r=self.ring(capacity_frames=9,channels=1,origin_sample=0,
                    overflow_policy="drop_oldest",underflow_policy="silence")
        kept={};producer=consumer=0
        for _ in range(200):
            if rnd.random()<0.60:
                n=rnd.randrange(1,7)
                values=[float(i+1) for i in range(producer,producer+n)]
                r.push(producer,[values])
                for at,v in enumerate(values,producer):kept[at]=v
                producer+=n
                # Exactly the nine newest unconsumed producer positions retained.
                for k in sorted(kept)[:-9]:del kept[k]
            else:
                n=rnd.randrange(1,8)
                out=r.pull(consumer,n)
                expected=[kept.get(i,0.) for i in range(consumer,consumer+n)]
                self.assertEqual(out["planar_samples"],[expected])
                for at in range(consumer,consumer+n):kept.pop(at,None)
                consumer+=n
                if consumer>producer:producer=consumer
            self.assertEqual(r.read_cursor,consumer)
            self.assertEqual(r.write_cursor,producer)
            self.assertEqual(r.buffered_frames,len(kept))


if __name__ == "__main__":
    unittest.main()
