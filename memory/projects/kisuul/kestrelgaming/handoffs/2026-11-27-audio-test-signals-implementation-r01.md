---
schema: 1
id: 2026-11-27-audio-test-signals-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: Kestrel
created: 2026-11-27
updated: 2026-11-27
sources: "Audio branch at 911038359fb5a6d7159f141502fe00454450505e, merged research PR #55, Gauge review G44-F01, and executed phase, headroom, and FIR fixtures."
---

# Audio test signals skill #44 implementation and review

## Summary

**Task outcome:** COMPLETE

The skill teaches stimulus choice, sample support,
phase, headroom, and sweep verification. The bounded
reference renders whole records and absolute subspans.
It keeps each channel recipe, active span, guards, and
observed sample peaks with the result. The shared fixture
bank supplies the short comparison signals and seeded
noise.
[Skill](../../../../../skills/audio-test-signals/SKILL.md) ·
[Contract](../../../../../skills/audio-test-signals/references/TEST_SIGNALS_CONTRACT.md) ·
[Research](2026-11-26-audio-test-signals-research-r01.md)

## Evidence

- For the initial implementation, the seed validator,
  28 local links and anchors, whitespace check, and all
  1,189 local tests passed. The 30 focused tests cover large
  origins, exact block replay, endpoint phase, off-bin power,
  and sub-ulp headroom. Seventeen deliberate faults failed
  targeted assertions.
  [Executable checks](../../../../../tests/test_audio_test_signals_reference.py)
- Measured in sample amplitude, 2,048 direct-phase tone
  checks and 512 sweep checks with mpmath 1.3.0 agreed
  within $1.2\times10^{-16}$ and $3.3\times10^{-12}$,
  respectively. SciPy 1.17.0 agreed within
  $1.5\times10^{-12}$ over 24,000 up- and down-sweep
  samples. The partition check matched 27,382
  independently rendered stereo subspans exactly.
- NumPy 2.3.5 recovered the known FIR within
  $3.3\times10^{-16}$ across 1,621 usable bins.
  Dropping the five-sample response tail raised the
  maximum complex error to 0.00468616.

## Review correction

Gauge found that rounding a subnormal normalized
endpoint before computing sweep growth changed the
integrated phase. The reference now computes growth
from the exact endpoint ratio. It uses a scaled
mantissa for wide ratios and keeps the largest
normalized endpoint as the phase scale.
[Gauge review](https://github.com/Kisuul/KestrelGaming/pull/68#pullrequestreview-6092582631)

The seven regression samples failed on the reviewed
head. Both directions now agree with a 120-digit
oracle within $4.4\times10^{-15}$ FS at those offsets.
An independent 160-digit comparison checked 2,048
samples across 256 sweeps. The maximum sample error
was below $2.0\times10^{-11}$ FS. The normalized
endpoint positivity test still rejects a value that
rounds to zero. The corrected reference passed all
1,190 local tests, including 31 focused checks.

## Next action

Give Gauge both directions of the subnormal endpoint
case and the scale and growth bounds in the contract.
Check the limiting sweeps and the complete FIR response.
[Fixture values](../../../../../tests/fixtures/AUDIO_TEST_SIGNALS_GOLDENS.md)

## Revisit when

The synthesis phase law, channel recipe, headroom
policy, support, or usable excitation band changes.
