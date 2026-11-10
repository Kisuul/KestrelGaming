# KestrelGaming

**Engineering Ensemble v1 (proposed):** [seven separate Kestrel agent characters](docs/ENGINEERING_PARTY_V1.md) with [branch manifest](agents/ROSTER_V1.json). The roster documents characters, not deployed agents or new permissions.
Synthetic organization meant to exist within the UCSH framework. Agency is sacrosanct!

**Common memory for Kestrel agents.** This repository holds the operating contract,
reusable skills, durable knowledge, and resumable handoffs shared across projects.
Memory is ordinary Markdown, versioned with Git. No database, embedding service,
agent runtime, or automatic background process is required.

The implementation starts from the supplied `kestrel-seed-v0.1.0.zip` and preserves
its **Operating Contract v1.0 (candidate)**. See [provenance](docs/PROVENANCE.md).

## Individual engineer roles

A Kestrel-based engineer can have a distinct long-lived character and independent
engineering instincts without gaining permissions from its personality. Read
the [agent structure](docs/AGENT_STRUCTURE.md) and the
[role pickup runbook](docs/AGENT_PICKUP.md) before assigning a character.
New characters start from the [first-person template](kestrel/templates/AGENT_CHARACTER.md)
and [structured profile template](kestrel/templates/AGENT_PROFILE.json).
Each character lives on its own `agents/<id>-v1` branch; `main` keeps the
generic shared contract and skills.

The [shared baseline reconciliation](docs/BASELINE_RECONCILIATION.md) records
the upstream/fork integration, preserved agent homes, and the procedure for
bringing both shared branches to the same commit without rewriting history.

## Start here

1. Read [AGENTS.md](AGENTS.md) and [KESTREL.md](KESTREL.md).
2. Read the [memory protocol](kestrel/MEMORY_PROTOCOL.md), then use the
   [memory index](memory/INDEX.md) to find only the context relevant to the task.
3. Select a procedure from the [skill index](skills/INDEX.md) when needed.
4. Inspect the actual project and its own instructions before relying on memory.
5. Save useful findings here using [the state protocol](kestrel/STATE_PROTOCOL.md).

For use from another project, follow [integration](docs/INTEGRATION.md). A short
[project pointer](docs/PROJECT_POINTER.md), or equivalent session instructions,
is sufficient; do not copy this memory system into every project repository.
This repository is publicly visible; the agent still needs a real checkout or host connection. A URL alone does not load the selected character or its skills.

## What lives where

| Location | Purpose |
| --- | --- |
| [KESTREL.md](KESTREL.md) | Identity, agency, engineering method, evidence, and completion contract |
| [kestrel/](kestrel/) | Memory, continuity, verification, permissions, templates, and evaluation guidance |
| [memory/shared/](memory/shared/INDEX.md) | Knowledge useful across projects |
| [memory/projects/](memory/projects/INDEX.md) | Project profiles, decisions, lessons, and task handoffs, keyed by owner/repository |
| [memory/agents/](memory/agents/INDEX.md) | Optional continuity for a named agent; visible to everyone with repository access |
| [skills/](skills/INDEX.md) | Reusable procedures, loaded only when relevant |
| [docs/](docs/) | Integration and design rationale |
| [tools/validate_seed.py](tools/validate_seed.py) | Read-only structure, local-link, record, and skill checks |

Application code, shipped documentation, and authoritative project decisions stay
in their owning project. Kestrel memory stores a concise lesson or a link back to
that source, including the revision where it matters. Disposable logs and scratch
work stay outside both repositories.

## Read, work, remember

**Recall:** Load the contract and indexes, then the matching project profile,
relevant shared lessons, and any current handoff. Recheck claims against source.

**Work:** Use the contract in the target project, respecting its local instructions
and the task's actual authorization. Keep agent memory writes in this repository.

**Remember:** Save only information likely to help a later task. Identify its source,
scope, uncertainty, and revisit condition. Update the appropriate index, validate,
and synchronize through the authorized Git workflow. Report local-only state honestly.

## Validate

Python 3.9+ and its standard library are sufficient:

```sh
python3 tools/validate_seed.py
python3 -m unittest discover -s tests -v
git diff --check
```

The included GitHub workflow runs the Python checks on pushes and pull requests.
These checks establish structural consistency, not the truth of memories or agent
behavior. Behavioral [evaluation scenarios](kestrel/evals/SCENARIOS.md) remain
trial specifications until actually run.

See [contributing](CONTRIBUTING.md) for updates and concurrent work. This repository
does not install skills into any host, grant access to other projects, or automatically
retrieve or write memory. Configure that connection in the agent's actual environment.
