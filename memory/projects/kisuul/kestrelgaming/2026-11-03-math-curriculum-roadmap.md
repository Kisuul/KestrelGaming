---
schema: 1
id: 2026-11-03-math-curriculum-roadmap
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: user-stated
author: ChatGPT
created: 2026-11-03
updated: 2026-11-03
sources: "User-provided core mathematics curriculum, 2026-11-03; Kisuul/KestrelGaming main at 47745f8a41463e1a202a2f9f84385f3ab61d49a1; separate audio PR #2 inspected 2026-11-03; new math branch verification pending."
---

# Mathematics curriculum — durable independent roadmap

## Summary

**Task outcome:** PARTIAL

Establish a separate, reusable math skill library at `skills/math-*` for audio, graphics, physics, simulation, programming and data. The six initial narrowly activated procedures are numerical analysis, mathematical verification, dimensional analysis, linear algebra, complex numbers and probability/statistics. The [curriculum plan](../../../../docs/MATH_CURRICULUM.md) records candidate families, dependency boundaries, engineering reviews and next priorities.

**Implementation scope:** `skills/math-foundations-2026-11-03` review branch based on `main`, deliberately not branched from open audio PR #2. No contract or application edits. Committing a skill does not activate it inside a particular host.

## Evidence

**User-stated:** Mathematics should be shared across disciplines, not duplicated in domain skills. Mathematical verification and numerical analysis are highest priority. Six initial module names and eleven candidate families supplied. The existing 73-candidate audio curriculum is independent and must not be inflated.

**Observed before implementation:** On 2026-11-03 `main` had no audio skill files; PR #2 remained open on branch `skills/audio-dsp-core-foundation-2026-11-03` with eight audio skills and 65 pending. This condition must be rechecked on resume.

**Proposed on the math review branch:** Six `SKILL.md` files; indexed activation triggers; math fixture policy; analytic cases and standard-library regression tests; this persistent roadmap. Check exact branch commit and CI before promoting any assertion from 'proposed' to 'verified'.

**Limits:** General mathematical tests are not application integration, numerical proof, normal-distribution validation or instrument/standards certification. No claim that existing audio skill files already cross-link these math modules: see the deferred integration mapping in the curriculum plan. The audio backlog remains unchanged.

## Next action

Review commit-level CI (structural validator and full tests); inspect negative cases and numerical tolerances, then open/maintain a dedicated mathematics PR. Cross-link existing audio skill files *after* the independent initiatives reach compatible bases, without copying math implementations or changing the 73-candidate backlog. Prioritize transform mathematics, calculus and geometry only when demonstrated cross-domain needs justify separate modules.

## Revisit when

Either PR merges/rebases, CI discovers a faulty example, authoritative mathematical references change materially, new domain needs expose an absent foundation, or the owner changes the curriculum scope or priority.
