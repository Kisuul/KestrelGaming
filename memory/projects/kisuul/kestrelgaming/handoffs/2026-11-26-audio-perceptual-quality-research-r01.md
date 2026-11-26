---
schema: 1
id: 2026-11-26-audio-perceptual-quality-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch a435c790546b7aefc8ba35ba18be1d7c235f916f; ITU-T P.800 and P.800.1; ITU-R BS.1116 and BS.1534; ViSQOL documentation; executed error localization and rating aggregation checks."
---

# Skill 63 research for perceptual quality

## Summary

**Task outcome:** COMPLETE

Choose a listening test or predictor that fits the content,
expected impairments, and decision. Keep the study protocol,
aggregation unit, and provenance with each result.
A global error average can hide a local event. Unbalanced
ratings can reverse a comparison when the aggregation
changes. The fixtures let Gauge check both effects.
[ITU-T P.800.1](https://www.itu.int/ITU-T/recommendations/rec.aspx?rec=P.800.1)

## Evidence

### Select the test and control the comparison

| Question | Starting point |
| --- | --- |
| How do listeners rate speech transmission quality? | Select the relevant procedure in [ITU-T P.800](https://www.itu.int/rec/T-REC-P.800-199608-I/en). |
| Can listeners rate very small audio impairments? | Use the small-impairment methods in [ITU-R BS.1116](https://www.itu.int/rec/R-REC-BS.1116). |
| How do several intermediate-quality versions compare with a reference and anchors? | Review the MUSHRA method in [ITU-R BS.1534](https://www.itu.int/rec/R-REC-BS.1534/en). |

Pin the method and edition. Record programme material,
degradation, playback equipment, presentation level,
listener criteria, and test environment. Control order
and hide system identity. Use references, hidden
references and anchors as the method specifies. Balance
clip and listener assignment across systems. Predeclare
how to handle missing responses and how much weight each
clip or listener gets. Show sample sizes and uncertainty
that account for repeated ratings. Use the same stated
comparison objective for each system.

Keep listening ratings and model predictions under distinct
score names. Mean opinion score (MOS) requires the method
and origin of the ratings or estimates. For a full-reference
utility such as ViSQOL, pin the release, mode, model,
input transformations and score interpretation. Check
its required reference and sample rate. Review what the
comparison tap, gain match, alignment and any downmix do
to an impairment. Include a known degradation to check
the predictor and retain listening evidence for the
deployment domain.
[ITU-T P.800.1](https://www.itu.int/ITU-T/recommendations/rec.aspx?rec=P.800.1) ·
[ViSQOL modes and input requirements](https://github.com/google/visqol) ·
[Speech intelligibility](2026-11-26-audio-speech-intelligibility-research-r01.md)

### Executed checks and portable fixtures

Use 100 samples. Error A has value `0.01` at every sample.
Error B has 99 zeros followed by `0.1`. Compute the mean
square on all samples and the maximum of the mean squares
over ten disjoint windows of ten samples. Convert the
window statistic to dB relative to unit squared amplitude.

| Error | Mean square | Worst window |
| --- | --- | --- |
| A, spread across the record | `0.0001` | `−40 dB` |
| B, isolated in the last window | `0.0001` | `−30 dB` |

The peak window check exposes a difference in concentration.
Audibility and preference still depend on content, time scale,
level and listening conditions.

For an aggregation check, use two clips and two systems.
On the easy clip, A has one rating of 5 and B has nine
ratings of 4. On the hard clip, A has nine ratings of 2 and
B has one rating of 1.

| System | Mean of all ratings | Mean of the two clip means |
| --- | --- | --- |
| A | `2.3` | `3.5` |
| B | `3.7` | `2.5` |

The pooled ratings weight different material for each
system. Equal clip weights give the same material weights
for both. In a real test, define the target mix of clips and
listeners in advance and use that design to make the
comparison. This constructed ratings table checks the
calculation. Listening results and validation of a specific
predictor require separate observations.

## Next action

Give Gauge a full test record with impairments, sample
counts, method, mode, support, and aggregation. Include
equal average power with different error timing, a case
that changes under downmix, and the unequal ratings
fixture. For a release decision, collect the ratings or
validate a predictor in the target domain.

## Revisit when

The impairments, reference, playback setup, listener group,
predictor or aggregation design changes.
