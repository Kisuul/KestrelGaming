---
schema: 1
id: 2026-11-04-audio-parallel-execution-plan-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: ChatGPT
created: 2026-11-04
updated: 2026-11-04
sources: "Owner 2026-11-04 requests concurrent work and an initial outside-agent task, beginning at far end of audio list; live PR #2 and skills index at 9a260fa18649cf071dfc0ade21bb049c5f246eca; current roadmap 15/73, 58 pending; Kestrel memory and parallel-agent onboarding."
---

# Audio curriculum — bounded concurrent development plan (proposal)

## Summary

**Goal and acceptance criteria:** Permit distinct Kestrel agents to implement independent audio engineering skills concurrently while maintaining **one source of truth**, serial verification of integration and the owner-defined [full 73-skill completion gate](../2026-11-04-audio-curriculum-full-completion-gate-r01.md). Current snapshot: **15 / 73 developed; 58 pending**. The [canonical roadmap](2026-11-03-audio-skills-roadmap.md) owns the list and counts. No candidate is removed or credited by writing this plan.

**Task outcome:** COMPLETE

This means the **coordination design is prepared**, NOT that participating agents have been launched or that another module is complete. Participation requires an explicit assignment and actual tool permissions. This plan is a proposed way of working, not standing remote-write, publish or merge authority.

**Target:** Kisuul/KestrelGaming open [PR #2](https://github.com/Kisuul/KestrelGaming/pull/2), source `skills/audio-dsp-core-foundation-2026-11-03`, observed head `9a260fa18649cf071dfc0ade21bb049c5f246eca`; current PR base SHA at inspection `c268a4d0be121738cbfdb0d7a90de7874299c0f2`. Another remote `main` tip may differ. **Always re-fetch the current PR branch head before branching or integrating.**

## Evidence

**Observed:** PR #2 is open and unmerged, with 15 audio skill entrypoints, 58 canonical pending modules, 308 passing repository tests and structural validation at latest confirmed head. Existing [parallel-agent onboarding](2026-11-04-audio-parallel-work-onboarding-r01.md) already requires isolated work, separate task memory, serial catalog reconciliations, real verification and owner permission before any final main merge.

**Engineering rationale (inference):** The 58 modules span nine fields, so serial development is unnecessarily conservative for low-coupling components. Concurrent *writing and local tests* can proceed; integration to the one canonical branch must be reviewed and serialized. Dependencies still matter for cross-cutting contracts; speculative parallel changes to the same math/reference module or index waste more time than they save.

### Initial lanes (offered, not claimed)

| Lane | Suggested agent | Counted module | Primary ownership | Review dependency |
| --- | --- | --- | --- | --- |
| Foundation | Existing coordinator / primary engineer | `audio-numerical-stability` | `skills/audio-numerical-stability/` and its tests | Existing numerical / PSD / STFT contracts; no automatic fixes elsewhere |
| Far end of curriculum — **Task 1** | Other Kestrel agent, not yet assigned | `audio-analysis-provenance` | `skills/audio-analysis-provenance/` and its tests | Existing timebase, DSP test fixtures and result contracts |
| Optional later third lane | Another authorized agent | A disjoint loudness or speech/perception skill from roadmap | Its own skill/tests | Source standards and clear stated evidence |
| Integrator/reviewer | Coordinator | No counted module | Shared `skills/INDEX.md`, project memory index and canonical roadmap | Reviews all child work one at a time |

The [Task 1 handoff](2026-11-04-audio-analysis-provenance-agent-task-01-r01.md) provides a fully bounded, copyable agent assignment. Beginning at the last item tests parallelism without competing for numerical-stability source files. This is *not* permission to edit the entire validation/infrastructure family.

### Workflow and merge gates

1. **Claim and inspect.** An assigned agent reads `AGENTS.md`, `KESTREL.md`, `kestrel/MEMORY_PROTOCOL.md`, `kestrel/VERIFICATION.md`, current branch catalog/roadmap, [parallel onboarding](2026-11-04-audio-parallel-work-onboarding-r01.md) and its own handoff. Check whether another agent has already claimed the same module before touching files. The assignment record is initially **prepared/unclaimed**.
2. **Isolate from the live PR head.** Use a unique child branch/worktree from the *current* `skills/audio-dsp-core-foundation-2026-11-03` head. Prefer a child PR whose **base is the audio branch**, not `main`. Do not force-push shared refs or modify root governance, merged Math, unrelated audio implementations, workflows, CI dependencies or production software without new approval.
3. **Own your own paths.** Author `skills/audio-<topic>/SKILL.md`, focused references, optional bounded stdlib oracle and `tests/test_audio_<topic>_reference.py`; create an indexed task-specific handoff. To pass Kestrel's structural validator, a child may propose the **single new catalog row and memory-index row needed for its own files**. The coordinator alone resolves shared index collisions/rebases and edits the canonical audio roadmap after integration. Never overwrite parallel agents' index changes.
4. **Independent evidence.** Set precise units, sample clocks, processing tap, channels, representation/version, assumptions, error policies and limits. Test analytical, negative, metamorphic and independently derived expectations; cite actual external source editions. Do not count multiple computations of the *same* implementation as independent confirmation.
5. **Verification.** Run targeted tests, `python3 tools/validate_seed.py`, `python3 -m unittest discover -s tests -v` and `git diff --check` if environment supports them. A child missing index rows may need a local temporary proposed index entry for structural validation. Report actual commands, exits and known checks not run.
6. **Deliver and review.** Provide child PR/diff, exact head SHA, list of owned files, test evidence, reviewed limitations, a valid Kestrel task memory handoff and any source/security risks. The coordinator conducts hostile review and integrates approved child contributions *one by one* using the latest shared audio head. Resolve changed-base conflicts and rerun combined checks. Credit a new module only on verified audio-branch integration.
7. **Control work-in-progress.** Start with **two simultaneous implementers** and one reviewer/coordinator; expand to 3–4 implementers only after a complete handoff/merge cycle shows low conflict and healthy verification latency. No performance gain is claimed until measured.
8. **Final barrier.** PR #2 to `main` is an entirely separate owner decision, **only after all 73** completed obligations and curriculum-wide review. Never merge it on a partial count.

**Source-of-truth roles:** `skills/INDEX.md` = executable activation catalog; running roadmap = one 73-item ledger; independent task handoffs = per-agent evidence; PR/commits = actual delivered work. These are distinct and must be reconciled.

## Next action

Prepare [Task 1 provenance agent](2026-11-04-audio-analysis-provenance-agent-task-01-r01.md) for handoff, separately continue `audio-numerical-stability` when authorized, and create no more than two active implementation streams initially. The coordinator checks claims, exact branch SHA and child PR base; reviews each delivery; serializes index/ledger updates. **Task 1 has NOT begun in this planning record.**

## Revisit when

A second agent accepts/claims the task; a child branch or PR is opened; the live audio branch changes; count, test evidence or module taxonomy changes; integration conflicts materialize; or the owner adjusts workstream concurrency or the full-curriculum acceptance policy.
