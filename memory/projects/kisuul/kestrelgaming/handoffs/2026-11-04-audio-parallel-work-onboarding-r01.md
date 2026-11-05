---
schema: 1
id: 2026-11-04-audio-parallel-work-onboarding-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: ChatGPT
created: 2026-11-04
updated: 2026-11-04
sources: "2026-11-04 stream-buffering skill 304b1cdc1c7275af98892f1ef980e309bfdfaaee passed GitHub Actions 41951059313 (308 repository tests and structural validation, 36 new); prior verified filter-design head d37ffa3e200b9065fafa312ee5f60c9fbc973ba1 had 14/73; owner requires all 73 completed before PR #2 merges."
---

# Audio curriculum — handoff for parallel Kestrel agents

## Summary

**Goal and acceptance criteria:** Coordinate independently authored, rigorously reviewed audio skills until the **entire** 73-module program passes the owner's [completion gate](../2026-11-04-audio-curriculum-full-completion-gate-r01.md). Preserve the single [canonical backlog](2026-11-03-audio-skills-roadmap.md).

**Task outcome:** PARTIAL

The parallel coordination handoff remains active. Separately authorized `audio-channel-mapping`, `audio-filter-design` and `audio-stream-buffering` skills are implemented and verified; **58 modules remain**. This handoff neither assigns nor starts another agent.

**Authorization boundary:** This is a plan, **not** standing authority to write, force-push, merge or deploy. Every agent must verify current user assignment and actual permissions. **Do not merge umbrella PR #2 into main before all curriculum modules are finished and the owner approves.**

**Target repository and branch:** [Kisuul/KestrelGaming PR #2](https://github.com/Kisuul/KestrelGaming/pull/2), `skills/audio-dsp-core-foundation-2026-11-03`; latest verified implementation head `304b1cdc1c7275af98892f1ef980e309bfdfaaee` (308 tests, Actions `41951059313`). Main branch and PR base may change; recheck live refs and read this memory on the audio PR branch.

**Memory revision loaded:** [Running audio handoff](2026-11-03-audio-skills-roadmap.md), [audio independent audit](../2026-11-03-audio-skills-independent-audit.md), [math integration handoff](2026-11-03-audio-math-integration-workorder-r01.md), [Kestrel memory protocol](../../../../../kestrel/MEMORY_PROTOCOL.md), [kestrel-remember](../../../../../skills/kestrel-remember/SKILL.md), and the current skill catalog.

## Evidence

- **Observed:** 15 audio skills are indexed in PR #2 and **58 modules remain** in nine families. GitHub Actions [41951059313](https://github.com/Kisuul/KestrelGaming/actions/runs/41951059313) passed structural validation and **308 repository tests** (36 new stream-buffering cases) at `304b1cd`. Two seeded independent queue oracles verify FIFO and synthetic discontinuity accounting in the new unit suite; no live audio concurrency was exercised. Reference results do not verify host skill activation, production audio performance, calibrated instruments or standard compliance.
- **Observed/source-derived review concerns:** The PSD/STFT reference code squares Fourier magnitudes before normalization, so extreme but finite intermediates can overflow. This is a numerical-range review finding; reproduce it and add bounded/negative regression evidence before calling it fixed. An audio-specific agent-efficacy with/without-skill trial has not been run. Resampling's frequency sweep, device clock and realtime performance remain unverified. `docs/MATH_CURRICULUM.md` retains historically correct 9/64 integration-time wording, which may need a clearly dated status note.
- **User-stated:** All modules must be completed before merging PR #2. No lowering the remaining count simply to satisfy an arbitrary milestone.

### Available, unclaimed work lanes

This table groups the **same 58** named modules already enumerated in the roadmap; it does not create another backlog or assign work.

| Area | Pending | Dependencies and review focus |
| --- | ---: | --- |
| Foundation/numerical DSP | 1 | Numerical stability only; channel mapping, filter design and stream buffering are completed |
| Levels/loudness/dynamics | 5 | VU, PPM, loudness, LRA, envelopes; edition-specific calibration |
| Spectra/frequency domain | 5 | Fractional octave, resolution, descriptors, harmonics, cepstrum; FFT/PSD |
| Oscilloscopes/phase | 8 | Scope, phase, stereo, correlation and group delay; channel semantics |
| Temporal/music | 8 | Onsets, tempo, pitch, harmony and event timing; uncertainty |
| Quality/distortion | 8 | Test signals, THD/IMD, SNR, clipping, codecs, dropout; known-bad vectors |
| Acoustics/spatial | 8 | SPL, microphone/room/impulse, surround and latency; instrument evidence |
| Speech/perception | 8 | Speech, VAD, psychoacoustics and intelligent analysis; dataset claims |
| Validation/visualization/infrastructure | 7 | Independent checks, uncertainty, UI integrity, realtime and provenance |
| **Total pending** | **58** | **One canonical module list in the running roadmap** |

An optional **audit lane** can investigate PSD/STFT numerical extremes and design audio agent behavioral trials without counting itself as a new audio curriculum module.

## Parallel workflow and safe handoffs

1. **Read first:** `AGENTS.md`, `KESTREL.md`, `kestrel/MEMORY_PROTOCOL.md`, `kestrel/STATE_PROTOCOL.md`, `kestrel/PERMISSIONS.md`, `kestrel/VERIFICATION.md`, this handoff, the owner decision, the **current branch** roadmap, and relevant `skills/INDEX.md` entries. Validate the actual GitHub PR head and CI. The shared mathematics skill set is optional, task-conditional support rather than a wholesale imported curriculum.
2. **Claim a bounded module with real authorization.** Record agent/task scope, start SHA, expected paths, acceptance checks, overlap dependencies and exclusions in a separate, indexed Kestrel handoff. Proposed lanes are not locks or evidence someone started.
3. **Work separately.** Make a uniquely named branch/worktree from the **latest audio PR #2 head**. Prefer a child PR **targeting the audio branch**; do not use the final main merge as your integration strategy. Do not force-push, bypass review or overwrite another agent's work.
4. **Keep ownership narrow.** Agent edits focus on its own `skills/audio-<topic>/`, reference/tests and assigned handoff. Other agents' work, governing contracts, merged math sources, applications and already-accepted tests are out of scope unless separately authorized.
5. **Protect shared indexes.** Agents can propose `skills/INDEX.md` changes, but the integrating coordinator reconciles and serializes updates to that index and the canonical audio roadmap against the latest remote state. Keep test and proof evidence in task-specific records; no simultaneous replacement of the running handoff.
6. **Build falsifiable acceptance evidence.** Define real input/clock/channel/reference conventions, derive expected results separately from the code, test negative cases and metamorphic properties, cite standards with editions and qualification, and disclose what remains unverified. Run focused tests, `python3 tools/validate_seed.py`, `python3 -m unittest discover -s tests -v` and `git diff --check` wherever possible; never claim an unrun check.
7. **Deliver a reviewable child handoff.** Record branch, exact SHA, affected files, test results, sources, limitations, rejected approaches and COMPLETE/PARTIAL/BLOCKED task outcome. Register the handoff, confirm synchronization on the **explicit PR branch**, and do not claim a completed audio module until review/integration.
8. **Integrate in small, verified waves.** The coordinator reviews child branches, detects overlaps, preserves each agent's evidence, updates the **one** 73-item ledger and reruns combined checks. Failed/incomplete modules remain pending. If a module needs changing, propose owner-visible scope/count changes before recounting.
9. **Final gate:** On completion of all 73, conduct a cross-skill hostile audit and agent-use evaluation, then obtain the owner's explicit acceptance/merge decision. Current partial status is **not merge-ready**.

## Hypotheses and assumptions

Parallelism might increase throughput, but conflict-resolution cost and skill duplication are unmeasured. Acceptance-test, model-harness and real device coverage are incomplete. Distinguish these planning hypotheses from the observed GitHub state and the owner's requirement.

## Changes and persistence

Original onboarding was memory-only. This revision records CI-verified channel mapping, filter design and **stream buffering**. No other agent was assigned or started by this record; program count is **15/73 developed, 58 pending**. Active memory remains available only on the audio PR branch until integrated with `main`.

## Next action

**Open issues:** 58 curriculum obligations, unexecuted audio agent-use pilot, numerical-extreme review, and incomplete production/device/standards evidence where relevant.

**Suggested next assignments:** `audio-numerical-stability` (last remaining numerical foundation skill), or disjoint modules from the loudness/spectra family lanes, with PSD/STFT numerical audit and an audio agent-use A/B trial as independent review tasks. Do not duplicate the completed channel mapping, filter design or stream buffering. Read the [stream-buffering completion handoff](2026-11-04-audio-stream-buffering-completion-r01.md) and current [roadmap](2026-11-03-audio-skills-roadmap.md) before starting. No other agents are implied to have begun.

## Revisit when

Any module is claimed, reviewed or integrated; a new head/CI changes state; outstanding audit evidence changes; or the owner revises the curriculum or definition of done.
