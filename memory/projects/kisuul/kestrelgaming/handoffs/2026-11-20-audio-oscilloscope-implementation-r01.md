---
schema: 1
id: 2026-11-20-audio-oscilloscope-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: Kestrel
created: 2026-11-20
updated: 2026-11-20
sources: "Owner requested Skill #28 after prep. Audio development base f9094d66f387ec5c689bc294138dfae37c347dfe includes Skill #27. Research PR #29 at e2e622d9644dad922a079653b9301826f73c4919. Focused regression tests and deliberate-fault checks executed on the implementation."
---

# Skill #28 oscilloscope implementation and review

## Summary

**Task outcome:** COMPLETE

The skill and offline reference are ready for review. Capture advances on
the sample clock. Display projection preserves recorded extrema from
each channel. Skill #29 owns trigger selection and pending capture.
[Skill](../../../../../skills/audio-oscilloscope/SKILL.md) ·
[Contract](../../../../../skills/audio-oscilloscope/references/OSCILLOSCOPE_CONTRACT.md) ·
[Curriculum PR #2](https://github.com/Kisuul/KestrelGaming/pull/2)

## Evidence

- All 29 focused tests passed. They include a block longer than retained
  history, atomic rejection of a late NaN, reset with reused coordinates,
  initial and later wrap, integer bounds above $2^{53}$, antiphase, and
  a transient that stride sampling misses.
  [Fixtures](../../../../../tests/fixtures/AUDIO_OSCILLOSCOPE_GOLDENS.md) ·
  [Tests](../../../../../tests/test_audio_oscilloscope_reference.py)
- Direct tape slices matched the reference across 8,192 partition replays.
  A position-based oracle matched the bucket projection for 8,256
  length/width pairs and 707,264 sample assignments. Temporary deliberate
  faults in window scheduling, final-sample validation, pixel rounding,
  ties, and epoch checks each failed the corresponding test.
  [Research handoff](https://github.com/Kisuul/KestrelGaming/blob/e2e622d9644dad922a079653b9301826f73c4919/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-20-audio-oscilloscope-research-r01.md)

## Next action

Review the exact child PR head. Replay the oversized block, gap and retry,
and projection cases with separate oracles. Record the agent's decisions
on the proposed review tasks. Count Skill #28 after owner acceptance.
[Curriculum acceptance gate](../2026-11-04-audio-curriculum-full-completion-gate-r01.md)

## Revisit when

The capture tap, channel layout, clock, retention policy, or projection
semantics change, or a trigger uses an explicit retained span.
