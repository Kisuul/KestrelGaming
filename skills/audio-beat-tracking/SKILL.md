---
name: audio-beat-tracking
description: Estimate tempo and align musical beats on a sample-clocked novelty curve. Use for beat grids, half-rate or double-rate ambiguity, missed beats, tempo changes, timing drift, or beat-tracking evaluation.
---

# Audio beat tracking

1. **Define the pulse.** State what a listener should tap. Name the
   target metrical level and any levels the application accepts.
   Record the label convention. If the task needs bar position, include
   separate evidence for the downbeat.
2. **Keep the novelty clock.** Use continuous onset strength. Preserve
   the tap, epoch, window, hop, exact rate, and frame centers. Distinguish
   missing features from measured zeros. Start a new run at a gap or
   an incompatible input change.
   [Input clock](references/BEAT_TRACKING_CONTRACT.md#input-clock-and-readiness) ·
   [Onset detection](../audio-onset-detection/SKILL.md)
3. **Rank plausible tempos.** Measure periodicity with enough overlap
   and cycles. Check the effect of a steady floor. Compare half-rate
   and double-rate candidates on the same support. Record when a prior
   resolves an ambiguity.
   [Period evidence](references/BEAT_TRACKING_CONTRACT.md#period-evidence)
4. **Align the beat phase.** Start with a known tempo. Check onset
   evidence and the cost of changing each beat interval. Retain
   inferred beats and apply an elapsed limit through quiet spans.
   Use supplied local periods to isolate a tempo change from a
   phase-tracking error.
   [Path objective](references/BEAT_TRACKING_CONTRACT.md#beat-path) ·
   [Offline reference](scripts/reference_beat_tracking.py)
5. **Report timing and verify.** Keep the beat estimate and input
   boundary used for the decision. For a live system, specify a
   commitment rule and measure dispatch. Match beats one-to-one on
   the declared pulse level. Report continuity and signed timing
   errors alongside tempo and match counts.
   [Evaluation](references/BEAT_TRACKING_CONTRACT.md#evaluation) ·
   [Fixtures](../../tests/fixtures/AUDIO_BEAT_TRACKING_GOLDENS.md)
