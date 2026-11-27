---
name: audio-intermodulation
description: Measure two-tone audio intermodulation distortion. Use for IMD2 and IMD3 levels, sum and difference products, alias and collision checks, and ratios to measured output carriers.
---

# Audio intermodulation

1. **Set the stimulus and capture.** Choose two coherent
   tones. Record frequencies, peak levels, phases, tap,
   channel, rate, and band. Check headroom and measure
   the source or loopback at the same drive.
   [Capture and stimulus](references/INTERMODULATION_CONTRACT.md#capture-and-stimulus)
2. **Map candidates to bins.** Predict the signed products.
   Apply the declared sampling policy. Include carrier,
   harmonic, and DC candidates in the collision check.
   Keep the observed bin and all possible contributors.
   [Product assignment](references/INTERMODULATION_CONTRACT.md#product-assignment)
3. **Measure isolated lines.** Use calibrated bin power.
   Name the output carrier reference and selected products.
   Report unavailable ratios when a carrier or product
   fails qualification.
   [Carrier references](references/INTERMODULATION_CONTRACT.md#carrier-references) ·
   [Offline reference](scripts/reference_intermodulation.py)
4. **Check the assignment.** Compare a linear control with
   a quadratic and a cubic response. Change drive, tone
   spacing, or sample rate to probe a suspected overlap.
   [Known results](../../tests/fixtures/AUDIO_INTERMODULATION_GOLDENS.md)
