---
name: audio-noise-snr-sinad
description: Measure audio noise power, signal-to-noise ratio, and SINAD. Use for quiet-input and driven captures, PSD bandwidth, spur exclusions, and quantization limits.
---

# Audio noise, SNR, and SINAD

1. **Declare the measurement.** Record whether the
   input is quiet or driven. Keep the stimulus or
   termination, tap, gain, units, capture interval, band,
   weighting, and reference.
   [Capture and reference](references/NOISE_SNR_SINAD_CONTRACT.md#capture-and-reference)
2. **Integrate power.** Apply the declared band and
   endpoint policy. Multiply calibrated density by
   bin width once. Pool comparable powers before
   converting to dB.
   [Band power](references/NOISE_SNR_SINAD_CONTRACT.md#band-power)
3. **Assign the driven residual.** Keep the fundamental,
   harmonics, declared spur exclusions, and noise powers.
   Use the masked noise term for SNR and the full admitted
   residual for SINAD. Qualify the signal before giving
   a ratio.
   [Driven ratios](references/NOISE_SNR_SINAD_CONTRACT.md#driven-ratios) ·
   [Offline reference](scripts/reference_noise_snr_sinad.py)
4. **Verify the interpretation.** Check a quiet capture,
   an SNR spur mask, and a bandwidth change. State
   stimulus and noise assumptions before using SINAD
   to estimate effective bits.
   [Quantization](references/NOISE_SNR_SINAD_CONTRACT.md#quantization) ·
   [Fixture values](../../tests/fixtures/AUDIO_NOISE_SNR_SINAD_GOLDENS.md)
