---
schema: 1
id: 2026-11-04-p0-adversarial-review-agent-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: user-stated
author: ChatGPT
created: 2026-11-04
updated: 2026-11-04
sources: "User request to delegate P0 skill development; GitHub issue #7; program planning branch based on main c268a4d0be121738cbfdb0d7a90de7874299c0f2."
---

# Agent handoff C — Adversarial Code Review & Regression Engineering

## Summary

**Task outcome:** IN PROGRESS

**Assignment:** Deliver [issue #7](https://github.com/Kisuul/KestrelGaming/issues/7): a skeptical, evidence-disciplined `engineering-adversarial-review` procedure with demonstrably discriminating checks and false-positive restraint.

**Repository:** Kisuul/KestrelGaming. **Program branch:** `skills/p0-engineering-foundations-2026-11-04` (based on `main` at `c268a4d0be121738cbfdb0d7a90de7874299c0f2`). **Task status:** proposed/awaiting agent; refresh revisions when resuming.

**Required startup:** Read [AGENTS.md](../../../../../AGENTS.md), [KESTREL.md](../../../../../KESTREL.md), [memory protocol](../../../../../kestrel/MEMORY_PROTOCOL.md), [state protocol](../../../../../kestrel/STATE_PROTOCOL.md), [verification](../../../../../kestrel/VERIFICATION.md), [permissions](../../../../../kestrel/PERMISSIONS.md), the [project memory index](../INDEX.md), and the [program design](../../../../../docs/P0_ENGINEERING_SKILLS.md). Inspect actual branch, source and prior work, not just remembered assumptions.

**Branch workflow:** Create an isolated task branch from the **latest program branch**, commit only your task's work, and open a pull request **targeting the program branch**. Do not modify `main` or force-push. Update *this exact handoff* as the task advances and submit it with your task PR. Preserve unrelated agent changes. Confirm branch revisions before synchronizing.

**Boundaries:** Skills are progressive, selectively loaded procedures. The operating contract is not being rewritten. Do not edit `KESTREL.md`, `AGENTS.md`, permissions, CI policy, PR #2, or application code without a separate, explicit user task. Avoid new runtimes/services, unnecessary packages, personal data or duplicate memory trees. Requirements and application acceptance tests remain owned by applications. Use `COMPLETE` only for demonstrated work, not expected work.


## Evidence

**User-stated:** Other agents should perform the substantial work, with shared Kestrel memory enabling retrieval and handoffs. P0 procedures must help prevent errors by untrained agents without making every agent load every specialty.

**Observed when planned:** [Kestrel's verification rules](../../../../../kestrel/VERIFICATION.md) cover evidence integrity, but a dedicated reusable hostile review workflow was not introduced in this planning task. Issue #7 is the detailed specification.

**Unverified:** No new reviewer skill, reproducibility harness, hidden-grading trial, or independently observed improvement has yet been implemented or run.

## Staged execution

0. **Bootstrap:** Load source/current branch, issue #7, contracts and applicable indexes; identify relevant PR baseline and evidence.
1. **Review triage:** Specify a proportional fast path vs deep inspection, risk ranking, accepted baseline, protected tests and review-only action boundaries.
2. **Finding schema:** Record impact/severity rationale, revision/path, reproduced trigger or discriminating next check, violated invariant, regression attribution, observed-versus-inferred status, corrections and NOT RUN checks.
3. **Protect test integrity:** Compare acceptance tests against baseline; detect removals, weakened tolerances/golden values and undocumented requirements changes. Keep edits to reviewed code out of review-only tasks.
4. **Adversarial fixtures:** Demonstrate a green-unit-test bug, an intentionally weakened accuracy threshold and a pre-existing defect that must not be called a regression. Add a **clean decoy** to measure false positives.
5. **GitHub report procedure:** Findings first, severity and evidence, suggested independent reproduction, must-fix vs optional concerns, disposition and unresolved risks; no speculative bug lists.
6. **Evaluation:** Specify paired fixed trials, blind independent grading for precision and recall, risk-weighted correctness and resource costs; withheld answer keys outside participant-accessible repositories or tools.
7. **Register and verify:** Add `skills/engineering-adversarial-review/SKILL.md`, references and catalog entry. Follow Kestrel verification commands, check new fixtures and negative cases, inspect diff. Clearly mark unrun host trials.
8. **Close or continue:** Update this memory record, provide exact changed paths and checks, and open an isolated task PR targeting the program branch. Do not self-merge.

## Acceptance gate

Shows reproducible true defects, distinguishes baseline failures, does not report clean decoys as confirmed bugs, and does not mutate reviewed source on a review-only assignment. Works for small and large PRs without requiring unrelated specialist skills. Follow issue #7 for detailed evaluation requirements.

## Next action

A review-specialist agent should take issue #7, perform Stage 0 and produce an independently testable first skill draft.

## Revisit when

Target repository/tests change, requirements or interface skill becomes available, task PR is reviewed, behavioral evidence changes, or false-positive failures are discovered.
