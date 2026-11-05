---
schema: 1
id: 2026-11-05-audio-ppm-metering-completion-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: ChatGPT
created: 2026-11-05
updated: 2026-11-05
sources: "User 2026-11-05 requested implementation following PPM research; EBU Tech 3205-E 1979 Table 2 source and ITU-R BS.645-2 1992; audio branch implementation 4ee7e72c0457d9a71d35b799c0b7cc62374b74e0; GitHub Actions 42004049812 passed structural validation and all 451 repository tests (32 new); optional local NumPy 2.3.5 SciPy 1.17.0 seed 20261105 24 cases 15186 sample values, max 4.574e-14 dB; known EBU flatness violation preserved."
---

# Skill 19 — PPM metering research-to-implementation completion (bounded, nonconformant)

## Summary

**Task outcome:** COMPLETE

This means the **audio-ppm-metering engineering skill and bounded, falsifiable reference task** is implemented, tested and indexed. It does **not** mean the reference is a certified EBU Type IIb / IEC 60268-10 meter or ready for production use. The instrument's **31.5 Hz–16 kHz frequency response fails EBU Tech 3205-E §2.3** and is explicitly represented as failed compliance in code, tests and documentation.

**Observed implementation:** [audio PR #2](https://github.com/Kisuul/KestrelGaming/pull/2), branch `skills/audio-dsp-core-foundation-2026-11-03`, commit `4ee7e72c0457d9a71d35b799c0b7cc62374b74e0`. The [running roadmap](2026-11-03-audio-skills-roadmap.md) now counts **19/73 developed, 54 pending**. Owner explicitly [forbids merging the umbrella PR to main until all 73 are completed and authorizes final acceptance](../2026-11-04-audio-curriculum-full-completion-gate-r01.md).

## Evidence

### Research-first benefit and falsifiable implementation

The [pre-implementation research record](2026-11-05-audio-ppm-metering-research-r01.md) already distinguished IEC Type I, BBC Type IIa, historic EBU Type IIb, IEC digital peak indicators and modern EBU R128; preregistered 1979 Tech 3205 Table 2 burst levels and ancillary timing/flatness requirements; and rejected the naive single-pole attack math. The implementation thus began with **external acceptance data**, not user-interface intuition or post-hoc target selection.

[Primary skill procedure](../../../../../skills/audio-ppm-metering/SKILL.md), [full model contract](../../../../../skills/audio-ppm-metering/references/PPM_CONTRACT.md) and [bounded stdlib Python reference](../../../../../skills/audio-ppm-metering/scripts/reference_ppm.py) implement an expressly labelled **legacy Type IIb normal-mode burst FIT, PARTIAL**. Detector: full-wave magnitude scaled by π/2 for well-sampled sines, two lowpasses of 1.39366241 ms and 9.23475167 ms with 0.389565905 fast weight, and a separate log-linear 24 dB / 2.8 s release envelope. This is **chosen implementation math fitted to the standard's published burst targets**, not a normative circuit schematic or independent proof of meeting the full specification.

**Published burst training/verification:** EBU Tech 3205 1979 Table 2 +8dB continuous reference gives isolated burst indications +8 (100 ms at 5 kHz), +6 (10 ms at 5 kHz), +4 (5 ms at 5 kHz), −1 (1.5 ms at 5 kHz), and −9 (0.5 ms at ≥10 kHz with five cycles), with tolerance ±0.5 / 0.5 / 0.75 / 1.0 / 2.0 dB. These expected values are frozen separately in [reference fixtures](../../../../../tests/fixtures/AUDIO_PPM_EBU_1979_GOLDENS.md). The fitted reference passed the given ranges at rates 44.1/48/96/192 kHz and multiple carrier phases; this verifies **fit plus sample-rate/phase checks** rather than external instrument conformance. Additional 10 ms integration, +12→−12 dB in 2.8 s, +9 onset/overswing, 1 kHz TEST 0.775 V RMS calibration, unidirectional pulse, polarity, level linearity and channel/epoch invariants are tested.

### Actual executed checks

- **Locally:** Python 3.13.5 `python -m unittest discover -s /mnt/data/ppm_skill/tests -q` passed **32 tests** (tested package). The standalone fixture was corrected from the *finite* 1e308 times π/2 to a true overflowing 1.5e308 input after an expected-red check; production source guards input overflow and tiny-underflow nonzero signals atomically.
- **Optional independent SciPy arithmetic checker:** `python skills/audio-ppm-metering/scripts/check_scipy_ppm.py --seed 20261105 --cases 24` (local NumPy 2.3.5/SciPy 1.17.0) passed **24 cases, 15,186 sample comparisons**, maximum absolute error **4.574118861455645e-14 dB**. SciPy lfilter plus the vectorized max-of-decayed-signal identity differ from the reference's sample loop. **Agreement concerns arithmetic of the *same fitted model*, not historical metrological correctness.**
- **Published implementation and GitHub verification:** `4ee7e72c0457d9a71d35b799c0b7cc62374b74e0`; [Actions 42004049812](https://github.com/Kisuul/KestrelGaming/actions/runs/42004049812) passed structural checks and **451 full-repository tests**, increased from 419 by 32. All seven published source/docs/test files were independently checked as identical to locally tested Git blob SHA1s before committing; `skills/INDEX.md` was updated.
- **Explicit negative finding — NOT compliant:** At 48 kHz a 400 ms steady 31.5 Hz sine indicates about **+2.15 dB**, and a 16 kHz sine about **−0.82 dB**, compared to ~+0.02dB at 5 kHz (equal peak amplitude). EBU Tech 3205-E §2.3 permits **±0.3 dB across 31.5 Hz–16 kHz**. The suite's `test_low_frequency_flatness_conformance_is_KNOWN_TO_FAIL` preserves this red **conformance finding while the suite remains green as a test of an honest limited implementation**. The reference always reports `standards_conformance=False`, never promises a certified device.
- **Not checked:** Complete paywalled IEC 60268-10 requirements, real analogue inputs, physical temperature/impedance/distortion/overload compliance, arbitrary programme test corpus, realtime CPU/callback deadlines, full frequency/phase continuum, actual agent with/without-skill effectiveness. Slow mode, Type I, BBC Type IIa and R128 loudness are expressly unsupported.

## Next action

**Next counted skill:** `audio-program-loudness`, with independent edition-specific ITU-R BS.1770 / EBU R128 requirements, K-weighting, channel energy weights, absolute/relative gating, reference calibration, true-peak boundaries and adversarial external golden values. `audio-loudness-range` and `audio-envelope-dynamics` remain in the levels family. Parallel assignments require current audio-branch claim checks and reviewed child integration; do not reimplement VU/PPM as new pending skills.

**Separate non-creditable remediation:** The fitted Type IIb reference requires a new frequency-flat design and a complete historical compliance audit **before** it could be described as EBU/IEC compliant. Preserve the failure, not a widened tolerance. Existing PSD/STFT intermediate-overflow audit and actual audio-agent A/B usefulness trial also remain open. Nothing in this handoff starts those tasks.

**Do not merge umbrella PR #2 to main.** This count is a stage snapshot; validate the final memory-only commit CI independently.

## Revisit when

A future Type IIb design actually passes frequency response; IEC text or an independent calibrated physical instrument is available; source standards change; an agent-use A/B evaluation is run; new skills integrate; the owner revises the 73-module commitment; or the final PR #2 audit starts.
