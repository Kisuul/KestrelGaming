---
schema: 1
id: 2026-11-20-audio-spectral-descriptors-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: Kestrel
created: 2026-11-20
updated: 2026-11-20
sources: "Owner requested the next skill after reviewing PR #29. Audio development base 4dc854e450bac96ec985c7ab226941cc8efe13c9. VeNerVRA handoff at e2e622d9644dad922a079653b9301826f73c4919. CPython 3.12.14 focused tests and independent Decimal comparison, seed 50251120."
---

# Skill #25 spectral descriptors implementation and review

## Summary

**Task outcome:** COMPLETE

The implementation is ready for independent review. Owner acceptance is
pending. The curriculum count is 24 of 73 accepted.
[Audio curriculum PR #2](https://github.com/Kisuul/KestrelGaming/pull/2)

The skill teaches power-weighted shape and flux from a calibrated PSD frame.
The bounded reference takes one channel and one analysis profile. It preserves
the source clock and the exact frame support. Read the
[skill](../../../../../skills/audio-spectral-descriptors/SKILL.md) and
[measurement contract](../../../../../skills/audio-spectral-descriptors/references/SPECTRAL_DESCRIPTORS_CONTRACT.md).

## Evidence

- The reference uses discrete bin centers and keeps full one-sided endpoint
  power. The explicit terminal Nyquist option applies to even transforms.
  Tests use the upstream PSD reference with odd and even lengths, windowing,
  padding, and mean removal. An integration test uses one original profile
  from the multiresolution analyzer. [Research handoff](https://github.com/Kisuul/KestrelGaming/blob/e2e622d9644dad922a079653b9301826f73c4919/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-20-audio-spectral-descriptors-research-r01.md)
- Rolloff uses exact cumulative weights and rational thresholds. The 85% and
  95% tie regressions check the smaller crossing index. Logs of the original
  ordinates preserve representable flatness. A separate fixture sums entropy
  contributions that each round to zero. Flux requires exact sample adjacency
  and matching clock, epoch, and measurement metadata. The maintained tests
  cover these cases. [Frozen fixtures](../../../../../tests/fixtures/AUDIO_SPECTRAL_DESCRIPTORS_GOLDENS.md)
- The focused suite passed all 32 tests under CPython 3.12.14. Run
  `python3 -m unittest discover -s tests -p test_audio_spectral_descriptors_reference.py -v`.
  An additional local comparison used 580-digit Decimal arithmetic and exact
  rolloff fractions for 144 generated frames. It checked 1,200 metric values.
  The largest relative error among normal results was about $1.48\times10^{-13}$.
  This probe used seed 50251120. The maintained suite includes its own smaller
  seeded Decimal fixture. [Test module](../../../../../tests/test_audio_spectral_descriptors_reference.py)

## Next action

Review the exact child PR head. Try to falsify the tie rule, the difference
between zero and underflow, the window provenance, and the gap recovery path.
Use the agent tasks in the fixture document to evaluate routing and engineering
decisions. Record the owner's acceptance before counting Skill #25.
[Curriculum acceptance gate](../2026-11-04-audio-curriculum-full-completion-gate-r01.md)

## Revisit when

The band rule, PSD calibration, supported numeric range, flux continuity rules,
or analysis profile changes. A continuous-cell estimator and a real-time
deployment need their own measured acceptance criteria.
