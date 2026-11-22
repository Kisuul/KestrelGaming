---
name: audio-group-delay
description: Measure group delay from known filter coefficients or sampled complex transfer data. Use to check phase slope, frequency-dependent timing, alignment offsets, apertures, and unavailable measurements near spectral nulls.
---

# Audio group delay

1. **Declare the time reference.** Name the reference and measurement
   taps. Record clock, epoch, sample rate, original intervals, and
   any advances already applied. Report group delay in samples and
   seconds. Confirm sign with a known pure delay.
   [Timing and units](references/GROUP_DELAY_CONTRACT.md#timing-and-units)
2. **Select the measurement.** For known FIR or rational sections, use
   the coefficient derivative. For a sampled transfer, check excitation,
   both tap levels, and phase continuity over every used interval.
   [Known model](references/GROUP_DELAY_CONTRACT.md#known-model) ·
   [Welch phase and coherence](../audio-phase-coherence/SKILL.md)
3. **Qualify the sampled branch.** Use an independent delay bound, a
   known coarse advance, or a finer supported grid. Check adjacent
   phase increments. Split the aperture at a null, rejected bin, or
   gap. Restore each advance once.
   [Sampled transfer](references/GROUP_DELAY_CONTRACT.md#sampled-transfer) ·
   [Offline reference](scripts/reference_group_delay.py)
4. **Verify the diagnosis.** Report the actual aperture and unavailable
   intervals. Compare two apertures, then repeat the measurement with
   a known delay. Inspect the impulse when the task asks for first
   arrival or broadband timing.
   [Review fixtures](../../tests/fixtures/AUDIO_GROUP_DELAY_GOLDENS.md)

Separate a point derivative from a sampled aperture average in the
report. Include the branch evidence and time reference with each curve.
