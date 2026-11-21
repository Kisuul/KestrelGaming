---
schema: 1
id: 2026-11-20-audio-oscilloscope-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-20
updated: 2026-11-20
sources: "Tektronix acquisition modes, W3C Web Audio waveform/downmix rules, BBC audiowaveform, and a bucket-versus-stride check. Audio curriculum PR #2 at 4dc854e450bac96ec985c7ab226941cc8efe13c9. VeNerVRA audio engineering research brief, revised 2026-11-20."
---

# Oscilloscope waveform capture research

## Summary

Planned skill #28 · `audio-oscilloscope`

**Task outcome:** COMPLETE

Capture exact, aligned PCM intervals and preserve transient extrema when projecting many
samples to a few pixels. Give the agent a way to localize faults to the tap, capture
timeline or projection.

## Evidence

**Trace what the display can claim.** For a spike, channel mismatch, or waveform timing
issue, establish the PCM capture path before looking at pixels. Tektronix describes sample
and peak-detection acquisition modes. BBC audiowaveform provides a min/max example.
AnalyserNode time-domain output uses the latest samples after a mono downmix. A
sample-clocked stereo scope needs separately observable channels and a capture cursor.
[Tektronix acquisition modes](https://www.tek.com/en/documents/primer/oscilloscope-systems-and-controls)
· [BBC audiowaveform](https://github.com/bbc/audiowaveform) ·
[W3C Web Audio §1.8.3–5](https://www.w3.org/TR/webaudio/#AnalyserNode)

**First reference.** Capture complete windows $[s,s+L)$ on a declared sample hop. Carry tap,
units, rate, channels, epoch and exact sample bounds. Align all channels to the same
interval. Preserve signed peaks above nominal full-scale when the tap permits them. State
prehistory, gap, and epoch-reset behavior. Reject a malformed block before changing the
cursor or sample history. Size retained history for the supported capture windows, including
pretrigger and pending captures when used by
[scope triggering](2026-11-20-audio-scope-triggering-research-r01.md). The renderer can
skip a presentation update while sample ingestion continues.

**Map samples to pixels.** For $1\le W\le L$, bucket $j$ owns
$[\lfloor jL/W\rfloor,\lfloor(j+1)L/W\rfloor)$ relative to the window start. Return min/max
values and their support intervals. An optional extremum index needs a deterministic tie
rule. The envelope retains both extrema and leaves ordering within each bucket unspecified.
If $W>L$, use measured sample positions. Any connecting line is a display interpolation. If
a consumer needs a new, lower-rate waveform for analysis, define its filter, timing and
sample-rate contract separately from the pixel envelope.

**Find where a spike was lost.** Put +1 and −0.75 at indices 119 and 123 of an otherwise
zero 256-sample window. At 16 buckets, bucket 7 owns [112, 128) and should retain both
extrema. Selecting every 16th sample reports zeros throughout. If the raw capture passes and
the display fails only at certain widths, inspect the bucket partition and projection. If
the raw capture misses the pulse, inspect the tap, capture support and cursor first.

Test nondivisible partitions. For $L=11,W=3$, expect [0, 3), [3, 7), [7, 11). Exercise
first and last samples, equal extrema, independent channels, ring wrap, late invalid
samples, gaps, and long-running clocks. Replay the same samples with different callback
partitions and compare exact outputs. Measure render cadence and latency on the target
system when those properties are part of the requirement.

Use the [audio timebase](../../../../../skills/audio-timebase-sync/SKILL.md) rules for exact
sample positions and the
[stream buffering](../../../../../skills/audio-stream-buffering/SKILL.md) guidance for
retention and cursor ownership.

### Reproducible checks

| Check | Reproduction method | Recorded result |
| --- | --- | --- |
| Capture extrema | Use the 256-sample two-impulse fixture above. Compare the min/max of each bucket to a stride-16 pick of samples at indices 0, 16, 32 and so on. | Bucket 7 retained both extrema [−0.75, 1]. Stride 16 missed both. |

The reference contract and acceptance cases are proposed. The recorded checks concern the
listed numerical fixtures.

## Next action

Verify capture support before testing pixels. Give the agent a scope that loses impulses at
selected display widths. Compare raw samples, bucket ownership and extrema across widths and
callback partitions. Fix the sample-origin and channel rules before extending the capture to
stereo displays or trigger mode.

## Revisit when

The target changes its capture tap, channel map, retention budget, renderer, or
dropped-input policy.
