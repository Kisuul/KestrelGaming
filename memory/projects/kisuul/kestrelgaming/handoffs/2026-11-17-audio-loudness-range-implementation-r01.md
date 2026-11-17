---
schema: 1
id: 2026-11-17-audio-loudness-range-implementation-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: Codex
created: 2026-11-17
updated: 2026-11-17
sources: "Owner assignment for Skill #21. KestrelGaming base fe89ed525854a16e6a22d02d422378cb472c1d92. EBU Tech 3342 v4 §§3–5, Tech 3341 v4 §§2.2 and 2.4 and original EBU v5.0 archive. Local Python 3.12.14 tests and FFmpeg 7.1.5 comparison."
---

# Skill #21 — Loudness Range implementation review

## Summary

**Task outcome:** COMPLETE

Implemented the [agent procedure](../../../../../skills/audio-loudness-range/SKILL.md),
[technical contract](../../../../../skills/audio-loudness-range/references/LOUDNESS_RANGE_CONTRACT.md),
[reference](../../../../../skills/audio-loudness-range/scripts/reference_loudness_range.py)
and [official checker](../../../../../skills/audio-loudness-range/scripts/check_ebu_lra.py).
This completes the implementation assignment and local verification.
Independent adversarial review and acceptance are pending.

The child branch `skills/audio-loudness-range-2026-11-17` starts at
`fe89ed525854a16e6a22d02d422378cb472c1d92`, the PR #19 merge on
`skills/audio-dsp-core-foundation-2026-11-03`. The owner accepted Skill #20
and reported 20/73. PR #2's description and the previous roadmap counts
are historical. Credit Skill #21 through reviewed child integration and
follow the [umbrella merge gate](../2026-11-04-audio-curriculum-full-completion-gate-r01.md).

## Evidence

The adapter uses the Skill #20 short-term path with complete 3 s windows
at 10 Hz. EOF adds 72,000 zero frames through that path. The measurement
keeps the source and analysis end samples, and the 60 s duration flag uses
source frames. The shared EBU checker validates the WAV header before
creating the Skill #20 meter. It still uses the pinned digest and preserves
the WAVE_FORMAT_EXTENSIBLE exception for Skill #20 case 6.

The inclusive −70 LUFS and −20 LU gates feed a half-up order statistic.
The gate reference encloses normalized powers, resolves exact relative
ties with integer arithmetic, and increases precision when the bounds
overlap. The [golden ledger](../../../../../tests/fixtures/AUDIO_LOUDNESS_RANGE_GOLDENS.md)
pins the cases, archive and arithmetic expectations independently of the
reference.

| Tech 3342 case | Target LU | One copy LU | Two copies LU |
| --- | ---: | ---: | ---: |
| 1 | 10 | 10.001105 | 10.001105 |
| 2 | 5 | 4.999373 | 4.999373 |
| 3 | 20 | 19.995064 | 19.995064 |
| 4 | 15 | 14.999274 | 14.999274 |
| 5 | 5 | 4.976616 | 4.972863 |
| 6 | 15 | 14.984602 | 14.958805 |

| Check | Observed result |
| --- | --- |
| `python3 -m unittest discover -s tests -p 'test_audio_loudness_range_reference.py' -v` | 26 focused tests. Includes exact and adjacent gates, percentile ties, independent Decimal oracles, sample timing, partition invariance, and invalid archives. |
| `python3 -m unittest discover -s tests -v` | 528 passed with Python 3.12.14. The suite caught an initial fixture refactor that constructed the M/S/I meter before header validation. The final code restores that validation order and passes the original regression. |
| `python3 tools/validate_seed.py` and `git diff --cached --check` | Passed. |
| `python3 skills/audio-loudness-range/scripts/check_ebu_lra.py ARCHIVE` | Official SHA-256 matched. 12/12 within ±1 LU. Largest absolute error 0.041195 LU. |
| `python3 skills/audio-program-loudness/scripts/check_ebu_loudness.py ARCHIVE` | Same archive. 53/53 within ±0.1 LU, worst error 0.046486 LU. |
| FFmpeg 7.1.5 `apad=pad_dur=1.5,ebur128` on the six original files | One-copy rounded LRA values were 10.0, 5.0, 20.0, 15.0, 5.0, 15.0 LU. This comparison checks the final statistic at FFmpeg's summary precision. |
| Local arithmetic probes, seed 3342 | 1,000 integer-decade histories matched exact rational comparisons. 750 single-candidate near-gate histories matched an independent Decimal-100 comparison. |
| Contract shell example | Passed on Python 3.12.14. |

Verified source blobs are `99904b9c5a6aa02b214711dd5ba97544c72b7c80` for the
LRA reference, `236a67c44e23eac111a25299303e14779bedb2ba` for the LRA checker,
and `063002fea19ac0843b20e430fc8a758dad136d8a` for the shared fixture checker.
The archive is an external test resource. Only the results and checker are
part of this branch. [EBU test material](https://tech.ebu.ch/publications/ebu_loudness_test_set)

## Next action

Review the power enclosures and exact-tie proof, the relative gate at
adjacent binary64 inputs, and complete-window timing at both ends of a file.
Replay the original archive against the proposed revision. The implementation
keeps the full programme history and raises `ArithmeticError` when a gate
decision remains unresolved after 1,024 decimal digits. The evidence covers
the offline 48 kHz channel-bed reference and LRA cases. Real-time behavior,
full EBU Mode conformance, and the effect of the skill on agent decisions
require separate evidence.

## Revisit when

Recheck the exact branch and fixtures when adversarial review starts,
when a standard or dependency changes, or when the coordinator integrates
the skill and updates the curriculum ledger.
