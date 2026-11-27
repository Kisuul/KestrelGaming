---
name: audio-thd-thdn
description: Measure audio harmonic distortion and in-band residual power. Use for THD, THD+N, fundamental rejection, harmonic assignment, and comparisons with different ratio references.
---

# Audio THD and THD+N

1. **Declare the measurement.** Record the tap, channel,
   sample rate, capture interval, stimulus frequency and
   level, weighting, band, and DC policy. For the coherent
   reference, use a complete rectangular record and a known
   interior fundamental bin.
   [Capture and bin power](references/THD_THDN_CONTRACT.md#capture-and-bin-power)
2. **Assign powers.** Sum the admitted harmonic bins for
   distortion. Sum all admitted bins except the fundamental
   for the residual. Keep the fundamental power, total band
   power, and a disposition for each requested harmonic.
   [Harmonics and residual](references/THD_THDN_CONTRACT.md#harmonics-and-residual) ·
   [Offline reference](scripts/reference_thd_thdn.py)
3. **Name the denominator.** Use fundamental power for THD.
   State whether THD+N uses fundamental or total in-band
   power. Report a zero numerator and an unavailable
   reference as distinct results.
   [Ratio references](references/THD_THDN_CONTRACT.md#ratio-references)
4. **Check rejection.** Verify the coherent powers first.
   For an off-bin tone, test the fundamental rejection method
   with a clean tone, a nearby spur, and a frequency error.
   [Off-bin checks](references/THD_THDN_CONTRACT.md#off-bin-checks) ·
   [Fixture values](../../tests/fixtures/AUDIO_THD_THDN_GOLDENS.md)
