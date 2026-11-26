---
schema: 1
id: 2026-11-26-audio-sound-classification-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch a435c790546b7aefc8ba35ba18be1d7c235f916f; AudioSet ontology and strong labels; ESC-50 source folds; DCASE 2024 Task 4; executed threshold, ranking, and split leakage checks."
---

# Skill 65 research for sound classification

## Summary

**Task outcome:** COMPLETE

Define prediction and annotation units before training or
scoring. Preserve label semantics and partition original
recordings before deriving windows or augmented samples.
The fixtures show what a decision threshold can hide
about ranking quality and how clip-level splits can leak
source identity.
[AudioSet ontology and data paper](https://research.google/pubs/audio-set-an-ontology-and-human-labeled-dataset-for-audio-events/) ·
[ESC-50 folds](https://github.com/karolpiczak/esc-50)

## Evidence

### Match model outputs to the labels

Use an exclusive class decision only when each example
has one class under the task definition. For overlapping
sound categories, retain their individual scores and
permit multiple positive decisions. A clip-level label
can mark presence anywhere in the clip. An event label
requires time support and scoring rules for cross-label
overlap, boundary collars or overlap ratios, as applicable
to the selected evaluation. Declare unknown, unreviewed,
and confirmed absent labels. Score only the annotations
eligible under the dataset's completeness rules.
[AudioSet strong labels](https://research.google.com/audioset/download_strong.html) ·
[DCASE 2024 Task 4](https://dcase.community/challenge2024/) ·
[Event segmentation](2026-11-26-audio-event-segmentation-research-r01.md)

Pin the ontology version, label mapping, input tap,
sample rate, channel treatment, window, feature scaling,
and model release. Split by source before cropping and
augmentation. Keep repeated takes, speakers, rooms, or
devices together when independence along that axis is
required. Record the split definition and audit
intersections. Use known data to fit preprocessing and
validation data to select thresholds. Reserve the test
partition for reporting. Preserve dataset-native folds
where they define the benchmark, as in ESC-50.
[ESC-50 folds](https://github.com/karolpiczak/esc-50) ·
[Analysis provenance](../../../../../skills/audio-analysis-provenance/SKILL.md)

### Report ranking and operating-point evidence

For each class, report positive support, a ranking metric,
and operating-point counts with the threshold comparison.
Average precision (AP) for a tie-free list is the sum of
precision at the ranks of all positives, divided by the
number of positives. Pin the treatment of ties and
classes without positives. For F1, use
$2TP/(2TP+FP+FN)$ when the denominator is positive.
Compute micro F1 from pooled counts and macro F1 as
the mean across the eligible classes. State how empty
classes affect the mean. Report how the result changes
for rare classes or a held-out recording condition.
[Average precision definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html) ·
[F1 aggregation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html)

### Executed checks and portable fixtures

The table contains complete binary labels for both
classes. Sort scores by decreasing value within each
class. For operating-point counts, mark a positive
where the score is at least `0.5`.

| Clip | A present | B present | A score | B score |
| --- | --- | --- | --- | --- |
| 1 | 1 | 0 | 0.9 | 0.1 |
| 2 | 0 | 1 | 0.8 | 0.9 |
| 3 | 1 | 1 | 0.7 | 0.4 |
| 4 | 0 | 0 | 0.6 | 0.2 |
| 5 | 0 | 0 | 0.2 | 0.3 |
| 6 | 0 | 1 | 0.1 | 0.5 |

A has counts `(TP, FP, FN) = (2, 2, 0)` and AP
`(1 + 2/3)/2 = 5/6`. B has counts `(2, 0, 1)` and
AP `1`. B ranks all positives ahead of its negatives
but misses the positive below the decision threshold.
Micro F1 is `8/11`, macro F1 is `11/15`, and mean AP
is `11/12`. Scikit-learn 1.8.0 reproduced all three
aggregates for the table. For two negative labels with scores
`[0.8, 0.1]`, AP is unavailable under this fixture policy.

For a split audit, use training sources `take-2` and
`take-7` and test sources `take-7` and `take-13`. The
intersection contains `take-7`, even with unique clip
names. Reject the split by source ID. These checks verify
scoring and split preconditions. Acoustic classification
performance requires a fit and held-out evaluation.

## Next action

Define the annotation unit and split keys, then attach
score and decision records to the same support. Give
Gauge the two-class table, tied scores, incomplete
labels, a source split violation, and a held-out category
with no positives. Measure a declared operating point on
held-out recordings.

## Revisit when

The ontology, model, frontend, label completeness,
data grouping, threshold, or time-scoring policy changes.
