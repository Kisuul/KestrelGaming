# Skill catalog

These are reusable Kestrel procedures, stored centrally. Read the description and
load only the matching `SKILL.md`. They depend on the surrounding repository and
are not standalone installed host plugins.

| Skill | Trigger |
| --- | --- |
| [kestrel-recall](kestrel-recall/SKILL.md) | Begin or resume a project task; retrieve relevant shared context |
| [kestrel-remember](kestrel-remember/SKILL.md) | Save a useful lesson, decision, project profile, or resumable handoff |
| [kestrel-html-conformance](kestrel-html-conformance/SKILL.md) | Lesson 1: create, edit, generate, or ship HTML; validate final artifacts with the official Nu Html Checker and require a verified zero-error gate |

## Core engineering (selectively activated)

| Skill | Trigger |
| --- | --- |
| [engineering-adversarial-review](engineering-adversarial-review/SKILL.md) | Skeptical PR/code review, baseline regression attribution, green-test defects, test-integrity checks and false-positive restraint |

## Core mathematics (independent curriculum)

Load **only** the relevant module; consult [the mathematics curriculum](../docs/MATH_CURRICULUM.md) for dependencies, assumptions, and the deferred audio integration plan.

| Skill | Trigger |
| --- | --- |
| [math-numerical-analysis](math-numerical-analysis/SKILL.md) | Floating point, error budgets, cancellation, overflow, conditioning and precision |
| [math-verification](math-verification/SKILL.md) | Independent numerical oracles, analytic fixtures, invariants, error bounds and regression evidence |
| [math-dimensional-analysis](math-dimensional-analysis/SKILL.md) | Physical quantities, units, rates, scaling, sample time and dimensional consistency |
| [math-linear-algebra](math-linear-algebra/SKILL.md) | Vectors, matrix operations, coordinate transforms, solves and conditioning |
| [math-complex-numbers](math-complex-numbers/SKILL.md) | Complex arithmetic, polar representations, conjugates, Euler exponentials and phasors |
| [math-probability-statistics](math-probability-statistics/SKILL.md) | Sampling, estimators, distributions, variability and uncertainty |

Add future procedures here as they become useful. Keep project-specific recipes
explicit about their applicability and verified revision. A skill may suggest a
method; it does not supply permission to execute it or override project instructions.
