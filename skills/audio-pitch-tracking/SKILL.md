---
name: audio-pitch-tracking
description: Estimate monophonic fundamental frequency from sample-clocked PCM. Use for pitch and voicing, octave errors, missing fundamentals, short frames, sub-sample lag refinement, or evaluation in cents.
---

# Audio pitch tracking

1. **State the pitch target.** Choose a channel or declare a mix.
   Record its tap, rate, units, and gain. Set the expected pitch
   band. Use a single pitch for a signal with one dominant
   periodicity. Check the harmonics when two lags could explain
   the same signal.
   [Signal model](references/PITCH_TRACKING_CONTRACT.md#signal-model) ·
   [Harmonic analysis](../audio-harmonic-analysis/SKILL.md)
2. **Choose support for the lowest pitch.** Set the comparison
   width, search lags, guard lags, and hop. Use the same number of
   pairs at each lag. Wait for complete input. Check phase and
   frame length with a clean tone near the lower frequency limit.
   [Frame geometry](references/PITCH_TRACKING_CONTRACT.md#frame-geometry)
3. **Keep the lag evidence.** Save the raw difference, normalized
   depth, and competing troughs. Normalize from lag one. Qualify
   troughs with a declared threshold. Check the fitted period
   against the physical band after interpolation.
   [Candidate rules](references/PITCH_TRACKING_CONTRACT.md#candidate-selection-and-refinement)
4. **Qualify voicing.** Check AC level in the declared PCM units.
   Report missing input, silence, constant input, low AC level,
   and an unvoiced frame as distinct results. Retain both octave
   candidates when a weak harmonic can change the decision.
   [Level and voicing](references/PITCH_TRACKING_CONTRACT.md#level-and-voicing)
5. **Verify on the sample clock.** Keep the frame center, first
   complete input boundary, and observed delivery boundary.
   Replay with different block sizes. If you add continuity,
   test voicing transitions and pitch leaps. Report voicing
   errors, signed cents, and octave errors on aligned labels.
   [Timing and evaluation](references/PITCH_TRACKING_CONTRACT.md#timing-tracking-and-evaluation) ·
   [Reference](scripts/reference_pitch_tracking.py) ·
   [Fixtures](../../tests/fixtures/AUDIO_PITCH_TRACKING_GOLDENS.md)
