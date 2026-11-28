---
name: audio-transfer-response
description: Measure complex audio transfer from a reference tap to a response tap. Use for H1 and H2 estimates, paired Welch spectra, excitation and coherence gates, response nulls, and delay sign.
---

# Audio transfer response

1. **Identify the path.** Record both taps, units,
   gains, clock, original intervals, and any applied
   advance. Pair complete windows on the common clock.
   Check the stimulus band and response support.
   [Path and support](references/TRANSFER_RESPONSE_CONTRACT.md#path-and-support)
2. **Choose the estimate.** Pool the conjugate-reference
   cross products and both auto powers on the same
   support. Choose H1 or H2 based on evidence of where
   noise enters the measurement.
   [Estimator choice](references/TRANSFER_RESPONSE_CONTRACT.md#estimator-choice)
3. **Qualify each bin.** Keep both powers, the cross
   density, coherence, and segment support. Check the
   relevant denominators and distinguish a zero output
   from a zero cross density with positive output.
   [Bin qualification](references/TRANSFER_RESPONSE_CONTRACT.md#bin-qualification) ·
   [Offline reference](scripts/reference_transfer_response.py)
4. **Check phase and delay.** Compare a known delay and
   a known null. Keep any applied advance with the
   result. Repeat at a second level or time to test
   the path model.
   [Timing](references/TRANSFER_RESPONSE_CONTRACT.md#timing) ·
   [Fixture values](../../tests/fixtures/AUDIO_TRANSFER_RESPONSE_GOLDENS.md)
