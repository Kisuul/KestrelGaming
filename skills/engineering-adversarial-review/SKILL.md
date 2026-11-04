---
name: engineering-adversarial-review
description: Independently review code changes and regression claims with pinned baselines, protected acceptance checks, falsifying counterexamples and calibrated findings; use on PRs, risky fixes or disputed test evidence, not as an excuse to edit reviewed code.
---

# Engineering adversarial review — hostile to assumptions, fair to evidence

## Activate / do not activate

Use for an assigned code or PR review, disputed correctness claim, unexplained regression, suspicious test change, or important cross-boundary invariant. A tiny safe diff may receive the **fast path** below. Do not activate merely because an agent is asked to write code, explain a concept, or complete a routine low-risk task. Review-only work grants **no authority** to alter target code, acceptance tests, policies, or branches. If access is insufficient, deliver a bounded review and name the missing checks; never simulate execution.

## Required input

Identify the **target owner/repository, exact head revision, baseline revision, actual diff, authorized intent, affected consumers, protected behavior, changed tests, relevant environment and review boundaries**. Distinguish acceptance requirements from existing tests and from the implementation's claims. If the intended behavior is unresolved, mark it as a decision rather than silently choosing your preferred specification.

## Risk-proportionate procedure

1. **Pin reality.** Verify the branch/revisions, compare the *whole* change set, identify uncommitted/concurrent work and important dependencies. A comment, changelog, commit message, CI badge or agent memory is an **assertion**, not independent evidence. Code is also a fallible implementation; logic depends on stated premises. Collect independent observables.
2. **Triage.** Prioritize high-impact interfaces, state/persistence, security, numerical comparisons, lifecycle, migrations, error paths and changed acceptance tests. Fast path for narrow low-risk change: inspect diff + acceptance intent, run/inspect nearest discriminating check, inspect test edits, report disposition and NOT RUN. Escalate only where uncertainty or blast radius warrants.
3. **Reconstruct behavior.** Trace at least one real caller-to-consumer path when interaction is involved. Identify invariants, inputs/outputs, configuration precedence, error and cancellation semantics, and supported boundary conditions. Do not invent application contracts to manufacture defects.
4. **Challenge tests independently.** Diff tests, reference/golden values, tolerances, mocks and exclusions against baseline. Re-run a **previously accepted oracle** when relevant. A changed expected value or wider tolerance is not justified by its new green result. If acceptance legitimately changed, require an independent requirement decision, not just an implementation diff.
5. **Seek a discriminating counterexample.** Derive an expected outcome from a contract, mathematical identity, independent algorithm, external specification or previously approved acceptance criterion. Test both vulnerable and legitimate cases. Avoid self-referential oracles (same library, same algorithm or matching forward/inverse bug). Link [math verification](../math-verification/SKILL.md) only if numerical evidence actually matters.
6. **Attribute accurately.** Compare the same test/input under baseline and head when safe. Report: newly introduced regression, pre-existing defect, changed requirement, environment-dependent behavior, or unresolved attribution. Do not label a longstanding bug as a PR regression. A failing new check might still be valuable as a separate pre-existing finding.
7. **Control false positives.** Propose a specific violated invariant, visible trigger and alternative explanation before raising a finding. If a clean change survives relevant checks, **no finding** is a valid result. Explain limitations without turning hypothetical risks into confirmed defects.
8. **Report and stop.** Findings first with evidence, reproduction or decisive next check, severity/likelihood rationale, attribution and correction scope. Distinguish must-fix from optional advice; choose `MERGE`, `REQUEST CHANGES`, or `NEEDS EVIDENCE` with explicit conditions. Do not keep reviewing for ceremony after adequate coverage.

## Output contract / acceptance gate

Use the [finding and GitHub review template](references/REVIEW_REPORT.md). Include: ID; severity; impact and likelihood **with rationale**; exact file/revision/line where possible; observed evidence; reproducible or discriminating test; violated invariant; regression status; hypothesis vs fact; minimal proposed correction; uncertainty; and **checks NOT RUN**. Separate independent empirical execution from CI logs, quoted claims and theoretical predictions. Findings must be actionable and bounded. Review-only means **no edits to the reviewed artifact**.

Before claiming skill effectiveness, run [paired trials](references/BEHAVIORAL_EVAL.md); file/header validation and fixture scripts alone do **not** establish improved agent behavior. The [worked cases](references/WORKED_CASES.md) are **synthetic**, not discovered Kestrel defects.
