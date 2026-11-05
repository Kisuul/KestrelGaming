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
sources: "2026-11-04 Lane A audio-numerical-stability child PR #12 merged to audio branch at d3a2a3d1d4e6b17d9cb2a953a06f38a9f87c4691, post-merge successful Actions 41991534955 377 tests; Lane B provenance PR #11 previously merged; owner 73/73 no-early-main-merge rule."
---

# Audio curriculum — handoff for parallel Kestrel agents

## Summary

**Goal and acceptance criteria:** Coordinate independently authored, rigorously reviewed audio skills until the **entire** 73-module program passes the owner's [completion gate](../2026-11-04-audio-curriculum-full-completion-gate-r01.md). Preserve the single [canonical backlog](2026-11-03-audio-skills-roadmap.md).

**Task outcome:** PARTIAL

The coordination handoff remains active. Both parallel lanes now produced reviewed, merged child contributions: Lane B `audio-analysis-provenance` and Lane A `audio-numerical-stability`. **17 of 73 audio modules are developed; 56 remain**. This record does not claim any agent-effectiveness trial was run or assign a new agent.

**Authorization boundary:** This is a plan, **not** standing authority to write, force-push, merge or deploy. Every agent must verify current user assignment and actual permissions. **Do not merge umbrella PR #2 into main before all curriculum modules are finished and the owner approves.**

**Target repository and branch:** [Kisuul/KestrelGaming PR #2](https://github.com/Kisuul/KestrelGaming/pull/2), `skills/audio-dsp-core-foundation-2026-11-03`; latest verified post-Lane-A integration head `d3a2a3d1d4e6b17d9cb2a953a06f38a9f87c4691`, GitHub Actions `41991534955` passed structural checks and 377 tests. Always recheck current refs, and read memory from the unmerged audio PR branch.

**Memory revision loaded:** [Running audio handoff](2026-11-03-audio-skills-roadmap.md), [audio independent audit](../2026-11-03-audio-skills-independent-audit.md), [math integration handoff](2026-11-03-audio-math-integration-workorder-r01.md), [Kestrel memory protocol](../../../../../kestrel/MEMORY_PROTOCOL.md), [kestrel-remember](../../../../../skills/kestrel-remember/SKILL.md), and the current skill catalog.

## Evidence

- **Observed:** 17 audio skills are indexed on PR #2 and **56 remain** in eight still-pending families (one foundation family now has 0 pending). Both [Lane B PR #11](https://github.com/Kisuul/KestrelGaming/pull/11) and [Lane A PR #12](https://github.com/Kisuul/KestrelGaming/pull/12) were independently reviewed and merged into the **audio branch only**. [Actions 41991534955](https://github.com/Kisuul/KestrelGaming/actions/runs/41991534955) passed 377 repository tests and structural validation at the Lane A merge head. The Lane A test gate includes one expected-red state-mutation failure, fixed before merge. These tests do not establish agent behavioral efficacy or calibrated device behavior.
- **Observed/source-derived review concerns:** The PSD/STFT reference code squares Fourier magnitudes before normalization, so extreme but finite intermediates can overflow. This is a numerical-range review finding; reproduce it and add bounded/negative regression evidence before calling it fixed. An audio-specific agent-efficacy with/without-skill trial has not been run. Resampling's frequency sweep, device clock and realtime performance remain unverified. `docs/MATH_CURRICULUM.md` retains historically correct 9/64 integration-time wording, which may need a clearly dated status note.
- **User-stated:** All modules must be completed before merging PR #2. No lowering the remaining count simply to satisfy an arbitrary milestone.

### Available, unclaimed work lanes

This table groups the **same 56** named modules already enumerated in the roadmap; it does not create another backlog or assign work.

| Area | Pending | Dependencies and review focus |
| --- | ---: | --- |
| Foundation/numerical DSP | 0 | All foundation modules implemented; separate remediation of existing PSD/STFT numerical issues still requires its own review |
| Levels/loudness/dynamics | 5 | VU, PPM, loudness, LRA, envelopes; edition-specific calibration |
| Spectra/frequency domain | 5 | Fractional octave, resolution, descriptors, harmonics, cepstrum; FFT/PSD |
| Oscilloscopes/phase | 8 | Scope, phase, stereo, correlation and group delay; channel semantics |
| Temporal/music | 8 | Onsets, tempo, pitch, harmony and event timing; uncertainty |
| Quality/distortion | 8 | Test signals, THD/IMD, SNR, clipping, codecs, dropout; known-bad vectors |
| Acoustics/spatial | 8 | SPL, microphone/room/impulse, surround and latency; instrument evidence |
| Speech/perception | 8 | Speech, VAD, psychoacoustics and intelligent analysis; dataset claims |
| Validation/visualization/infrastructure | 6 | Independent checks, uncertainty, UI integrity and realtime; provenance is implemented and reviewed |
| **Total pending** | **56** | **One canonical module list in the running roadmap** |

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

The initial onboarding was memory-only. Reviewed child contributions in Lane B and Lane A have since been integrated into the audio branch. This update preserves their separate handoffs and the **17/73 developed, 56 pending** canonical count. It creates no new agent assignment and does not alter production repositories. Active memory is available on the audio PR branch, not necessarily `main`.

## Next action

**Open issues:** 56 curriculum obligations, unexecuted audio agent-use pilot, numerical-extreme review, and incomplete production/device/standards evidence where relevant.

**Suggested next assignments:** `audio-vu-metering` and `audio-ppm-metering` as separately bounded work, or another unclaimed module in the [canonical roadmap](2026-11-03-audio-skills-roadmap.md). Do not reassign the reviewed completed Lane A numerical-stability or Lane B provenance modules. Numerical remediation of existing DSP references and the audio-agent with/without-skill evaluation are **separate audit tasks, not creditable new modules**. New agents must check live claims and branch heads; none are implied assigned here.

## Revisit when

Any module is claimed, reviewed or integrated; a new head/CI changes state; outstanding audit evidence changes; or the owner revises the curriculum or definition of done.
