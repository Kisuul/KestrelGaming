---
schema: 1
id: 2026-11-16-audio-program-loudness-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: archived
evidence: observed
author: Kestrel
created: 2026-11-16
updated: 2026-11-17
sources: "Owner assigned audio skill 20 on 2026-11-16. Audio PR 2 base fbd88c658c4f0d5e73c14493827b8b0150a841b5, implementation 9543a4b9c490556ec89e51135643920e33feafa8. Python 3.12.14 ran 31 focused and 482 repository tests. EBU Loudness Test Set v5.0 original files for Tech 3341 cases 1-14 and independent libebur128 1.2.6 and FFmpeg 7.1.5-0+deb13u1 integrated-loudness comparisons."
---

# Programme loudness skill #20 review handoff

## Summary

**Archive note (2026-11-17):** #20 `audio-program-loudness` is now part of the owner-accepted 23/73 curriculum. The pending-review wording and recorded test evidence below reflect this handoff's original implementation checkpoint; do not use it as a current assignment. See the [current curriculum status](2026-11-17-audio-curriculum-status-r01.md).

**Task outcome:** PARTIAL

The skill, reference, tests and offline fixture checks are complete.
Independent review and integration are pending.

Implement `audio-program-loudness` from the [research and frozen test matrix](2026-11-14-audio-program-loudness-research-r01.md).
The work is on `skills/audio-program-loudness-2026-11-16`, derived from
`fbd88c658c4f0d5e73c14493827b8b0150a841b5` on
`skills/audio-dsp-core-foundation-2026-11-03`. The review covers one module.
[Implementation commit](https://github.com/Kisuul/KestrelGaming/commit/9543a4b9c490556ec89e51135643920e33feafa8)

The child branch proposes a skills catalog entry. The coordinator reconciles
that entry and credits skill #20 in the canonical ledger after integration.
The branch remains subject to the [owner's curriculum merge gate](../2026-11-04-audio-curriculum-full-completion-gate-r01.md).

## Evidence

- The [skill entrypoint](../../../../../skills/audio-program-loudness/SKILL.md)
  routes M, S and I decisions. The contract pins BS.1770-5 Annex 1 at 48 kHz,
  Tech 3341 v4 time scales and R 128 v5 delivery guidance. The Python
  reference accepts explicit mono, stereo, 5.0 and 5.1 speaker labels.
- The implementation preserves IIR and window state across callbacks, uses
  strict gates, recomputes I from complete block history, and distinguishes
  silence, under-gate blocks and insufficient data. Readout defaults to 10 ms
  for M/S to resolve the EBU offset tests. I uses the fixed 100 ms block grid.
  It uses scaled RMS reductions for extreme amplitudes and atomic rejection
  for invalid PCM or arithmetic. Subnormal filter and RMS behavior remains
  subject to binary64 resolution.
- The [fixture ledger](../../../../../tests/fixtures/AUDIO_PROGRAM_LOUDNESS_OFFICIAL_GOLDENS.md)
  records the original ZIP hash, file results and tolerance. Test sequences
  © EBU. The original case 6 WAVEEX RIFF length omits its last frame. The
  first checker run exposed the discrepancy. The verified checker reads the
  final frame from the original data without rewriting the WAV.

| Check | Observed result | Scope |
| --- | --- | --- |
| `python3 -m unittest discover -s tests -p 'test_audio_program_loudness_reference.py' -v` | 31 passed | Synthetic EBU fixtures, independent filter/energy checks, limits, sample indexes above 2^53, gate reclassification and failed-chunk recovery |
| `python3 -m unittest discover -s tests -v` | 482 passed | Local Python 3.12.14 repository suite, including 31 new tests |
| `python3 tools/validate_seed.py` and `git diff --cached --check` | Passed | Local structure and staged diff |
| `check_ebu_loudness.py` with the original EBU v5.0 ZIP | 53/53 files passed, maximum error 0.046486 LU | Cases 1–14, including offline per-segment maxima for live cases 11 and 14 |
| libebur128 1.2.6 and FFmpeg 7.1.5-0+deb13u1 `ebur128` | Max I differences 9.363e-11 LU and 0.006859 LU | Same nine original files for cases 1–8, including both case 6 versions |

The evidence covers measured values at the supported sample rate and
layouts. Full EBU Mode also needs true peak, LRA and device workflow tests.
Separate ITU BS.2217 corpus testing and an agent with/without-skill trial
remain open. The [fixture ledger](../../../../../tests/fixtures/AUDIO_PROGRAM_LOUDNESS_OFFICIAL_GOLDENS.md)
provides the reproduction commands and identifies which test values came
from the publications.

## Next action

Review steady tone and dynamic programme readings, strict gate boundaries,
the PCM layout and tap contract, atomic rejected pushes, and the distinction
between offline M/S/I and full EBU Mode. Check the child PR's GitHub Actions
result. After reviewed integration into the audio branch, rerun the combined
checks and update the single [canonical roadmap](2026-11-03-audio-skills-roadmap.md).

## Revisit when

The child PR is reviewed or integrated, source editions change, the ITU
corpus or agent routing is exercised, or a new rate, layout or deployment
claim needs support.
