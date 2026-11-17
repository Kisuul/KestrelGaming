---
schema: 1
id: 2026-11-16-audio-program-loudness-gauge-correction-r02
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: Kestrel
created: 2026-11-16
updated: 2026-11-16
sources: "Owner's Skill 20 correction request and supplied Gauge hostile audit/reproducer, reviewed PR19 head dc272e8ebc60f38078c98d99bd099a66645842f2. Corrected reference Git blob fb596cb5da59bc98a053b87a495dd625fff84876; checker Git blob 0a3367e6eda6eca7bf1b0e091d2171a3566638d0. Python 3.12.14 local checks and pinned original EBU v5.0 archive replay."
---

# Skill 20 — Gauge audit correction handoff

## Summary

**Goal:** Repair G-20-01/02 gate boundaries and G-20-03 fixture identity in
existing [PR #19](https://github.com/Kisuul/KestrelGaming/pull/19), preserving
48 kHz M/S/I, streaming state, channel semantics and published tolerances.

**Task outcome:** COMPLETE

The correction implementation and local verification are complete; fresh
Gauge acceptance and coordinator integration remain pending.
This record does not mark Skill 20 accepted or change the curriculum count.

**Target:** `Kisuul/KestrelGaming`, PR branch
`skills/audio-program-loudness-2026-11-16`, base
`skills/audio-dsp-core-foundation-2026-11-03`. Audited and fetched PR head was
`dc272e8ebc60f38078c98d99bd099a66645842f2`, matching the supplied audit.
Work was prepared on local `fix/skill20-hostile-audit`, directly from that
commit. The source blobs in frontmatter identify the actual tested code,
without requiring this handoff to predict its own commit. Inspect Git history
and final PR-head CI for the containing revision and synchronization status.

The shared contract and protocols were initially loaded at main `504da1d`,
then current branch instructions, contribution guidance, numerical-analysis,
math-verification, recall and remember procedures were consulted. No individual
character was selected. Two delegated agents assisted with fixture correction
and a read-only numerical review; this does not replace Gauge's independent
acceptance audit.

## Evidence

### Root causes and decisions

- **G-20-01:** rounding normalized squares, the mean, square root and
  `sqrt(10)` division moved the relative boundary. For Gauge's exact roots
  `(0.011456406447987386, 0.03771438262924999, 0.04882472278710498)`, the
  imported original source kept 3 blocks and returned −29.510031739085374
  LUFS. The corrected source and Decimal oracle keep indices `(1, 2)` and
  return −27.896351716735627 LUFS. Comparing exact rational squared roots
  via `10*N*r_j**2 > sum(r_i**2)` removes this discontinuous decision error.
  No epsilon or inclusive equality is introduced.
- **G-20-02:** evaluating the published decimal threshold in binary64 made
  the old constant about 4.15 ULPs too large. The exact threshold
  `10**(-69309/20000)` lies strictly between hex roots
  `0x1.670bbcee4aad0p-12` and its immediate successor. Strict comparison to
  the lower endpoint is equivalent for binary64 inputs. An independent
  exact-integer certificate proves the bracket; Decimal100/160 checks both
  neighbors and the old constant. The old constant now correctly yields `ok`.
- **G-20-03:** official runs hash the archive before ZIP parsing, report the
  observed SHA and official mode, and reject mismatches. The pinned digest
  is `9cc500b4df83f7c21855c74dce795ef5209a752bf884253ae57d0ce512efb062`.
  The checker validates 53 required names, duplicates/encryption, bounded
  archive/member/expanded sizes and PCM durations. The original WAVEEX
  last-frame workaround is preserved and regression-tested.

The [precision contract](../../../../../skills/audio-program-loudness/references/PROGRAM_LOUDNESS_CONTRACT.md#gate-precision-policy)
limits exact gate membership to supplied roots **after binary64 conversion**.
Filtering, weighted RMS summaries, LUFS outputs and the diagnostic relative
threshold remain rounded. No exact PCM-to-LUFS or subjective-perception claim
is made. BS.1770 is a standardized measurement model, not universal subjective
loudness or acoustic SPL.

### Executed checks

Commands below ran from the repository root with Python 3.12.14. Local scratch
paths are environment-specific and not shared memory or distributed fixtures.

| Command/check | Observed result | Limits |
| --- | --- | --- |
| `git show dc272e8:skills/audio-program-loudness/scripts/reference_program_loudness.py` then supplied `hostile_gate_repro.py` importing that exact file | Exit 1; 2 mismatches (relative count and absolute status) | Original source, not a formula shim |
| Supplied `hostile_gate_repro.py skills/audio-program-loudness/scripts/reference_program_loudness.py` | Exit 0; zero mismatches; Gauge I −27.896351716735627 LUFS | Independent Decimal100 exact-input oracle, block-root API |
| `python3 -m unittest discover -s tests -p 'test_audio_program_loudness_reference.py' -v` | 37 passed | Independent Decimal100/160 survivor identities and outputs, integer bracket proof, strict ties/neighbors, scaled/range extremes, gate recomputation, existing channel/epoch/stream regressions |
| `python3 -m unittest discover -s tests -p 'test_audio_program_loudness_fixtures.py' -v` | 14 passed | Synthetic archive/hash/parser/error tests, actual synthetic WAVEEX last frame; not official compliance evidence |
| `python3 -m unittest discover -s tests -v` | 502 passed | Repository tests, including 51 loudness/reference/parser tests; no physical-device claim |
| `python3 tools/validate_seed.py` and `git diff --check` | Passed | Structure, links, metadata and whitespace, not mathematical certification |
| `python3 skills/audio-program-loudness/scripts/check_ebu_loudness.py /workspace/work/skill20/ebu-loudness-test-setv05.zip` | Exit 0; official pinned hash matched; 53/53 files passed; max absolute error 0.046486 LU | Original EBU v5.0 cases 1–14, ±0.1 LUFS; both case 6 layouts passed |

The 91,631,421-byte ZIP was obtained from the EBU publication's official file
link using curl after urllib requests returned HTTP 403. It is outside the
repository and must not be committed or redistributed. First official replay
stopped at case 8 because the initial 180-second resource cap was too short.
Inspection of the verified archive found a 246.358-second case 8; the final
300-second cap and a 301-second rejection regression were then applied and
the complete official run passed. See the [fixture ledger](../../../../../tests/fixtures/AUDIO_PROGRAM_LOUDNESS_OFFICIAL_GOLDENS.md)
for provenance and interpretation.

A separate seeded exploration (`random.Random(20261116)`, 2,000 independent
pairs `b,c = uniform(.1,10)`, `a = float(sqrt((b*b+c*c)/29))` evaluated with
Decimal160 over exact binary64 `b,c`) compared `(a,b,c)` to the published
power gate. The imported baseline had 643 survivor-count mismatches and the
corrected source had zero. This bounded search is empirical evidence, not a
general proof; the exact comparison algebra supplies the gate argument.
An opposite-rounding-direction case is frozen in the regressions as well.

**Changes:** only this skill's reference, fixture checker, contract/entrypoint,
associated tests/fixture ledger, and this indexed review handoff. The DSP
filter, window timing, channel map, epoch handling and streaming push code
were preserved. No standards edition, acceptance tolerance, curriculum count,
other agent work, PR merge or umbrella merge was changed.

**Persistence at preparation:** local correction for the existing PR branch.
Verify the containing commit on PR #19 and its exact-head Actions result
before treating this as synchronized. The final user response supplies the
confirmed remote SHA/CI if publication succeeds. A PR branch is not main.

## Next action

Gauge and the coordinator should review the exact corrected PR head, rerun
the hostile helper and independent oracles, inspect the absolute-bracket proof,
and verify archive rejection and official corpus provenance. Leave PR #19
and umbrella PR #2 unmerged; preserve the owner's 73-skill completion gate.

**Remaining limits:** exact Fraction decisions add per-query allocation and
integer work while rescanning all history. This remains offline educational
code, not allocation-safe real-time code. Full EBU Mode, LRA, true peak,
physical-device validation, ITU BS.2217 corpus and agent efficacy remain
outside this correction. Historical libebur128/FFmpeg comparisons were not
rerun; the new official corpus pass is separate evidence.

## Revisit when

The PR head, thresholds, binary64 input representation, source editions,
fixture identity, supported rate/layout or deployment scope changes. Recheck
current branch, working tree, authority and CI when resuming.
