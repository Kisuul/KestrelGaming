---
name: audio-phase-coherence
description: Measure frequency-dependent phase and magnitude-squared coherence from paired PCM. Use to diagnose transfer measurements, polarity, delay, band cancellation, and the effects of gain changes or segment alignment.
---

# Phase and coherence

1. **Identify the pair.** Name the reference and measurement channels.
   Record their tap, clock, units, and exact sample support. Record any
   known alignment offset and both original intervals.
   [Shared capture](../audio-oscilloscope/SKILL.md)
2. **Match the segment profile.** Use the same complete segment starts,
   window, detrending, and DFT length for both channels. Report the
   number of complete segments and the used interval.
   [Profile and density](references/PHASE_COHERENCE_CONTRACT.md#welch-profile)
3. **Pool the complex products.** Average both auto powers and the
   conjugate-reference cross-products before forming coherence or phase.
   Check auto powers, the summed cross-product, and the energized pair
   count. Preserve unavailable measurements and separate display masking.
   [Validity](references/PHASE_COHERENCE_CONTRACT.md#read-the-measurement) ·
   [Offline reference](scripts/reference_phase_coherence.py)
4. **Test a diagnosis.** Compare wrapped phase with a known delay or
   polarity change. Replay a shared transient with a known sample offset.
   Check the pairing and the delivered mono output when a band cancels.
   Use a stated null model for any significance threshold.
   [Interpretation](references/PHASE_COHERENCE_CONTRACT.md#interpret-the-estimate) ·
   [Review fixtures](../../tests/fixtures/AUDIO_PHASE_COHERENCE_GOLDENS.md)

Report the profile, measured channel levels, phase convention, available
bins, and evidence for the diagnosis. State when a reading depends on
one energized pair or on a changed alignment.
