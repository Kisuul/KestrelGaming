---
schema: 1
id: 2026-11-04-p0-requirements-acceptance-agent-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: user-stated
author: ChatGPT
created: 2026-11-04
updated: 2026-11-04
sources: "User request to delegate P0 skill development; GitHub issue #5; program planning branch based on main c268a4d0be121738cbfdb0d7a90de7874299c0f2."
---

# Agent handoff A — Requirements & Acceptance Engineering

## Summary

**Task outcome:** IN PROGRESS

**Assignment:** Deliver [issue #5](https://github.com/Kisuul/KestrelGaming/issues/5): a concise, transferable `engineering-requirements-acceptance` skill with falsifiable acceptance maps and controlled behavioral evaluation designs.

**Repository:** Kisuul/KestrelGaming. **Program branch:** `skills/p0-engineering-foundations-2026-11-04` (based on `main` at `c268a4d0be121738cbfdb0d7a90de7874299c0f2`). **Task status:** proposed/awaiting agent; refresh revisions when resuming.

**Required startup:** Read [AGENTS.md](../../../../../AGENTS.md), [KESTREL.md](../../../../../KESTREL.md), [memory protocol](../../../../../kestrel/MEMORY_PROTOCOL.md), [state protocol](../../../../../kestrel/STATE_PROTOCOL.md), [verification](../../../../../kestrel/VERIFICATION.md), [permissions](../../../../../kestrel/PERMISSIONS.md), the [project memory index](../INDEX.md), and the [program design](../../../../../docs/P0_ENGINEERING_SKILLS.md). Inspect actual branch, source and prior work, not just remembered assumptions.

**Branch workflow:** Create an isolated task branch from the **latest program branch**, commit only your task's work, and open a pull request **targeting the program branch**. Do not modify `main` or force-push. Update *this exact handoff* as the task advances and submit it with your task PR. Preserve unrelated agent changes. Confirm branch revisions before synchronizing.

**Boundaries:** Skills are progressive, selectively loaded procedures. The operating contract is not being rewritten. Do not edit `KESTREL.md`, `AGENTS.md`, permissions, CI policy, PR #2, or application code without a separate, explicit user task. Avoid new runtimes/services, unnecessary packages, personal data or duplicate memory trees. Requirements and application acceptance tests remain owned by applications. Use `COMPLETE` only for demonstrated work, not expected work.


## Evidence

**User-stated:** Build P0 specialist engineering procedures on demand, minimizing resident context and avoidable mistakes. Other Kestrel agents should implement; this handoff delegates work but does not claim anyone has begun it.

**Observed when planned:** Existing Kestrel [verification protocol](../../../../../kestrel/VERIFICATION.md) governs evidence integrity. No new engineering P0 SKILL.md was authored by this planning task. Exact issue #5 is the authoritative, more complete requirements specification.

**Unverified:** No implementation, new tests, host-activation trial, agent improvement or cross-application applicability has yet been demonstrated.

## Staged execution

0. **Bootstrap and inspect:** Identify task branch, actual files, current catalog, branch head and overlaps. Recheck issue #5 and this memory against source.
1. **Claim separation:** Distinguish user requirement, observed baseline, inference, design choice, unresolved decision and test claim. Map onto Kestrel's existing contract to avoid duplicating policy.
2. **Design compact procedure:** Specify activation/non-activation, inputs, fast path vs consequential-question path, outputs and stop criteria. Make decisions actionable.
3. **Acceptance map format:** Include provenance, invariants, boundaries, compatibility, negative cases, oracles, planned checks and resolution owner. No application-specific facts.
4. **Adversarial worked cases:** Cover ambiguous architectural fork, threatened shipped behavior, and green unit tests that miss an integration requirement. Show wrong and right outcomes.
5. **Evaluation fixtures:** Create fixed participant-visible task descriptions, separate evaluator protocol, false leads and deterministic scoring. Keep withheld keys **outside all participant-accessible Git repositories or tools**; do not claim hidden in-repo files are secret.
6. **Register and test:** Add `skills/engineering-requirements-acceptance/SKILL.md` and catalog entry, appropriate references and bounded fixture checks. Run `python3 tools/validate_seed.py`, `python3 -m unittest discover -s tests -v`, `git diff --check` and inspect entire diff. Mark anything not run explicitly.
7. **Demonstrate or disclose:** If authorized and feasible, conduct paired baseline-versus-with-skill trials, recording environment/cost and failures; otherwise mark behavioral efficacy NOT RUN and document exact runnable trial protocol.
8. **Handoff:** Update this record with changed files, commit, results, remaining gaps and next agent action. Open task PR against program branch; do not merge it or the parent PR without review.

## Acceptance gate

Another agent can use the skill on an unfamiliar repo; material acceptance criteria can reject an incorrect implementation or are explicitly UNVERIFIED. Examples reveal invented requirements and premature completion. The skill is independently loadable, indexed and sized for progressive disclosure. Tests and trials are reported only if executed. Follow issue #5 for remaining detailed criteria.

## Next action

An implementation agent should take issue #5, inspect program branch and start Stage 0. No implementation has been requested from this planning session.

## Revisit when

Task is assigned, program branch moves, the skill gets a PR, evidence changes, review discovers ambiguous requirements, or the implementation is integrated.
