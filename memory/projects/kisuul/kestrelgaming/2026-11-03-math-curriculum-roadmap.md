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
sources: "2026-11-03 user mathematics curriculum; main 47745f8; separate audio PR #2; math implementation 53dbbd171348f2e321aebf2ed544f2bb5766309d; GitHub Actions 41771827951 and 41771860005 passed 55 tests and structural validation; local 19-fixture run passed."
---

# Mathematics curriculum — durable independent roadmap

## Summary

**Task outcome:** PARTIAL

Establish a separate, reusable math skill library at `skills/math-*` for audio, graphics, physics, simulation, programming and data. The six initial narrowly activated procedures are numerical analysis, mathematical verification, dimensional analysis, linear algebra, complex numbers and probability/statistics. The [curriculum plan](../../../../docs/MATH_CURRICULUM.md) records candidate families, dependency boundaries, engineering reviews and next priorities.

**Implementation scope:** `skills/math-foundations-2026-11-03` review branch based on `main`, deliberately not branched from open audio PR #2. No contract or application edits. Committing a skill does not activate it inside a particular host.

## Evidence

**User-stated:** Mathematics should be shared across disciplines, not duplicated in domain skills. Mathematical verification and numerical analysis are highest priority. Six initial module names and eleven candidate families supplied. The existing 73-candidate audio curriculum is independent and must not be inflated.

**Observed before implementation:** On 2026-11-03 `main` had no audio skill files; PR #2 remained open on branch `skills/audio-dsp-core-foundation-2026-11-03` with eight audio skills and 65 pending. This condition must be rechecked on resume.

**Implemented on the mathematics review branch:** Six `SKILL.md` files, indexed activation triggers, fixture policy, analytic cases, 19 new standard-library tests and this persistent roadmap. GitHub Actions run `41771827951` passed the structural validator and all **55 repository tests** at implementation commit `53dbbd171348f2e321aebf2ed544f2bb5766309d`; pull-request run `41771860005` also passed. The 19 mathematical fixtures were independently executed locally. These results do not validate host activation or application behavior.

**Limits:** General mathematical tests are not application integration, numerical proof, normal-distribution validation or instrument/standards certification. No claim that existing audio skill files already cross-link these math modules: see the deferred integration mapping in the curriculum plan. The audio backlog remains unchanged.

## Next action

Maintain [draft mathematics PR #3](https://github.com/Kisuul/KestrelGaming/pull/3), inspect negative cases and numerical tolerances, and check CI on any new commit before merge. Cross-link existing audio skill files *after* the independent initiatives reach compatible bases, without copying math implementations or changing the 73-candidate backlog. Prioritize transform mathematics, calculus and geometry only when demonstrated cross-domain needs justify separate modules.

## Revisit when

Either PR merges/rebases, CI discovers a faulty example, authoritative mathematical references change materially, new domain needs expose an absent foundation, or the owner changes the curriculum scope or priority.
