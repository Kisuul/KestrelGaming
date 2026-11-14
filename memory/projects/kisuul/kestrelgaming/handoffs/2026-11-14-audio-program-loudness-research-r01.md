---
schema: 1
id: 2026-11-14-audio-program-loudness-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: ChatGPT
created: 2026-11-14
updated: 2026-11-14
sources: "Primary-source research on 2026-11-14: ITU-R BS.1770-5 (11/2023) Annex 1, 3, 4, EBU R 128 v5 (11/2023), EBU Tech 3341 v4 (11/2023) Sections 2.1-2.9 and Table 1, EBU Loudness Test Set v5.0, ITU-R BS.2217 compliance test files; live Kisuul/KestrelGaming PR #2 at 435a3b10c6e23cca2aba4712fb03fd148d65a13a, 19 developed of 73, 54 pending. Independent arithmetic counterexample computed separately; no code or agent-efficacy trial executed."
---

# Skill 20 research — audio programme loudness (research only)

## Summary

**Task outcome:** COMPLETE

Research complete; **audio-program-loudness is NOT implemented, indexed as a skill or counted**. Observed audio [PR #2](https://github.com/Kisuul/KestrelGaming/pull/2) is open and unmerged at \`435a3b10c6e23cca2aba4712fb03fd148d65a13a\`, with **19/73 developed, 54 pending**. The [owner's full 73-skill merge gate](../2026-11-04-audio-curriculum-full-completion-gate-r01.md) still controls final integration. This file and the project memory index are the only intended changes in the research pass.

**Proposed implementation scope:** A clearly bounded **ITU-R BS.1770-5 (2023), Annex 1** programme loudness skill (mono, stereo and defined 3/2 channel-bed combinations; correctly labelled LFE excluded), with **EBU R 128 v5 / Tech 3341 v4** as the initial verification/usage profile. Prefer a fully verified **48,000 samples/s** reference first, using the exact published K-filter coefficients; additional rates need properly designed and independently verified coefficient sets, not reused 48 kHz numbers. Declare the profile, source tap, PCM/reference scale, ordered speaker channels, epoch and half-open sample range. Advanced channel-based, object-based and scene-based systems use different annexes/considerations; they are **NOT** silently covered by an Annex 1-only implementation.

**Standards versus usage policy:** ITU-R BS.1770-5 defines the measurement algorithm and no universal -23 LUFS target. EBU R 128 **recommends** -23 LUFS normalization for its programme workflow. R 128 v5 allows ±1.0 LU for cases such as live work and ±0.2 LU in QC workflow implementation; these are **not** the ±0.1 LUFS test-signal accuracy requirements in Tech 3341 Table 1. "LUFS" (EBU) and "LKFS" (ITU) are numerically equivalent absolute units; **LU** is a difference relative to a declared target, e.g. 0 LU = -23 LUFS **only in the stated EBU reference**. Do not confuse digital dBFS sample peak, dBTP reconstructed peak, LUFS loudness, VU, historical PPM or physical SPL.

## Evidence

### Primary standards and compliance fixtures (editions verified 2026-11-14)

1. **[ITU-R BS.1770-5 (11/2023)](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I%21%21PDF-E.pdf)**, in force per [ITU version catalogue](https://www.itu.int/rec/R-REC-BS.1770/en): Annex 1 defines K-weighting, gated loudness and channel weights for up to five main channels, excludes LFE; Annex 3 deals with advanced channel configurations, Annex 4 object-based programmes, and Annex 2 discusses a distinct **true-peak** method. The primary document notes that subjective loudness estimation is not exact perception.
2. **[EBU R 128 v5.0 (Nov 2023)](https://tech.ebu.ch/files/live/sites/tech/files/shared/r/r128.pdf)** and [publication history](https://tech.ebu.ch/publications/r128): use -23 LUFS normalisation target; integrated gated programme loudness in the whole-programme context; distinguish Maximum True Peak, LRA and M/S quantities; prescribe separately bounded workflow tolerances. Do not extrapolate this target to every platform.
3. **[EBU Tech 3341 v4 (Nov 2023)](https://tech.ebu.ch/docs/tech/tech3341.pdf)**: Section 2 defines EBU Mode. **Momentary M = 400 ms sliding rectangular, ungated; Short-term S = 3 s sliding rectangular, ungated; Integrated I = programme-duration with BS.1770 two-stage gate.** Live meters must update S at least 10 Hz and I at least 1 Hz; the M/S values are NOT further attack/release smoothed. Incomplete final integrated gating blocks are discarded; live I must recalculate the two-stage gate from stored block values as more programme arrives. Full EBU Mode additionally specifies LRA/true peak and presentation; an integrated-only educational oracle is NOT a complete EBU Mode instrument.
4. **[EBU Loudness Test Set v5.0](https://tech.ebu.ch/publications/ebu_loudness_test_set)**: official 70-file set (2016); test material is downloadable under EBU terms, **not downloaded or executed during research**. Tech 3341 Table 1 includes reproducible synthetic tone cases and actual programme tests, plus separate true-peak/LRA cases.
5. **[ITU-R BS.2217 compliance test files](https://www.itu.int/oth/R1102000001)**: separate official ITU reference corpus; inspect exact versions, permissions and expected outputs before importing; **not executed**.
6. **[EBU Tech 3343 production guidance](https://tech.ebu.ch/docs/tech/tech3343.pdf)**: explains why foreground-based programme matching uses a relative gate and why averaging displayed dB values is wrong. Context only; the normative algorithmic math remains BS.1770 Annex 1.

### Mathematical contract before code: K-weighting and block energies

**Per channel** apply the two-stage K weighting: a high-frequency shelving pre-filter followed by the RLB high-pass, continuously across sample and callback boundaries. Annex 1 provides these **48 kHz coefficients**, using the difference-equation convention H(z)=(b0+b1 z^-1+b2 z^-2)/(1+a1 z^-1+a2 z^-2). A renderer with an alternative feedback sign convention must translate them explicitly:

| Stage | b0 | b1 | b2 | a1 | a2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Shelf (Table 1) | 1.53512485958697 | -2.69169618940638 | 1.19839281085285 | -1.69065929318241 | 0.73248077421585 |
| RLB high-pass (Table 2) | 1.0 | -2.0 | 1.0 | -1.99004745483398 | 0.99007225036621 |

The coefficients are not a valid arbitrary-rate template. Require verified frequency response and independent signal tests at 44.1, 96 or 192 kHz before expanding rate support. Preserve state per channel, including at chunk boundaries; a seek, sample-rate change or discontinuity must use an explicit epoch/reset policy.

**Per complete 400 ms block with 75% overlap** (nominally 100 ms hop), calculate each filtered channel's mean-square energy \`z_ij\`; apply the **power** weights **G_L=G_R=G_C=1.0, G_Ls=G_Rs=1.41**, LFE ignored, then loudness \`l_j = -0.691 + 10 log10(sum_i G_i*z_ij)\` in LKFS/LUFS. Interpret the Annex 1 997 Hz, unit-peak sine on a single L/C/R main channel as approximately **-3.01 LKFS**, not 0. A two-channel in-phase tone adds *power* and has a roughly 3 LU greater programme reading than the one-channel counterpart; it is NOT a sum-then-square mono downmix. ITU explicitly cautions that this programme estimator is not generally suitable for estimating subjective loudness of isolated pure tones; the tones are calibration and test fixtures, not a comprehensive perception model.

Apply the **two independent strict thresholds**:
- Absolute gate: include only complete blocks with \`l_j > -70 LUFS\` to find absolute-gated loudness. In energy terms, average filtered/channel-weighted powers, then convert to the log unit; do NOT average the block dB values.
- Relative gate: threshold \`absolute_gated_loudness - 10 LU\`; final pass includes only complete blocks whose loudness is **strictly above both** the relative and absolute thresholds. Reaverage retained energies, not logged readings. As the programme changes, the threshold can change and previously accepted blocks can become excluded. Do not silently treat the second gate as a fixed -10 LUFS absolute threshold.

Distinguish (a) **insufficient data** to form a complete gating block from (b) **no blocks above the absolute threshold** (silence/under-gate), and from (c) an externally imposed display floor; do not call all three 0 LUFS or silently invent an output. The chosen API should document unavailable versus -infinity representations and preserve zero-energy provenance.

### Independent arithmetic counterexample (NOT an executed audio-file test)

Given **already K-weighted, channel-weighted block loudness values** [-23, -40, -23, -40] LUFS of equal 400 ms window length, independent math gives:
- Arithmetic mean of displayed loudness values: **-31.5 LUFS** (WRONG estimator).
- Convert each to energy \`E_j = 10^((L_j + 0.691)/10)\`, average, then convert back: **-25.9244999643 LUFS** after absolute gate.
- Relative gate: **-35.9244999643 LUFS**; excludes the two -40-LUFS blocks.
- Energy mean of remaining two -23-LUFS blocks: **-23.0000000000 LUFS**.

This is an analytically checkable **gate arithmetic fixture**. These are hypothetical precomputed block levels, not a realizable continuous PCM record proven to produce those overlapping blocks. The implementation must also pass independently generated continuous-sample tests, not only this simplified test.

### Pre-registered Tech 3341 Table 1 acceptance matrix

The following examples are published **expected values and tolerances**, NOT measured results from any new Kestrel code. A stereo 1 kHz sine is applied **in phase to both channels**, at the stated **per-channel peak** dBFS. Freeze these requirements before fitting any filter:

| Case | Signal | Expected response / accepted tolerance |
| --- | --- | --- |
| 1 | 20 s stereo tone at -23.0 dBFS per-channel peak | M, S, I = **-23.0 +/-0.1 LUFS** (0.0 +/-0.1 LU relative to -23 reference) |
| 2 | As #1 at -33.0 dBFS per-channel peak | M, S, I = **-33.0 +/-0.1 LUFS** |
| 3 | 10 s -36; 60 s -23; 10 s -36 (same stereo tone) | Integrated **-23.0 +/-0.1 LUFS** |
| 4 | 10 s -72; 10 s -36; 60 s -23; 10 s -36; 10 s -72 | Integrated **-23.0 +/-0.1 LUFS** |
| 5 | 20 s -26; 20.1 s -20; 20 s -26 | Integrated **-23.0 +/-0.1 LUFS** |
| 6 | 20 s 5.0 tone, L/R -28, C -24, Ls/Rs -30 dBFS peaks | Integrated **-23.0 +/-0.1 LUFS** |

Tech 3341 additionally includes M/S transition tests (cases 9–14), authentic programme recordings (7–8), and independent true-peak cases (15–23). Claims about full "EBU Mode" require a broader suite; a first integrated-only skill may claim that it matches **the tested integrated subset**, never that it covers every EBU requirement.

A unit sine at 0 dBFS peak is **not** a 0 LUFS stereo reference. Do not assume the -23 target is a filter design constant, or that the LUFS reading of a loudness-normalized programme bounds its sample/true peaks.

### Engineering risks, state contracts, adversarial checks

- **Filter:** wrong coefficient sign, wrong order or stage gain, zeroed state on each callback, coefficient reuse at wrong sample rate, nonfinite/overflow/underflow, silence and subnormal input. Test using published coefficients and independent analytic/SciPy or libebur128 comparisons; an implementation matching itself is not an independent oracle.
- **Timebase:** exact sample-index windows and hop, 75% overlap, first full window, rounded windows at nonintegral rates, 100 ms hop at 48 kHz = 4800 frames, 400 ms block = 19200 frames; trailing incomplete block excluded. Independent chunk schedules and exact indices >2^53. No silently inserted zeros for dropped frames or timestamp discontinuities.
- **Channels:** explicit identity/order, surround 1.41 *power* factor, completely exclude LFE, mono/stereo/5.0/5.1 bed with clear separation of the LFE. Anti-phase L/R must not cancel when powers are summed. Unknown/discrete channel maps must fail closed until labeled. Annex 3 multichannel elevation/azimuth weight tables and Annex 4 objects are different profiles and outside first scope.
- **Gating:** thresholds strict ">", -70 and -10 relative, blockwise two-pass energy mean, changing relative threshold and retroactive reclassification, all-silent signal, below -70 continuous signal, start <400 ms, aborted epoch and pause/resume, partially complete last block. Do not implement "sum LUFS then divide", sample-wise -70 gate or sample-level 10 dB gate.
- **Numeric:** stable filtered-sample squared means and weighted sums, finite-range failures (including mathematically finite output with overflowing intermediate), compensated or scaled accumulation when appropriate; track precision budget separately from EBU +/-0.1-LUFS test tolerance.
- **Boundary of skill:** \`audio-loudness-range\` remains a **separate module** using Tech 3342; true peak belongs to an independent algorithm and the existing \`audio-true-peak\` reference in Kestrel is explicitly experimental. Sample peak, quasi PPM and VU skills answer different questions.
- **Usefulness, still NOT demonstrated:** preregister held-out agent questions about choosing integrated vs momentary/short-term, handling an LFE-only signal, correcting channel assignments, understanding why a long silent segment does not imply -inf programme loudness, identifying dBFS vs LUFS vs LU vs dBTP, and explaining why audio with matched LUFS can still clip. A/B evaluate with and without the new skill later; no such trial was run during research.

### Recommended implementation stages, with hard proof gates

1. **Contract and fixed goldens first:** Author \`skills/audio-program-loudness/SKILL.md\` with load triggers, standards scope/version, processing tap, unit/channel/rate/epoch contract and independent EBU test matrix in \`references/PROGRAM_LOUDNESS_CONTRACT.md\`. Preserve historic source tables as *specification data*, not new measured outcomes.
2. **Bounded signal/reference engine:** Define standard-library 48 kHz K-weighting two biquads; explicit channels and power weights; complete overlapping 400 ms blocks and a two-stage gate; sample-clock/state continuity. Separate measurement arithmetic from display formatting, normalization target/gain advice and full EBU Mode features.
3. **Independent adversarial tests:** Validate the analytic block-power fixture, 48-kHz coefficient transfer and filtering, sine calibration, published EBU cases 1–6 where computationally feasible, negative/edge cases and live recalculation behavior. Compare against a *separate* implementation such as [libebur128](https://github.com/jiixyj/libebur128), appropriate FFmpeg \`ebur128\`, and/or official test PCM where available. Specify tool version and tests actually run.
4. **Hostile review:** Try to falsify actual measured results (not just math functions) via stereo phase inversion, LFE-only, loudness near gates, callback changes, format/epoch transition, numerical extremes, pulse- or speech-like dynamics. Do not widen the published tolerances to rescue a failed design. Report any noncompliance prominently in the skill.
5. **Kestrel integration and memory:** Run focused tests, \`python3 tools/validate_seed.py\`, full \`python3 -m unittest discover -s tests -v\`, \`git diff --check\` when available. Save completion and negative evidence using [kestrel-remember](../../../../../skills/kestrel-remember/SKILL.md), update the canonical roadmap **only after verified integration**, and keep umbrella PR #2 open and unmerged until all 73 audio skills and owner approval.

**No reference implementation was written, no official test audio downloaded or executed, and no audio-agent efficacy measurement performed in this research phase.** The analytic four-block exercise is an independent mathematical fixture, not an ITU/EBU conformance test.

## Next action

Prepare bounded implementation from this research handoff. Verify current PR head, that no other agent has claimed \`audio-program-loudness\`, and the present primary-source editions. Start with exact 48 kHz coefficient/filter/time/energy contracts, implement and test against the frozen matrix, perform hostile review and independent oracles, then credit skill #20 only after GitHub CI and coordinator integration. Do not silently broaden an Annex 1 bed reference into immersive/object-based, true-peak or LRA certification.

## Revisit when

ITU/EBU publish revised editions; a new agent claims or integrates this module; official test sequences are downloaded and executed; a different sample-rate design is validated; gating or channel tests expose mismatches; the owner revises completion criteria; or an actual held-out agent-use A/B evaluation is run.
