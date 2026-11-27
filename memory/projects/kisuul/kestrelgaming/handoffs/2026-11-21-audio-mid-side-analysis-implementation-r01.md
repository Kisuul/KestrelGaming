---
schema: 1
id: 2026-11-21-audio-mid-side-analysis-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: archived
evidence: observed
author: Kestrel
created: 2026-11-21
updated: 2026-11-26
sources: "Owner requested Skill #32. Audio development base a2323f1c8f8bba04c3ae7d6bea2be72a9d024230. Research PR #40 at 8c9bfc28e0dcfe285e5996ad9bddb97ba476d225. Stereo correlation comparison used PR #41 at 8794831ad1805a536ddd9e68e868750327e5e37b. Local tests, differential checks, and deliberate-fault checks executed. Gauge reviewed 12b1bc4a4cd34b84c3ad1897f1b356299b0389a4. PR #42 merged at f61899c9b2ece1c831ad424aee34cb08a4cfb62c."
---

# Skill #32 Mid/Side analysis implementation and review

## Summary

**Task outcome:** COMPLETE

Gauge gave a technical GO on `12b1bc4`. Skill #32 merged
in PR #42 at `f61899c`.
[Gauge review](https://github.com/Kisuul/KestrelGaming/pull/42#pullrequestreview-6007309442) · [Merged PR #42](https://github.com/Kisuul/KestrelGaming/pull/42)

The skill measures half-sum Mid and half-difference Side on the shared
PCM capture. It derives exact powers from the component samples and
reports binary64 RMS with separate exact-zero and underflow states.
The contract covers gain, headroom, delivered mono, and band cancellation.
[Skill](../../../../../skills/audio-mid-side-analysis/SKILL.md) ·
[Contract](../../../../../skills/audio-mid-side-analysis/references/MID_SIDE_ANALYSIS_CONTRACT.md) ·
[Research](https://github.com/Kisuul/KestrelGaming/blob/8c9bfc28e0dcfe285e5996ad9bddb97ba476d225/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-21-audio-mid-side-analysis-research-r01.md)

## Evidence

- All 24 focused tests and 29 adjacent capture tests passed locally.
  The fixtures include 5,929 signed gain cases, 128 callback partitions,
  finite binary64 endpoints, integer FLAC parity, the two-tone band
  comparison, and the change in delivered mono after clipping or delay.
  [Fixtures](../../../../../tests/fixtures/AUDIO_MID_SIDE_ANALYSIS_GOLDENS.md) ·
  [Tests](../../../../../tests/test_audio_mid_side_analysis_reference.py)
- Seed `3220261121` covered 408 windows, 9,604 pairs, and 816 RMS
  rounding cells. Mid power and RMS matched Skill #31's equal-weight
  mono on the pinned candidate. Exact Side fraction complemented mono
  retention. The direct and correlation forms also agreed for all
  86 equal-power windows.
  [Skill #31 candidate](https://github.com/Kisuul/KestrelGaming/pull/41/commits/8794831ad1805a536ddd9e68e868750327e5e37b)
- Six deliberate faults failed their targeted tests. FFmpeg 7.1.5 matched
  the reference encode, decode, and doubled-Side decode on seven pairs.

## Next action

Use the [current curriculum ledger](2026-11-17-audio-curriculum-status-r01.md) for the next module.

### Review plan at submission

Review the exact PR head and run the fixture review tasks. Record the
observed decisions and count Skill #32 after owner acceptance.
[Owner completion gate](../2026-11-04-audio-curriculum-full-completion-gate-r01.md)

## Revisit when

The channel convention, capture representation, rounding policy, or
delivery matrix changes.
