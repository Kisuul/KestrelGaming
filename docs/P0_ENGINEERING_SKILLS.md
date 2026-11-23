# Kestrel P0 engineering foundations — program proposal

**Status:** proposal / agent work pending. **Target:** [Kisuul/KestrelGaming](https://github.com/Kisuul/KestrelGaming) · **Program branch:** `skills/p0-engineering-foundations-2026-11-04`.

## Purpose

Build **three compact, selectively activated, reusable engineering procedures**. Kestrel's [operating contract](../KESTREL.md) already requires sound judgment, scope discipline and evidence integrity. These modules must teach **how to do the work** and how to recognize plausible failures—not copy governance into three bigger prompts.

**Design measure:** maximum accessible expertise; minimum resident context; measurable improvement in engineering outcomes.

| Sequence | Issue | Proposed skill entrypoint | Primary failure prevented |
| --- | --- | --- | --- |
| P0-A | [#5 — Requirements & Acceptance](https://github.com/Kisuul/KestrelGaming/issues/5) | `skills/engineering-requirements-acceptance/SKILL.md` | Invented requirements, unfalsifiable completion |
| P0-B | [#6 — Interface Evolution](https://github.com/Kisuul/KestrelGaming/issues/6) | `skills/engineering-interface-evolution/SKILL.md` | Silent interface/config/lifecycle compatibility breaks, unnecessary abstraction |
| P0-C | [#7 — Adversarial Review](https://github.com/Kisuul/KestrelGaming/issues/7) | `skills/engineering-adversarial-review/SKILL.md` | Green-test complacency, fabricated regressions, hidden test weakening |

The order is a suggested dependency-informed review sequence; agents can design independently and in parallel. No skill should require importing another skill to function. Domain-specific mathematics lives in the existing math skills and is linked when useful.

## Progressive disclosure

1. Always-loaded [AGENTS.md](../AGENTS.md) and operating contract stay concise. **Do not alter them as part of this program**.
2. `skills/INDEX.md` advertises names and trigger descriptions; only activate the relevant `SKILL.md`.
3. The SKILL.md entrypoint carries a short, actionable workflow, explicit non-trigger and acceptance gate.
4. Detailed worksheets, counterexamples, fixtures and evaluation methods live in *on-demand* references.
5. Executable oracles and tests operate when relevant; they do not all need to reside in the agent's active prompt.

A skill that adds context cost without measurable decision-quality value is not automatically a success.

## Implementation workflow

- **Coordinator (this branch):** owns program overview, shared memory, PR integration, cross-module consistency and review gates. Its initial PR should be a **draft proposal**.
- **Specialist agents:** one per issue; each starts from the latest program branch, loads only relevant Kestrel memory, changes only its skill and necessary reference/index/test files, and opens a child PR **targeting the program branch**. Do not directly write to `main`.
- **Serial integration:** the shared `skills/INDEX.md` and `memory/projects/kisuul/kestrelgaming/INDEX.md` require reconciliation. Merge children only after independent review. Do not force-push.
- **Evaluation:** compare fixed tasks with/without the skill using the same model, harness, permissions, tool budget and acceptance rules. Use clean/decoy tasks to penalize false positives and unnecessary ceremony. Separate observed results from trial designs.

### Shared memory handoffs

- [Program coordinator](../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-04-p0-engineering-program-coordination-r01.md)
- [Requirements agent](../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-04-p0-requirements-acceptance-agent-r01.md)
- [Interface evolution agent](../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-04-p0-interface-evolution-agent-r01.md)
- [Adversarial review agent](../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-04-p0-adversarial-review-agent-r01.md)

## Evidence and security boundaries

- Files and green structure/fixture tests prove **only what they actually test**. They do not prove reliable host skill activation, general engineering correctness, or improved agent decisions.
- Never place evaluator-only withheld answer keys in a public repo or any location the assessed agent can access. A separate Markdown file in this repository is **not** a hidden key. If secure separation is unavailable, publish nonsecret evaluation design and mark blind trial **BLOCKED/NOT RUN**.
- Protect unrelated branch changes, existing acceptance tests and the authority of app repositories over app-specific behavior. Do not duplicate runtime service or project-local memory.
- Do not alter operating-contract/permissions files or change other PRs from this work. [RFC #4](https://github.com/Kisuul/KestrelGaming/issues/4) is a separate doctrine review, not a dependency.

## Minimum quality gates

1. Issue requirements are traced to an actionable skill method and finite scope.
2. Each skill provides at least three **wrong-versus-right** concrete examples, including a negative check that actually distinguishes the cases.
3. Relevant fixture scripts are run; `python3 tools/validate_seed.py`, `python3 -m unittest discover -s tests -v`, and `git diff --check` have truthful, revision-specific results.
4. Each proposed behavioral trial has a fixed baseline, clear rubric, realistic budget and securely withheld judging material where needed.
5. Documentation, skill index and Kestrel memory handoffs are consistent and cite current source.
6. Final PR disposition distinguishes **structural ready**, **tested procedures**, and **observed agent effectiveness**, rather than conflating them.

**Current state:** three issues and proposal scaffolding only. Three skill implementations and behavioral trials are pending separate agent work.
