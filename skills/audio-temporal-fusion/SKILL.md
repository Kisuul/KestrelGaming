---
name: audio-temporal-fusion
description: Associate compatible audio-event estimates on a common sample clock. Use for event matching across taps or rates, exact timing gates, missing coverage, readiness, late evidence, and commitment.
---

# Audio temporal fusion

1. **Declare the event and sources.** Name the event each
   contributor estimates and the run it belongs to. Keep source,
   tap, epoch, event ID, revision, and input support. Keep
   related events and forecasts as context.
   [Clock mapping](references/TEMPORAL_FUSION_CONTRACT.md#clock-mapping)
2. **Align and associate.** Map event positions and support to
   a common clock. Start at the earliest unassigned estimate.
   Apply the inclusive time gate and use at most one estimate
   per source. Preserve gaps, competing estimates, weights,
   and timing residuals.
   [Association and coverage](references/TEMPORAL_FUSION_CONTRACT.md#association-and-coverage) ·
   [Offline reference and replay](scripts/reference_temporal_fusion.py)
3. **Commit on evidence.** Keep the label, data readiness,
   and observed dispatch times. For an inclusive gate, wait
   until each required source guarantees progress beyond
   the gate or finalizes. Preserve earlier provisional
   decisions when late evidence changes the association.
   [Readiness and commitment](references/TEMPORAL_FUSION_CONTRACT.md#readiness-and-commitment)
4. **Verify the join.** Replay fractional positions, a tie at
   the gate edge, a late earlier estimate, and a silent or
   missing source. Check that valid continuations preserve
   a committed prefix.
   [Verification](references/TEMPORAL_FUSION_CONTRACT.md#verification) ·
   [Fixtures](../../tests/fixtures/AUDIO_TEMPORAL_FUSION_GOLDENS.md)
