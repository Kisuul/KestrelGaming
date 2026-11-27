---
schema: 1
id: 2026-11-26-audio-onset-detection-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: archived
evidence: observed
author: Kestrel
created: 2026-11-26
updated: 2026-11-26
sources: "Audio development head 5681c370b4c9ecca97f94845f43ffbd14895e16a, merged research PR #49, calibration and peak fixtures, local repository tests, and independent NumPy and SciPy checks. Gauge reviewed 34ed09d3dc9cd8c6e947d4bc5dcf9c6772ff0d3d. PR #59 merged at 319c5dd96b433aa47f8f32747b5f52ca4b376a7c."
---

# Onset detection skill #36 implementation and review

## Summary

**Task outcome:** COMPLETE

Gauge gave a technical GO on `34ed09d`. Skill #36 merged
in PR #59 at `319c5dd`.
[Gauge review](https://github.com/Kisuul/KestrelGaming/pull/59#pullrequestreview-6081285859) · [Merged PR #59](https://github.com/Kisuul/KestrelGaming/pull/59)

The [skill](../../../../../skills/audio-onset-detection/SKILL.md)
defines the event, measures positive spectral flux and weighted RMS
rise, and times accepted peaks. The reference preserves unavailable
warm-up, contributing bins, the selected frame, the event estimate,
and both earliest and observed data boundaries. Beat tracking can
use the original novelty curve.
[Contract](../../../../../skills/audio-onset-detection/references/ONSET_DETECTION_CONTRACT.md) ·
[Research handoff](2026-11-21-audio-onset-detection-research-r01.md) ·
[Research PR #49](https://github.com/Kisuul/KestrelGaming/pull/49)

The small PCM path reuses the shared STFT. The calibrated-frame path
supports wider grids with bounded streaming history. The peak picker
uses the nominal frame center for its estimate and the full right
flank for its earliest ready boundary. Event matching uses exact
doubled samples and an inclusive tolerance.

## Evidence

- Structural validation, the Markdown link and anchor check, and
  all 967 local repository tests passed. The 32 added tests include
  invalid-input recovery, exact peak separation, near-limit arithmetic,
  true state changes across epochs, and 12,544 matching cases checked
  against exhaustive assignments. Thirteen deliberate faults failed
  their targeted tests.
  [Regression checks](../../../../../tests/test_audio_onset_detection_reference.py)
- The independent SciPy FFT and direct DFT checks covered 497 amplitudes,
  28 exact frame centers and RMS levels, and 21 supported score pairs.
  The maximum STFT amplitude error was $1.64\times10^{-15}$ against
  SciPy. Maximum flux error was $1.42\times10^{-14}$. The five tone
  changes agreed with analytic flux within $8.35\times10^{-14}$.
  NumPy 2.3.5 and SciPy 1.17.0 were used for these local checks.
- The wide impulse at 4440 gave center 4319.5 and earliest readiness
  5280. Three callback partitions gave the same 27 points above
  origin $2^{60}+37$. The observed release offsets were 7200, 5280,
  and 5808. The 5279 prefix gave no confirmed peak. The 80 ms attack's
  largest weighted RMS rise had center 6479.5. The vibrato fixture's
  95th-percentile flux fell from 0.097353 to 0.031076 with radius one.
  [Fixture definitions](../../../../../tests/fixtures/AUDIO_ONSET_DETECTION_GOLDENS.md)

## Next action

Use the [current curriculum ledger](2026-11-17-audio-curriculum-status-r01.md) for the next module.

### Review plan at submission

Replay the impulse at the two readiness prefixes. Check the placement
of the center and the first ready boundary. Replay the slow attack
and state which point the application should label. Use the soft
neighbor fixture to explain the missed spectral rise when the
earlier maximum comes from the held tone. Check the plateau and
inclusive separation, and verify one-to-one event matching with
a case where nearest-first loses a feasible pair.

Measure accuracy on held-out annotated
audio before selecting a field threshold. Measure dispatch latency
on the target host if there is a delivery deadline.

## Revisit when

The event definition, input tap, grid, frequency-neighbor filter,
peak rule, latency budget, or evaluation interval changes.
