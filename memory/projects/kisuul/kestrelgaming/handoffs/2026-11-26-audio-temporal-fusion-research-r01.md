---
schema: 1
id: 2026-11-26-audio-temporal-fusion-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 327ca13df3cef9193599762685f1350ae4df6900; Kestrel sample clocks, resampling and provenance; Akidau et al. (2015) time domains and watermarks; PortAudio callback time contract; executed rational timing and grouping checks below."
---

# Skill 43 research for temporal fusion

## Summary

**Task outcome:** COMPLETE

Put temporal observations on a known common clock. Preserve when
each event is estimated to occur, which input supports it, the first
time that input is ready, and when the decision is emitted. Fuse
only compatible estimates of the same quantity. Keep related but
different events, such as a beat prediction and a measured onset,
available as context. Use a bounded join to teach disagreement,
late data, and causality before choosing a probabilistic model.
[Onset research](2026-11-21-audio-onset-detection-research-r01.md) ·
[Beat research](2026-11-21-audio-beat-tracking-research-r01.md) ·
[Segmentation research](2026-11-26-audio-event-segmentation-research-r01.md)

## Evidence

### Map the coordinates

Each contributor needs a source ID, tap, event class, epoch,
rate, original half-open input supports, event position, minimum
input readiness and revision status. Preserve a separate
processing or dispatch timestamp in its own clock domain.
Record whether the contributor is an observation, an estimate,
or a prediction. A prediction can carry a future event position
with evidence available now.

For locked clocks within a valid mapping interval, transform a
source coordinate $u$ to master coordinate $a u+b$ using the
known rate ratio and origins. Here $a$ is in master samples per
source sample, and $b$ is in master samples. Use exact rational
coordinates and keep the native interval. Rate conversion,
measured alignment, and filter lookahead each need named support.
A resampler can preserve nominal time and still need future
samples. Independent devices need measured anchors, a drift
model when required, and mapping uncertainty. On a discontinuity,
close the affected association state. Connect results across
epochs only when explicitly supported by a valid mapping and
the task permits it.
[Timebase](../../../../../skills/audio-timebase-sync/references/TIMEBASE_CONTRACT.md) ·
[Resampling timing](../../../../../skills/audio-resampling/references/RESAMPLING_CONTRACT.md#explicit-filter-and-delay)

Audio callback time and playback time describe different events.
PortAudio has separate ADC, callback and DAC fields for a stream.
Choose the anchor by its meaning and validate the clock connection
before turning a sample coordinate into a display or wall-clock
timestamp. Carry mappings and revision IDs with the output.
[PortAudio time fields](https://portaudio.com/docs/v19-doxydocs/structPaStreamCallbackTimeInfo.html) ·
[Kestrel provenance contract](../../../../../skills/audio-analysis-provenance/references/PROVENANCE_CONTRACT.md)

### Associate and combine

Declare a compatibility rule first. A peak in onset strength
and a measured envelope attack may estimate one event under a
particular definition. A beat or a segment cut can coincide with
that event and still represent a different quantity. Check tap,
epoch and ranges as well as event class. Use a named gating
tolerance in shared samples or seconds and account for mapping
error and method bias before calling estimates contradictory.

A simple offline baseline sorts mapped candidates by event
time and a stable tie key. Within each compatible run, start a
group at the earliest eligible candidate. For this baseline
admit other estimates within a maximum span of the group's
start and use each source at most once per group. Expose excluded
and competing candidates. Test alternative pairings when close
events compete. Successive pairwise proximity can chain events
beyond the intended gate. Keep contributor positions, weights,
and residuals, whichever representative you choose. An
explicit preferred source, weighted median or weighted mean all
need a stated rationale for the measurement. Preserve source
support as a union of intervals, including holes.

Combining several estimates from one capture often shares errors.
For two unbiased estimates with unit variance and correlation
$\rho$, the variance of their equally weighted mean is
$(1+\rho)/2$. Report correlation assumptions if making a
confidence or uncertainty claim. For a first reference, record
disagreement, coverage and data dependencies and leave
statistical confidence uncalibrated.

### Separate readiness and commitment

On the shared input clock the earliest data-readiness bound is
the maximum readiness over used evidence and any closure or
lookahead required by the decision. The observed dispatch
timestamp also includes queueing, computation or block
scheduling. Retain both. A late source may supply a better
historical label after the first decision, so issue revisions
according to the consumer's policy and preserve the earlier
dispatch record.

For online use, define a per-source frontier $W_i$ as a guarantee
that it will emit no additional eligible event earlier than
$W_i$ in that epoch. A complete group whose inclusive upper
event-time edge is $g$ can be closed by the frontier rule when
$g<\min_i W_i$ for all required sources. Define source finalization,
unavailable states, and the response to a broken guarantee.
With estimated frontiers or a wall-time deadline, mark the
decision provisional or partial as appropriate. Late data needs
an explicit discard or revision policy. A gap reports missing
coverage, while an observed quiet interval can provide evidence
about absence.
[Akidau et al. (2015), event time and watermarks](https://research.google.com/pubs/archive/43864.pdf) ·
[Stream-buffering contract](../../../../../skills/audio-stream-buffering/references/STREAM_BUFFER_CONTRACT.md)

### Executed checks and portable fixtures

| Probe | Verified result |
| --- | --- |
| The master is 48 kHz. A locked 44.1 kHz source has zero mapped to master origin $O=2^{60}+37$. Map source positions 1,470 and 1,470.5. | The master positions are $O+1600$ and $O+235280/147$. Keep fractional parts until a declared rounding boundary. |
| Compatible candidates from distinct sources have times 0, 9 and 18 samples, with a span limit of 10. Supply them in the arrival order 18, 0, 9. | In time order the earliest-anchor rule groups `[0,9]` and `[18]`. A neighbor chain would incorrectly cover 18 samples under this limit. |
| Two compatible onset estimates at 4,800 and 4,848 samples have weights 2 and 1. Their data are ready at exclusive input boundaries 5,280 and 5,520 on the same 48 kHz clock. | The weighted label is 4,816. The data used in the estimate are ready at 5,520, at least $44/3$ ms after that label before any required closure or processing. |
| The inclusive upper event-time edge is 4,848. Required source frontiers are 4,900 and 4,848. Increase the second to 4,850. | The first pair leaves the group open because an eligible event at 4,848 can still arrive. The second pair clears the edge. |
| Two unit-variance estimates have correlation 0.9. Combine them with equal weights. | The variance of the mean is $19/20$. With independent errors it would be $1/2$. |

The mapping, weighted estimate and variance checks used exact
rational arithmetic. The grouping and frontier checks used
ordered synthetic events. They do not measure device drift,
observed dispatch latency, or a learned confidence model.

## Next action

Implement a deterministic join on one mapped sample clock and
record contributor, support, and decision provenance. Replay
reordered messages, a gap, equal-prefix streams, late revisions
and conflicting tap offsets. Compare results under different
callback partitions. Verify delay at a real output if the
application makes a live delivery claim.

## Revisit when

The clock mapping, alignment budget, contributor semantics,
association policy, or consumer commitment rules change.
