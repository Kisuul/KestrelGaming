---
schema: 1
id: 2026-11-27-audio-thd-thdn-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: Kestrel
created: 2026-11-27
updated: 2026-11-27
sources: "Audio branch at 911038359fb5a6d7159f141502fe00454450505e, merged research PR #55, analytic fixtures, and an independent NumPy FFT comparison."
---

# THD and THD+N skill #45 implementation and review

## Summary

**Task outcome:** COMPLETE

The skill keeps four powers with three named ratios. The
reference measures a rectangular, unpadded coherent
capture with a known fundamental bin. It retains the
capture support, exact frequencies, admitted powers, and
harmonic dispositions. The off-bin probes check
fundamental rejection and the conditions for power
closure.
[Skill](../../../../../skills/audio-thd-thdn/SKILL.md) ·
[Contract](../../../../../skills/audio-thd-thdn/references/THD_THDN_CONTRACT.md) ·
[Research](2026-11-26-audio-thd-thdn-research-r01.md)

## Evidence

- The 26 focused checks cover the four coherent powers,
  both THD+N references, weak residuals, DC and band
  admission, Nyquist and odd endpoints, alias geometry,
  qualification, and off-bin rejection. The checks
  detected 14 deliberate faults in accounting and
  qualification.
  [Executable checks](../../../../../tests/test_audio_thd_thdn_reference.py) ·
  [Fixture values](../../../../../tests/fixtures/AUDIO_THD_THDN_GOLDENS.md)
- An independent FFT agreed across 512 coherent captures,
  including 24,960 bin powers and 309 qualified reports.
  Maximum absolute bin and aggregate power errors were below
  $1.05\times10^{-15}$ in squared PCM units. The maximum
  ratio level error was below $10^{-11}$ dB.
- Removing the nearest bin left about 0.43475 of the
  original RMS in the off-bin fixture. The known-frequency
  projection left less than $3\times10^{-15}$. The
  short-span two-line fixture has a nonzero cross term
  when removing the fundamental component.

## Next action

Give Gauge the equal-power denominator counterexample,
the weak residual with equal rounded totals, and the
Nyquist assignment where a fourth-order fold coincides
with the second-order bin. Check that an unavailable
fundamental preserves the measured powers and that an
off-bin joint fit can leave a cross term.

## Revisit when

The fundamental estimator, weighting, admitted band,
harmonic policy, or ratio reference changes.
