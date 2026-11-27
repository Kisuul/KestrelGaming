---
name: audio-event-segmentation
description: Detect boundaries between regimes in sample-clocked audio features. Use for audio cuts, section or activity changes, two-sided novelty, gap handling, peak lookahead, segment coverage, and boundary evaluation.
---

# Audio event segmentation

1. **Define the boundary.** Choose what changes and at what
   scale. Use a feature that measures that change. Declare the
   tap, units, normalization, source clock, and frame profile.
   Check a gain step and a change at constant level.
   [Feature selection](references/EVENT_SEGMENTATION_CONTRACT.md#feature-selection)
2. **Compare both sides.** Use complete, equally sized feature
   windows. Keep the signed mean change and squared distance.
   Treat a measured zero as available. Break support at a gap
   or a change in epoch or feature profile.
   [Score and support](references/EVENT_SEGMENTATION_CONTRACT.md#score-and-support)
3. **Confirm the peak.** Set the peak radius and threshold.
   Require every score within the radius. The cut must meet
   the threshold, exceed every score on the left, and meet or
   exceed every score on the right. Record the cut position,
   when the score and its flanks are ready, and any reported
   evidence delivery.
   [Selection and timing](references/EVENT_SEGMENTATION_CONTRACT.md#selection-and-timing) ·
   [Offline reference](scripts/reference_event_segmentation.py)
4. **Report coverage and evaluate.** Partition supported runs
   using the selected cuts. Mark unknown spans and keep
   imposed endpoints as coverage boundaries. Match interior
   cuts one-to-one on the exact clock. Score label agreement
   separately on the declared time intervals.
   [Coverage and evaluation](references/EVENT_SEGMENTATION_CONTRACT.md#coverage-and-evaluation) ·
   [Fixtures](../../tests/fixtures/AUDIO_EVENT_SEGMENTATION_GOLDENS.md)
