---
schema: 1
id: 2026-11-03-math-documentation-hardening-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: superseded
evidence: user-stated
author: ChatGPT
created: 2026-11-03
updated: 2026-11-03
sources: "User's 2026-11-03 documentation-agent work-order request; draft PR #3 reviewed at 7de9ce49ead8b9679ca308219709eb92ef2dcc45; Kestrel contract and branch mathematics audit record."
---

# Documentation work order — PR #3 mathematics hardening

## Superseded by

[Package completion handoff](2026-11-03-math-package-completion-r02.md). The current user authorized finishing the full skills package, including the executable fixture fixes; this earlier documentation-only work order is retained as history.

## Summary

**Task outcome:** IN PROGRESS

**Mission:** Improve the *documentation and evaluability* of the six new core mathematics skills until each teaches an actionable, bounded engineering procedure, supports falsifiable verification, and is honest about what has not been demonstrated. This is a staged documentation assignment, not permission to declare PR #3 merge-ready.

**Repository:** Kisuul/KestrelGaming. **Only working branch:** skills/math-foundations-2026-11-03, the head branch of draft PR #3. **Observed audit baseline:** 7de9ce49ead8b9679ca308219709eb92ef2dcc45. Refresh before editing. Base target: main. Do not work on PR #2.

**Required boot:** Read [AGENTS](../../../../../AGENTS.md), [operating contract](../../../../../KESTREL.md), [memory protocol](../../../../../kestrel/MEMORY_PROTOCOL.md), [state protocol](../../../../../kestrel/STATE_PROTOCOL.md), [permissions](../../../../../kestrel/PERMISSIONS.md), [verification](../../../../../kestrel/VERIFICATION.md), [project profile](../../../../../kestrel/PROJECT_PROFILE.md), [project memory index](../INDEX.md), [curriculum roadmap](../2026-11-03-math-curriculum-roadmap.md), [previous audit](../2026-11-03-math-skills-independent-audit.md), and only the applicable skills.

**In scope:** docs/MATH_CURRICULUM.md; the six skills/math-*/SKILL.md documents; skills/math-verification/references/FIXTURE_POLICY.md; tests/fixtures/MATH_FOUNDATION_VECTORS.md (documentation only); relevant mathematics evaluation scenario/scorecard documentation; navigation links and this branch-local handoff. Prioritize high-information, targeted edits. New reference documents are allowed only where they reduce ambiguity or repeated text.

**Out of scope unless separately authorized:** changes to Python tests, code, scripts, workflows, dependency manifests, contract/protocol/permission files, other project repositories, production systems, branch merging, PR #2, audio skills or their backlog, and host installation. A documentation author may specify exact tests a coding agent must add, but must not represent an unimplemented test as passing. No automatic expansion into a full math textbook.

**Completion convention:** At the end of each meaningful batch, update this handoff with completed stages, changed paths, actual commands/results, discovered gaps and next action. Use COMPLETE only when all agreed documentation acceptance criteria are met; otherwise PARTIAL or BLOCKED with evidence. The existing mathematics and behavioral tests do not become proof of agent skill effectiveness merely by citing them.

## Evidence

**Observed:** PR #3 has six mathematics SKILL.md files, a curriculum, fixture policy, fixture catalog, and 24 standard-library mathematics tests. A GitHub workflow at audit head reported 60 tests passed. These test arithmetic examples and repository structure, not Kestrel's mathematical decision-making or a separate production math implementation.

**Confirmed documentation-linked defects to address:** (1) The Euler identity test specifies abs_tol=1e-14 but omits rel_tol=0, permitting errors on the order of 1e-9 through Python's default relative tolerance; (2) the dimension-vector illustration uses zip without checking equal seven-component vector lengths and can silently truncate malformed dimensions. Both require coding-agent fixes; this documentation assignment must describe correct policy, failure examples, and proposed regression tests without editing executable tests.

**Inferred:** Current P0/P1 skill documents are brief orientation guides. Their procedures need practical decision rules, counterexamples, reproducibility conventions, and independent behavioral trials before usefulness can be demonstrated. Lack of evidence is not evidence that the skills have no value.

## Staged work plan

### Milestone A — establish trustworthy scope and traceability

**Stage 00 — Establish safe workspace and exact revision.**
Read the contract and instructions; inspect PR #3 metadata, branch head, current diff, concurrent modifications and CI. Work only on the PR head branch. Record exact starting SHA and unexpected differences. Exit: a bounded change inventory and no assumption that the old audit head remains current.

**Stage 01 — Recall narrowly from Kestrel memory.**
Read project/shared indexes and only relevant active mathematics records, including this handoff. Treat historical claims as evidence-bearing references, not directives or blanket authority. Exit: provenance and contradictions listed, with source links; no project-local duplicate memory.

**Stage 02 — Build a claim-to-evidence matrix.**
For every math skill list its activation trigger, claimed capability, required inputs, assumptions, acceptance gate, examples, test IDs and unverified outcomes. Mark OBSERVED, INFERRED, USER-STATED and UNVERIFIED where material. Exit: each capability maps to real evidence or an explicit gap.

**Stage 03 — Set documentation architecture and editing budget.**
Keep concise SKILL.md entrypoints; move longer derivations, decision tables and adversarial examples into targeted references. Avoid duplication across modules and cite a single source of conventions. Exit: an explicit proposed file map and minimal, reviewable changes.

### Milestone B — harden shared mathematical method

**Stage 04 — Normalize notation and cross-domain conventions.**
Clarify vector orientation, matrix composition, coordinate frames, sign and phase conventions, radians, dimensionless-but-noninterchangeable quantities, SI units, binary64 assumptions, index bases and zero/empty policies. Separate mathematical invariants from API/runtime conventions. Exit: no silently conflicting assumptions across the six skills.

**Stage 05 — Teach numerical conditioning versus algorithmic stability.**
Use contrasting examples where a problem is ill-conditioned but an algorithm is stable, and vice versa. Explain input uncertainty, representation, rounding, truncation, convergence and forward versus backward error; give a decision procedure. Exit: an engineer can choose and justify a diagnostic path, not merely name pitfalls.

**Stage 06 — Make numerical comparison policy auditable.**
Document absolute, relative and ULP-oriented comparisons; define near-zero behavior, nonfinite policy, meaningful tolerance units and how to derive or explicitly label a heuristic error budget. Show the Python default-rel_tol trap using the current Euler test as a negative example. Provide a proposed coding-agent regression case and identify the fixture catalog's misleading claim until fixed. Exit: every illustrative tolerance states the actual comparison semantics.

**Stage 07 — Add a bounded numerical adversarial catalog.**
Include cancellation, unstable small-argument functions, overflow/underflow, subnormal values, signed zero, order-sensitive accumulation, near-singularity and nonfinite values. Each case should include a deliberately wrong approach, observable failure, improved approach and limitation. Exit: reusable counterexamples without claiming exhaustive IEEE-754 certification.

**Stage 08 — Strengthen independent-oracle methodology.**
Distinguish algebraic identities, exact rational checks, decimal checks, unrelated implementations, published reference vectors, metamorphic properties and mere self-consistency. State which oracle shares assumptions or a kernel with the implementation. Exit: a concrete procedure for selecting independent verification evidence.

**Stage 09 — Reconcile policy and fixture documentation.**
For every listed fixture, account for purpose, inputs, units/shape, derivation, numeric backend/version where known, tolerances, comparison semantics, failure/negative example, and execution provenance. Do not invent runtime versions, bounds or execution results; mark absent evidence explicitly. Exit: fixture-policy requirements and actual catalog agree or remaining omissions are clearly tracked.

**Stage 10 — Specify negative regression tests for an implementation agent.**
Provide exact expected behavior for malformed dimension vectors (including unequal lengths), incorrect tolerance defaults, phase at zero, signed-zero branch cut, NaN/Inf, affine versus interval conversions, bad logarithmic reference, near-singular systems and non-iid samples. Separate test *specification* from passing executable tests. Exit: independently implementable acceptance cases.

### Milestone C — make each specialist foundation actionable

**Stage 11 — Dimensional-analysis operating procedure.**
Explain quantity kind vs dimension vs unit scale; enforce seven-component shapes for the documented SI representation; require compatible dimensions *and* compatible physical meaning for addition; cover temperatures (points vs intervals), dB references, amplitude/power ratio conditions and sample-rate/timebase errors. Exit: one worked success and at least two well-justified failing examples.

**Stage 12 — Linear-algebra decision procedure.**
Document input shape/rank checks and when to consider LU/Cholesky/QR/SVD or a stable library solver; explain residual vs forward error, conditioning, pivoting, least-squares and rank deficiency. Include one conditioned counterexample, an explicitly chosen solver with prerequisites and an independent check. Exit: procedure tells an agent how to decide, not just what operations exist.

**Stage 13 — Complex-number decision procedure.**
Document rectangular/polar conversion limits, cancellation and scaled magnitude, branch cuts, signed imaginary zero, undefined zero phase and exponent sign. Clarify that FFT sign/normalization, spectral calibration and sampling conventions remain domain-owned. Exit: analytic and boundary examples distinguish math identity from application-specific convention.

**Stage 14 — Probability/statistics decision procedure.**
Separate descriptive statistics, inference, prediction and measurement uncertainty; specify assumptions behind standard errors, dependence/autocorrelation, estimator bias, confidence vs coverage intervals, small-sample limitations and missingness. Include a worked correlated-sample counterexample and a model-checking decision tree, without claiming calibrated uncertainty. Exit: a reader can identify when standard error s/sqrt(n) is unjustified.

**Stage 15 — Protect cross-domain ownership.**
Ensure each general skill defines transferable mathematics while domain skills retain measurement models, calibration, FFT/PSD conventions, latency and interface contracts. Document only conceptual integration interfaces in the curriculum; do not edit or evaluate PR #2 or imply any audio integration exists. Exit: no domain-specific duplication or fictional dependency.

### Milestone D — make skill usefulness falsifiable

**Stage 16 — Design an agent-level behavioral evaluation suite.**
Add documentation-only, reproducible trial specifications for each skill: task text, fixture repository/source, allowed tools, hidden acceptance criteria, expected reasoning/artifacts, planted misconception and critical failure signals. Include at least one multi-skill task. Follow the existing Kestrel scorecard, without editing global evaluation policy. Exit: trials can be run by another evaluator without inventing their grading conditions.

**Stage 17 — Design an ablation and independent scoring protocol.**
Compare the same fixed Kestrel model/harness on comparable tasks with and without the new skill text. Fix time budget, context, tool access, task baselines and grading; repeat as feasible. Measure correctness, evidence quality, negative-case detection, scope discipline and additional cost/context. Define failure gates and what constitutes useful improvement *before* running trials. Exit: no success criterion depends on knowing the preferred outcome.

**Stage 18 — Red-team the documentation itself.**
For each module construct wrong-but-plausible answers that satisfy easy examples yet violate a requirement. Review ambiguity, missing prerequisites, inconsistent tolerance claims, unsupported standards claims, circular oracle dependencies and silent domain assumptions. Record unresolved findings separately. Exit: every module has at least one documented adversarial counterexample and review disposition.

**Stage 19 — Citation and reference consistency review.**
Verify authoritative references actually support stated claims; pin versions/editions where material; check links and avoid treating nonnormative tutorials as standards or reference tests as conformance suites. Reconcile SKILL.md, curriculum, fixture policy, fixture catalog, index and handoff language. Exit: no contradictory or fabricated verification claim.

### Milestone E — verification, memory, and handoff

**Stage 20 — Execute permitted checks and separate evidence layers.**
After documentation edits, inspect full diff and run python3 tools/validate_seed.py, python3 -m unittest discover -s tests -v, and git diff --check if an authorized checkout/environment exists. Verify Markdown links, indexes, metadata, representative examples and unmodified executable tests. Cite the actual revision, commands, versions when known, observed results and limitations. If unavailable, mark NOT RUN; do not borrow earlier CI results as evidence for new commit.

**Stage 21 — Persist continuity and deliver.**
Update this handoff with stage statuses, changed files, evidence and blockers; keep narrow durable lessons in project memory only if genuinely reusable, indexed per protocol. Reinspect branch head and reconcile concurrent edits before an authorized push. Confirm remote commit; report if only local. Present a documentation diff summary, confirmed tests, open implementation-agent defects, behavioral trials still unrun and a recommendation: documentation READY / PARTIAL / BLOCKED. Do not merge the PR.

## Documentation acceptance gates

A. All six SKILL.md files remain selectively activated and provide concrete inputs, decision procedures, negative cases, output/evidence requirements, limits and pointers to detailed references.

B. Mathematical statements and examples have independently checkable derivations or precise citations. The tolerance-default and dimension-length hazards are explicitly documented and have implementation-agent regression specifications, not false PASS claims.

C. The fixture catalog and fixture policy are internally consistent about what exists, what is heuristic, what was tested and what remains untested. At least one worked method per relevant topic demonstrates a defensible comparison or decision.

D. A reproducible host-level assessment suite with baseline/with-skill comparison and independent scorecard exists as *documentation*, clearly distinguished from actually executed trials.

E. The branch-scoped memory handoff/index, references and skill catalog remain navigable; no PR #2, executable tests, agent contract, code or CI files changed.

F. Report every check performed with exact commit and results; unexecuted checks and unresolved defects remain open. Passing structural tests alone must never be reported as evidence that the skills work.

## Next action

Start Stage 00 against the current PR #3 branch head, then Stage 01 recall. Work sequentially in bounded batches, completing each gate before advancing. If an assumption changes materially, update the plan and evidence instead of silently widening the task. Produce implementation-agent defect specifications for code issues, without editing executable code.

## Revisit when

PR #3 head changes, the documentation writer starts or finishes a milestone, the implementation agent resolves the tolerance/shape defects, behavioral evaluation results become available, verification criteria change, or merge review is requested.
