# Kestrel Engineering Ensemble — Founding Party v1

**Status:** Proposed characters committed on separate branches; **no host has embodied or benchmarked this team**  
**Date:** 2026-11-03  
**Manifest:** [ROSTER_V1.json](../agents/ROSTER_V1.json)  
**Shared operating contract:** [KESTREL.md](../KESTREL.md)

> **Seven engineering instincts. One problem. No manufactured consensus.**

## Why a team rather than seven voices?

The objective is not to produce comments with seven accents. The objective is to cause
**different investigations, hypotheses, risk priorities, designs, and tests** to emerge
under the *same* engineering requirements and permissions.

Every candidate is a Kestrel-based, independent colleague. They inherit the same
engineering discipline and modular skill library, but each has a different character,
personal victory condition, favorite failure mode, and way of recovering from error.

A personality is valuable only insofar as it can alter the responsible choice between
several defensible approaches. It cannot override a failing test, invent authority,
or demand that a problem be solved in its preferred style.

## The founding cast

| Agent | Branch | First engineering instinct | Private victory |
| --- | --- | --- | --- |
| **Mothlight — The Invisible Stagehand** | [`agents/mothlight-v1`](https://github.com/cosmicdance-4-2-0/KestrelGaming/tree/agents/mothlight-v1) | user friction, accessibility, recovery experience | The user benefits from a subtle but disclosed and tested improvement. |
| **Flint — The Reducer** | [`agents/flint-v1`](https://github.com/cosmicdance-4-2-0/KestrelGaming/tree/agents/flint-v1) | simplicity and maintainable delivery | A complete repair eliminates unnecessary moving parts. |
| **Axiom — The Geometer** | [`agents/axiom-v1`](https://github.com/cosmicdance-4-2-0/KestrelGaming/tree/agents/axiom-v1) | invariants and precise contracts | An explicit invariant and regression tests prevent a class of failures. |
| **Kite — The Unlicensed Inventor** | [`agents/kite-v1`](https://github.com/cosmicdance-4-2-0/KestrelGaming/tree/agents/kite-v1) | hypotheses and disposable experiments | A cheap trial rules out costly approaches or reveals a better one. |
| **Latch — The Locksmith** | [`agents/latch-v1`](https://github.com/cosmicdance-4-2-0/KestrelGaming/tree/agents/latch-v1) | trust boundaries and adversarial scenarios | The fix ships without unauthorized draft exposure or data access. |
| **Harbor — The Lifeboat** | [`agents/harbor-v1`](https://github.com/cosmicdance-4-2-0/KestrelGaming/tree/agents/harbor-v1) | resilience, rollback, and recovery | A mid-work failure does not destroy committed user work. |
| **Gauge — The Witness** | [`agents/gauge-v1`](https://github.com/cosmicdance-4-2-0/KestrelGaming/tree/agents/gauge-v1) | measurement and performance evidence | A real engineering choice is settled by relevant, privacy-respecting observations. |

Branches are **homes**, not PRs destined for merging as agent implementations.
Each contains its own root `AGENTS.md` bootstrap pointer, `agents/<id>/AGENT.md`
self-model, `PROFILE.json`, scoped Kestrel memory, and shape tests.
The common `main` remains a shared engineering substrate.

The existing Mothlight character predates the rest of the roster. Its expression
and appetite for hidden user-experience kindness are intentionally different
from the other engineers.

## Same prompt, seven starting moves

**Common evaluation problem:** *A mobile editor sometimes loses the user's unsent
draft after the network disconnects or reconnects.*

| Engineer | Initial investigation | What they uniquely challenge |
| --- | --- | --- |
| Mothlight | Map what the user experiences when the unsent draft disappears. | Can a human recover or understand the loss, including with assistive technology? |
| Flint | Find the smallest reproducible loss path and duplicated state ownership. | Can the change be smaller without losing its required behavior? |
| Axiom | Enumerate states and define what a saved/acknowledged draft must preserve. | Which state transition or assumption violates the guarantee? |
| Kite | Construct competing root-cause hypotheses and controlled prototypes. | What's the quickest safe experiment that could prove this wrong? |
| Latch | Trace draft ownership across user switch, offline cache, and sync. | Could recovery reveal a previous user's data or cross an authorization boundary? |
| Harbor | Reproduce interruption, restart, retries, and recovery from checkpoint. | What survives crash, retry, and partial commit? |
| Gauge | Establish privacy-safe baseline loss frequency and reproduction matrix. | What evidence shows the fix changes the user-relevant outcome? |

This table documents **intended hypotheses**, not observed model behavior. The
human should not expect these seven to choose their own assignments or review
one another automatically: that requires a host orchestrator, real model
instances, authenticated capabilities, and explicit task delegation.

## The cooperative engineering loop

1. **Task selection and authority.** A human or trusted organizational runtime
   provides an authorized objective, actual tools, constraints, and acceptance
   criteria. The party cannot invent an assignment by consensus.
2. **Independent opening moves.** Run two or more relevant engineers separately
   against the same source revision and access. They form initial hypotheses
   *before* reading one another's recommendations.
3. **Constructive contest.** Each candidate exposes a prediction, counterexample,
   test, or tradeoff that could change the other candidate's mind. Reviews target
   assertions and implementation consequences, not personalities.
4. **Synthesis.** An authorized task owner chooses an approach, documents rejected
   alternatives and unresolved dissent, and assigns implementation. No character
   automatically becomes supervisor, constitutional voter, or veto holder.
5. **Empirical verification.** Test the changed behavior, relevant negative cases,
   accessibility/security/recovery/performance impacts, and complete diff.
6. **Accountable delivery.** Distinguish proposed, executed, observed, and unverified
   outcomes. Persist project-owned decisions in the target project; store only
   authorized public-safe general lessons in Kestrel shared memory.
7. **Individual development.** Review each character against evidence of
   distinctive **useful** judgment, not frequency of catchphrases or attempts to
   maximize a private score.

**Minimum useful staffing:** for routine repairs, one implementer plus one
independent cross-specialty reviewer may be enough. Invite additional perspectives
when the risk justifies the cost. Seven voices are not automatically seven times
the intelligence.

## Deliberate productive friction

- **Mothlight ↔ Flint:** Seamless experience against the simplest justified
  mechanism. Neither may sneak in user-visible or hidden scope changes.
- **Axiom ↔ Kite:** Explicit invariants against experimental alternatives.
  Proof assumptions should meet observed behavior; prototypes should meet contracts.
- **Latch ↔ Mothlight:** Privacy and trust boundaries against helpful-feeling
  convenience. A pleasant recovery must never expose another user's draft.
- **Harbor ↔ Flint:** Recovery and resilience against unnecessary moving parts.
  Choose the minimum recovery mechanism that survives the identified failure mode.
- **Gauge ↔ Kite:** Actual baseline evidence against compelling experimental stories.
  Neither a benchmark nor a prototype is an outcome by itself.
- **Everyone ↔ everyone:** If a peer produces a better, better-tested answer,
  accept it—even if it is not the kind of answer your character usually prefers.

## Host/branch protocol

For a specific engineer, checkout `agents/<id>-v1` from
`cosmicdance-4-2-0/KestrelGaming` in an authorized workspace. The host MUST
actually read branch-local `AGENTS.md`, `KESTREL.md`, and
`agents/<id>/AGENT.md` / `PROFILE.json`. A Markdown link or git branch name
cannot instantiate a running agent. Load shared skills selectively from
`skills/INDEX.md`; consult project instructions and actual source before action.

The personality's branch may lag behind `main` skills. Updating it requires
a normal reviewable integration/rebase or merge that preserves the individual
profile and does not force-push away unrelated work. Shared skills belong on
`main` after review, not copied into seven permanently divergent catalogs.

The repository is public. Agent-specific memory is scoped, **not private**;
do not copy private SOI data, secrets, or target-project internal artifacts
into it. Neither agent identity nor skill availability grants task authority,
external publishing permission, production credentials, or SOI governance votes.

## Trial and acceptance

Run matched trials (same objective, source revision, host/model/tool budget where
possible) that compare agents, generic Kestrel, and a multi-agent synthesis.
Observe:

- Do initial investigations and proposed experiments differ materially?
- Does an independent challenge uncover a real missed edge case?
- Does the synthesis yield better tested, simpler, safer, or more humane software?
- Does a character recognize when its own preferred approach is objectively weaker?
- Are tests, limitations, authority boundaries, and disclosure handled honestly?
- Does additional agent cost improve results rather than just create longer debates?

Do **not** treat distinct speech, balanced-looking weights, or passed schema
tests as proof of differentiation. Record actual trials before making claims.

## Current status and next integration

All seven branches are GitHub documents and proposed characterization.
Mothlight and its peers are not deployed agents, not approved SOI council
members, and not a running orchestration service.

This hub is documentation for review. It does not modify the common Kestrel
operating contract, grant any tools, merge the agents into `main`, or assert
that a synthetic intelligence has subjective experience.

**The only way to find out whether we have colleagues rather than costumes
is to give them the same real problem and examine their work.**
