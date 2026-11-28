---
schema: 1
id: 2026-11-27-audio-dropout-detection-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: Kestrel
created: 2026-11-27
updated: 2026-11-27
sources: "Audio branch at 52cb9fac1dd5d19ee61626adffd6286ba73742b4, Skill 50 research from merged PR #55, and executed coverage, playout, partition, and quiet-window checks."
---

# Dropout detection skill #50 implementation and review

## Summary

**Task outcome:** COMPLETE

The reference audits source coordinates, explicit playout
provenance, and channel-specific quiet intervals. An early
start reports the actual accepted overlap. A forward jump
stays provisional until the caller confirms the gap.
The quiet profile qualifies an event at the first frontier
with complete adjacent active context.
[Skill](../../../../../skills/audio-dropout-detection/SKILL.md) ·
[Contract](../../../../../skills/audio-dropout-detection/references/DROPOUT_DETECTION_CONTRACT.md) ·
[Research](2026-11-26-audio-dropout-detection-research-r01.md)

## Evidence

- The 28 focused tests cover gap confirmation, partial overlap,
  exact indices, zero and repeat concealment, thresholds,
  readiness, and incomplete runs. The quiet timing fixture
  matches all 4,096 partitions across two origins.
  [Fixture values](../../../../../tests/fixtures/AUDIO_DROPOUT_DETECTION_GOLDENS.md) ·
  [Executable checks](../../../../../tests/test_audio_dropout_detection_reference.py)
- An independent scan matched 512 PCM records, 1,536 callback
  partitions and 11,136 callbacks. It used rational window
  powers to check 527 qualified and 2,222 incomplete baseline
  observations. It also checked 16,384 source offers and 512
  playout partitions against integer frame membership.
- The zero-fill and repeated-period fixtures produce the same
  PCM as genuine input at the same output coordinates. Their
  provenance gives different counts of original source frames.
- In the stereo quiet-window fixture only the left channel
  qualifies. Its quiet span is $[1004,1008)$ and the required
  exclusive frontier is 1012.

## Next action

Check the three-frame early offset with one frame of overlap.
Compare a provisional hole recovered in source order with a
confirmed loss that missed playout. Check the identical PCM
fixtures against their source and playout records. End the
quiet-window capture at 1011 and then at 1012 to verify the
difference in available context.

## Revisit when

The capture tap, device clock, delivery cutoff, replacement
policy, or waveform profile changes.
