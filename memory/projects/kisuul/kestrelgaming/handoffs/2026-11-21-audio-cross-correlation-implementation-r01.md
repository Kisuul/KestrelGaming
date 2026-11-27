---
schema: 1
id: 2026-11-21-audio-cross-correlation-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: archived
evidence: observed
author: Kestrel
created: 2026-11-21
updated: 2026-11-26
sources: "Owner requested Skill #34. Audio development base a5a530d30a9ffaaf57879f5523247a59c87ce10a. Research PR #45 at f80718da04cb224ed45c8aeba496fb89089f282a. Focused tests, SciPy 1.17.0, independent exact enumeration, and deliberate-fault checks executed. Gauge reviewed 5832c81d48cadcc65efba05bb4fa16b98f1f6c46. PR #47 merged at e98036399451a4c76f251a79e85a3ca8aa30ad99."
---

# Skill #34 audio cross-correlation implementation and review

## Summary

**Task outcome:** COMPLETE

Gauge gave a technical GO on `5832c81`. Skill #34 merged
in PR #47 at `e980363`.
[Gauge review](https://github.com/Kisuul/KestrelGaming/pull/47#pullrequestreview-6009195041) · [Merged PR #47](https://github.com/Kisuul/KestrelGaming/pull/47)

The reference evaluates the requested integer delays on one declared
sample clock. It keeps the signed lag, exact clock delay, overlap
intervals, four score modes, eligibility, and the two strongest
rank groups. The skill uses controlled probes and competing peaks
to diagnose delay, polarity, periodic ambiguity, and reflections.
[Skill](../../../../../skills/audio-cross-correlation/SKILL.md) ·
[Contract](../../../../../skills/audio-cross-correlation/references/CROSS_CORRELATION_CONTRACT.md) ·
[Research](https://github.com/Kisuul/KestrelGaming/blob/f80718da04cb224ed45c8aeba496fb89089f282a/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-21-audio-cross-correlation-research-r01.md)

## Evidence

- All 29 focused tests and 24 adjacent stereo correlation tests
  passed locally. Fixtures include 128 callback partitions, a local
  lag of $-2$ with clock delay $+3$, periodic ties, and two peaks that
  round to the same display value.
  [Fixtures](../../../../../tests/fixtures/AUDIO_CROSS_CORRELATION_GOLDENS.md) ·
  [Tests](../../../../../tests/test_audio_cross_correlation_reference.py)
- Exact pair enumeration at seed `3420261121` checked 160 captures,
  5,112 score rows, 2,301 binary64 rounding cells, and 640 peak
  decisions. A full 1,024-by-1,024 capture sweep covered 2,047 lags
  and 1,048,576 paired terms.
- Seed 340020 matched 836 padded FFT values against the raw curve
  within $2.67\times10^{-15}$. SciPy 1.17.0 direct and FFT modes
  matched the same 418 lags. The sinc and two-band weighting
  diagnostics reproduced the research values. Seven deliberate
  faults failed their targeted tests.

## Next action

Use the [current curriculum ledger](2026-11-17-audio-curriculum-status-r01.md) for the next module.

### Review plan at submission

Review the exact PR head. Run the input-only review tasks and record
the observed decisions. Count Skill #34 after owner acceptance.
[Owner completion gate](../2026-11-04-audio-curriculum-full-completion-gate-r01.md)

## Revisit when

The capture clock, tap pair, score mode, peak criterion, or numerical
representation changes.
