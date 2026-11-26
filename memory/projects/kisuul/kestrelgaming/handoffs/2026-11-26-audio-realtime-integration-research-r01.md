---
schema: 1
id: 2026-11-26-audio-realtime-integration-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch a435c790546b7aefc8ba35ba18be1d7c235f916f; PortAudio v19 callback and timing documentation; JACK ring buffer reference; executed deadline and bounded-queue schedule checks."
---

# Skill 72 research for real-time integration

## Summary

**Task outcome:** COMPLETE

Keep the audio path within its host deadlines. Carry
timed analysis records through a bounded handoff
and report dropped coverage at its source coordinates.
Average callback cost can hide a missed deadline.
A full analysis queue can lose coverage while the
source clock continues to advance.
[PortAudio stream callback contract](https://portaudio.com/docs/v19-doxydocs/portaudio_8h.html)

## Evidence

### Account for deadline and support

For a rate $f_s$ and callback frame count $N$, use
$N/f_s$ as the nominal time represented by the block.
Determine actual deadline margin from the host
contract and observed scheduling, buffer adaptation
and device state. Test the supported frame sizes,
including variable sizes and the smallest period.
Record duration distributions, worst observed time,
and deadline misses under workload. Record host
underflow or overflow events and affected audio
support where the API supplies that evidence.
[PortAudio stream callback and status flags](https://portaudio.com/docs/v19-doxydocs/portaudio_8h.html)

Preallocate and bound work on the callback path.
Move work with unpredictable duration, such as file
output, UI updates or unbounded analysis, to another
thread. The callback needs a defined output action
even when the analysis consumer stalls. Use bounded
record storage and a tested ownership and publication
protocol. A single-producer, single-consumer queue
assumes one thread in each role, as in the JACK ring
buffer interface. Reserve space for a complete bounded
record, publish initialized data, and reclaim it after
the consumer completes its read. Choose capacity for
the supported block sizes and backlog.
[PortAudio callback constraints](https://portaudio.com/docs/v19-doxydocs/writing_a_callback.html) ·
[JACK ring buffer contract](https://jackaudio.org/api/ringbuffer_8h.html)

Each analysis record needs an epoch, tap, source sample
range, and validity. Record source time and analysis
availability on declared clocks. Define the full-queue
policy and advance the source range for every observed
block. Leave gaps visible. Keep a consistent source
watermark or loss report so a dropped final block is
observable even without a later delivered record.
Qualify callback timing, host audio loss, analysis
loss and analysis delivery latency with their own
measurements.
[Timebase](../../../../../skills/audio-timebase-sync/references/TIMEBASE_CONTRACT.md) ·
[Dropout and coverage](2026-11-26-audio-dropout-detection-research-r01.md) ·
[Loopback latency](2026-11-26-audio-loopback-latency-research-r01.md)

### Executed checks and portable fixtures

In an ideal schedule model at 48 kHz, nominal periods
for 64, 128 and 256 frames are $4/3$, $8/3$ and $16/3$
ms. At 64 frames, use costs `[0.9,0.9,1.8]` ms with
zero start delay and the nominal period as the deadline.
The mean is 1.2 ms. The last callback misses its
deadline by $7/15$ ms, about 0.467 ms. The same cost
of 1.8 ms fits the nominal 128-frame period.

In a second model, use capacity for two unread records,
with room for the largest block in each record. Drop
the newest analysis record when both slots are full.
The producer advances one tick per frame regardless of
analysis delivery.

| Action | Verified result |
| --- | --- |
| Produce blocks of 96, 48, then 96 frames from tick 0. | Queue `[0,96)` and `[96,144)`. Drop `[144,240)`. |
| Consume one record, produce a 48-frame block, then drain the queue. | Receive `[0,96)` first. The drain gives `[96,144)` then `[240,288)`. |
| Produce and consume a final 48-frame block. | Receive `[288,336)`. The analysis has one 96-frame gap and coverage $240/336=5/7$. |

The schedule checks use ideal timing and queue ownership.
They verify accounting on supplied events. Timing and
correctness on a target host require measurement under
actual scheduling and concurrent load.

## Next action

Give Gauge deadline and queue traces with variable block
sizes, a stalled consumer, a drop at stream end, and
epoch changes. Measure real callback timing under the
intended workload. Verify delivery bounds and gap
semantics independently of host audio xrun reports.

## Revisit when

The host API, block negotiation, sample rate, buffer
capacity, concurrency protocol, or timing target changes.
