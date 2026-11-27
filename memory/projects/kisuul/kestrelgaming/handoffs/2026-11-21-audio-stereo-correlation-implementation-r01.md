---
schema: 1
id: 2026-11-21-audio-stereo-correlation-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: archived
evidence: observed
author: Kestrel
created: 2026-11-21
updated: 2026-11-26
sources: "Owner requested Skill #31 after prep. Audio development base a2323f1c8f8bba04c3ae7d6bea2be72a9d024230. Research PR #39 at e8cb75637f5e85d6fcedcbe61e1b5c256b2088f0. Focused tests and exact rounding-cell checks on seed 3120261121. Gauge reviewed 8794831ad1805a536ddd9e68e868750327e5e37b. PR #41 merged at 592c96b0cdfa45b0b78f05ec1866314fecd55f74."
---

# Skill #31 stereo correlation implementation and review

## Summary

**Task outcome:** COMPLETE

Gauge gave a technical GO on `8794831`. Skill #31 merged
in PR #41 at `592c96b`.
[Gauge review](https://github.com/Kisuul/KestrelGaming/pull/41#pullrequestreview-6007262903) · [Merged PR #41](https://github.com/Kisuul/KestrelGaming/pull/41)

The skill and bounded offline reference are ready for independent
review. Measure the raw coefficient and channel levels on the same
capture. Check the equal-weight mono retention and the actual delivery
path when diagnosing cancellation.
[Skill](../../../../../skills/audio-stereo-correlation/SKILL.md) ·
[Contract](../../../../../skills/audio-stereo-correlation/references/STEREO_CORRELATION_CONTRACT.md)

## Evidence

- All 24 focused tests and 29 shared capture tests passed. The focused
  suite compares all 128 callback partitions of the short tape. It
  exercises exact zero, signed underflow, endpoint rounding, gain and
  DC effects, and mono cancellation despite a positive coefficient.
  [Fixtures](../../../../../tests/fixtures/AUDIO_STEREO_CORRELATION_GOLDENS.md) ·
  [Tests](../../../../../tests/test_audio_stereo_correlation_reference.py)
- An exact neighboring-float oracle checked 2,597 rounded results
  across 650 windows and 20,218 stereo pairs. The cross moment also
  matched an independent calculation from the difference of the sum
  and difference powers. Six deliberate faults reproduced test
  failures for sign, product rounding, mono underflow, and root
  boundaries.
  [Research handoff](https://github.com/Kisuul/KestrelGaming/blob/e8cb75637f5e85d6fcedcbe61e1b5c256b2088f0/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-21-audio-stereo-correlation-research-r01.md)

## Next action

Use the [current curriculum ledger](2026-11-17-audio-curriculum-status-r01.md) for the next module.

### Review plan at submission

Review the submitted head. Check the tiny cross-product, the subnormal
RMS midpoint, and the +0.8 coefficient on the two-tone cancellation
case. Record the agent's decisions in the prepared use trials. Count
Skill #31 after owner acceptance.
[Curriculum acceptance gate](../2026-11-04-audio-curriculum-full-completion-gate-r01.md)

## Revisit when

The capture, estimator, output representation, window, or delivery
fold-down changes.
