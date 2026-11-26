---
schema: 1
id: 2026-11-26-audio-dropout-detection-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; Kestrel timebase and stream buffering; PortAudio callback status, W3C WebRTC statistics, RFC 6716; executed exact-coverage and concealment fixtures below."
---

# Skill 50 research for dropout detection

## Summary

**Task outcome:** COMPLETE

Use source timing and coverage evidence first. An unexpected
quiet interval in PCM can support a candidate dropout, and
also has other explanations. A dropped interval filled by
concealment remains a loss event even when the output has
continuous coordinates or nonzero samples. The fixtures
include identical PCM with two different source histories.
[Kestrel stream buffering](../../../../../skills/audio-stream-buffering/SKILL.md)

## Evidence

### Account for what the source supplied

For every block record the tap, clock, epoch, start, frame
count, channel set, status, and provenance. On a verified
common source clock, expect consecutive half-open intervals.
If the next start is greater than the expected end, the
missing span is `[expected_end, next_start)`. If the next
start is earlier, record overlap or reordering and inspect
delivery order. Treat a seek, device switch or rate change
as a discontinuity. Retain the original coordinates when
applying a recovery policy.
[Sample clocks and epochs](../../../../../skills/audio-timebase-sync/references/TIMEBASE_CONTRACT.md) ·
[Temporal fusion timing](2026-11-26-audio-temporal-fusion-research-r01.md)

Track the source loss, the playout result and the replacement
method. An underrun can present explicit silent samples.
Concealment can also estimate a waveform from surrounding
state. Use sample frame count for duration, even in stereo.
Keep per-channel waveform anomalies separate from a missing
frame shared across channels. Missing PCM, observed zero PCM,
and synthetic zero PCM have different evidence.
[Kestrel stream buffer spans](../../../../../skills/audio-stream-buffering/references/STREAM_BUFFER_CONTRACT.md) ·
[Opus PLC, RFC 6716 §4.4](https://www.rfc-editor.org/rfc/rfc6716.html#section-4.4)

PortAudio's input overflow flag reports a discard with
semantics that depend on the buffer setting. The flag by
itself does not give the exact count of lost frames. WebRTC
statistics expose counters for concealed samples, silent
concealed samples and concealment events. Counter differences
can corroborate loss during a polling interval. Exact event
placement needs timestamps, sequence or sample provenance
associated with the affected stream.
[PortAudio callback flags](https://files.portaudio.com/docs/v19-doxydocs/portaudio_8h.html) ·
[W3C WebRTC statistics](https://www.w3.org/TR/webrtc-stats/)

### Inspect PCM when provenance is limited

Define the sample-clocked detector profile, including the
quiet statistic, band, expected active level, minimum quiet
duration, edge hysteresis, and required pre/post context.
For example, find a short run where band-limited RMS is
well below both neighboring active regions. Return its
candidate span, support and score. Inspect abrupt edges,
continuing activity on other channels, and the alignment
to a reference when one exists. Speech pauses, gating,
intentional mutes, fades, edit boundaries and sustained
quiet tones can have similar values. Repeated nonzero audio
also needs corroboration before labeling it as concealment.

An energy decision using post-event context cannot be ready
until that context is acquired. Keep frame readiness and
any confirmation delay on the correct clock. Preserve
incomplete candidates at the capture end or across a gap.
Use a separate validated policy for timestamp resets and
packet reordering.
[Envelope dynamics](../../../../../skills/audio-envelope-dynamics/SKILL.md) ·
[Event segmentation timing](2026-11-26-audio-event-segmentation-research-r01.md)

### Executed checks and portable fixtures

| Probe | Verified result |
| --- | --- |
| At 48 kHz, observe a block at 1,000 with four frames of 0.5 and a block at 1,008 with four frames of 0.5 on the same verified source clock. | Source support is missing on `[1004,1008)`, four frames or about 83.333 µs. |
| Observe the same two outer blocks with four acquired zero frames at 1,004. Compare to a reconstruction of the missing case filled with zeros. | The two delivered PCM arrays are sample-identical. The first has continuous observed support. The reconstruction needs missing/inserted provenance on `[1004,1008)`. |
| After observing `[1000,1004)`, receive the coordinate range `[1002,1004)` again, then receive `[1004,1008)`. | The repeated range is an overlap. It does not create a missing span. |

The checks use exact synthetic frame ranges and a sample
comparison. They establish what the two histories permit the
detector to infer. Tuning an audio-content detector or measuring
actual driver and network loss needs additional captures.

## Next action

Implement explicit coverage classification before adding
content heuristics. Test gap, overlap, zero fill, repeat
concealment, intentional silence, different block partitions,
and a clock reset. Report measured source loss separately from
the playout effect and candidate waveform evidence.

## Revisit when

The source clock, buffer or concealment policy, evidence
counters, waveform threshold or event definition changes.
