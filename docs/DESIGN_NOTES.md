# Design notes and research basis

**Status:** Design rationale, not an empirical performance claim about Kestrel. Seed v0.1.0 intentionally has not been benchmarked.

## Central-memory adaptation (2026-11-02)

The current user request selects KestrelGaming as the common home for all agents'
long-term skills and Markdown memory. The original per-project distribution model
is therefore replaced by a short bootstrap pointer and one shared checkout or connector.
Records are scoped by owner/repository, carry provenance and uncertainty, and are
indexed for selective retrieval. Separate files and ordinary Git integration support
concurrent writers without a rolling shared transcript.

The core contract remains unchanged. The initial scope deliberately excludes a
runtime, database, vector index, scheduler, and automatic installation. The validator
checks structure only. See [provenance](PROVENANCE.md) and [integration](INTEGRATION.md).

## Original seed decisions

1. **Personality is separate from machinery.** `KESTREL.md` defines judgment and collaboration. Project configuration, verification, safety, state, and evaluation live in separate, more maintainable documents.
2. **Keep the entrypoint concise.** `AGENTS.md` points at an authoritative compact core instead of containing every detail. This reduces recurring context load and instruction drift.
3. **Default to one agent.** Reviewer or evaluator separation is risk-dependent; the seed does not require a complex multi-agent architecture to fix trivial bugs.
4. **Freedom of judgment; bounded authority.** Kestrel is allowed to critique specifications and choose methods, but not invent permissions. Actual containment is a host responsibility.
5. **Evidence before completion.** Requirements, implementation, and tests are independent enough that a passing suite can be incomplete or manipulated.
6. **Durable handoffs for substantial tasks.** The handoff template is available without requiring a journal for every change.
7. **Manual evaluations first.** Scenario definitions and scorecards are included; an automated agent harness is intentionally not claimed or simulated.

## Public references

These informed design choices; they do not establish that this particular seed has been validated.

- OpenAI, **Harness engineering: leveraging Codex in an agent-first world** — progressive repository documentation and feedback systems: https://openai.com/index/harness-engineering/
- **AGENTS.md** open format — project-level instructions and repository entrypoint: https://agents.md/
- Anthropic, **Effective harnesses for long-running agents** — incremental progress and handoff continuity: https://www.anthropic.com/research/effective-harnesses-for-long-running-agents
- Anthropic, **Harness design for long-running apps** — planning, evaluation, and the costs of orchestration: https://www.anthropic.com/research/harness-design-long-running-apps
- OWASP, **Secure Coding with AI Cheat Sheet** — repository prompt injection, tool permissions, test integrity, and supply-chain risks: https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html
- GitHub Docs, **About code owners** — protecting sensitive configuration with code ownership and branch rules: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners

## Unresolved design questions

- How concise can the core contract become without losing valuable guidance?
- Which evaluation tasks distinguish autonomy from premature scope expansion?
- What runtime policy can be enforced across different hosting tools?
- When does a separate evaluator materially outperform a single-agent review process?

Answers require trials against representative repositories and supported harnesses, not more prompt rhetoric.
