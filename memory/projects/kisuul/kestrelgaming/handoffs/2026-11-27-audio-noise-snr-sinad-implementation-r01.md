---
schema: 1
id: 2026-11-27-audio-noise-snr-sinad-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: Kestrel
created: 2026-11-27
updated: 2026-11-27
sources: "Audio branch at d5dcd2728274f1adf74cdaa27b01a93335a6cd03, Skill 47 research from merged PR #55, and executed coherent and quiet-input checks."
---

# Noise, SNR, and SINAD skill #47 implementation and review

## Summary

**Task outcome:** COMPLETE

The reference reports in-band quiet-input noise and
driven SNR and SINAD on complete rectangular records.
It uses the accepted coherent bin powers. The driven
ledger keeps signal, declared harmonics, SNR-only spur
exclusions, and remaining noise. SINAD uses the full
admitted residual.
[Skill](../../../../../skills/audio-noise-snr-sinad/SKILL.md) ·
[Contract](../../../../../skills/audio-noise-snr-sinad/references/NOISE_SNR_SINAD_CONTRACT.md) ·
[Research](2026-11-26-audio-noise-snr-sinad-research-r01.md)

## Evidence

- The seed validator, whitespace check, 24 local links
  and anchors, and all 1,273 local tests passed. The 29
  focused checks cover quiet noise, coherent assignments,
  bands, endpoint weights, weak residuals, signal
  qualification, Welch power, and sub-step quantization.
  They detected 14 deliberate faults.
  [Executable checks](../../../../../tests/test_audio_noise_snr_sinad_reference.py) ·
  [Fixture values](../../../../../tests/fixtures/AUDIO_NOISE_SNR_SINAD_GOLDENS.md)
- An independent FFT and bin mask check matched 256
  driven and 256 quiet-input reports. It compared 15,936
  bin powers and 170 finite ratios. Maximum differences
  were below $6.2\times10^{-16}$ in squared PCM units
  and $1.9\times10^{-12}$ dB.
- The two-spur fixture gives SNR 46.98970004 dB
  with both lines in the noise term and 53.97940009 dB
  with one line excluded. Full-residual SINAD is
  39.20818754 dB for both. The weak residual retains
  about $2^{-65}$ in squared PCM units when rounded
  signal and band powers are equal.
- The portable three-window Welch case gives power
  0.000796486372634173 at 128 and 256 DFT points.
  Its time-domain window-energy calculation agrees.
  The sub-step quantizer produces a zero output and
  error power 0.02 steps squared.

## Next action

Give Gauge the SNR-only mask, the two Welch grids,
the zero-noise case with a nonzero harmonic, and the
quiet-input result with unavailable signal ratios.
Compare SINAD with the two THD+N references on the
equal signal and residual case.

## Revisit when

The operating state, weighting, band, stimulus,
exclusion membership, or reference level changes.
