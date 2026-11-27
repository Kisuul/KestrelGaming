---
schema: 1
id: 2026-11-27-audio-intermodulation-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: Kestrel
created: 2026-11-27
updated: 2026-11-27
sources: "Audio branch at db83e5180e67ec31487226c60648671a237287e1, Skill 46 research from merged PR #55, and executed waveform and geometry checks."
---

# Intermodulation skill #46 implementation and review

## Summary

**Task outcome:** COMPLETE

The skill measures known two-tone products on a
rectangular coherent capture. The report keeps signed
nominal frequencies, measured bin powers, candidate
membership, and the selected carrier reference. The
profile declares digital folding or verified band limiting
and the quadratic or cubic family for collision checks.
[Skill](../../../../../skills/audio-intermodulation/SKILL.md) ·
[Contract](../../../../../skills/audio-intermodulation/references/INTERMODULATION_CONTRACT.md) ·
[Research](2026-11-26-audio-intermodulation-research-r01.md)

## Evidence

- The seed validator, whitespace check, 24 local links
  and anchors, and all 1,244 local tests passed. The 28
  focused checks cover carrier references, absolute line
  growth, bands, endpoints, alias and collision geometry,
  and ratio qualification. They detected 14 deliberate
  faults.
  [Executable checks](../../../../../tests/test_audio_intermodulation_reference.py) ·
  [Fixture values](../../../../../tests/fixtures/AUDIO_INTERMODULATION_GOLDENS.md)
- Independent grouping matched 4,060 geometry profiles
  and 16,240 signed product assignments. An independent
  FFT matched 33,184 bins in 256 captures and 791 ratio
  levels. Maximum absolute differences were
  $4.5\times10^{-15}$ in squared PCM units and
  $2.1\times10^{-10}$ dB.
- In the 19 and 20 kHz fixture, the 39 kHz sum has peak
  0.02 at 39 kHz in the 96 kHz capture and at 9 kHz in
  the 48 kHz capture. The cubic family adds the possible
  fold of 57 kHz to the same bin at both rates.
- In the 9 and 15 kHz fixture, a quarter-turn phase
  change moves the shared 21 kHz peak from 0.00035
  to 0.00005. Both captures retain the same collision.
  The isolated 6 kHz line from the 7 and 8 kHz fixture
  gives −56.517174 dBc and −50.516008 dBc using
  the low and high output carriers, respectively.

## Next action

Give Gauge the two-rate fold with both candidate families,
the 21 kHz shared-bin phases, the paired and unpaired
endpoint powers, and the incomplete group under a band
cut. Confirm that both carriers qualify before reporting
any ratio.

## Revisit when

The capture window, candidate family, source or filter
model, frequency band, or ratio reference changes.
