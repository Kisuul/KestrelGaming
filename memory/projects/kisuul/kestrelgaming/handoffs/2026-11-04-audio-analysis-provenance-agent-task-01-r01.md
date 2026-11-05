---
schema: 1
id: 2026-11-04-audio-analysis-provenance-agent-task-01-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: ChatGPT
created: 2026-11-04
updated: 2026-11-04
sources: "Owner 2026-11-04 requests Task 1 prompt for another agent from far end of Kestrel audio curriculum; audio PR #2 head 9a260fa18649cf071dfc0ade21bb049c5f246eca, 15/73 implemented 58 pending; W3C PROV-O / PROV-DM and RFC 8785 design context."
---

# Parallel Task 1 — audio-analysis-provenance (prepared, unclaimed)

## Summary

**Goal and acceptance criteria:** Implement the **last listed pending module** `audio-analysis-provenance` as a bounded, independently reviewed Kestrel engineering skill, while the coordinator can separately work on `audio-numerical-stability`. Record enough *audio-specific* provenance to distinguish reproducible, traceable analyses from unlabeled DSP results, without asserting authenticity or device proof.

**Task outcome:** PARTIAL

This outcome means **the assignment prompt is prepared, not that implementation has started**. No external agent has yet accepted, claimed, branched, tested or delivered this module. Do not credit this as skill #16 until integration, test evidence and index/roadmap reconciliation are verified.

**Authorization boundary:** This is a suggested work order. The assigned agent must verify actual permissions before GitHub writes and must not merge the umbrella PR #2 to `main`. The owner requires **all 73 modules** finished before final merge. Source branch is `skills/audio-dsp-core-foundation-2026-11-03`, observed at `9a260fa18649cf071dfc0ade21bb049c5f246eca`—fetch the latest before starting.

## Evidence

**Observed repo context:** The [canonical roadmap](2026-11-03-audio-skills-roadmap.md) names `audio-analysis-provenance` as the last of 58 pending modules, and `skills/INDEX.md` does **not** contain it yet. Related existing skills: [audio-timebase-sync](../../../../../skills/audio-timebase-sync/SKILL.md), [audio-dsp-test-fixtures](../../../../../skills/audio-dsp-test-fixtures/SKILL.md), [audio-sample-formats](../../../../../skills/audio-sample-formats/SKILL.md), [audio-stream-buffering](../../../../../skills/audio-stream-buffering/SKILL.md), [math-verification](../../../../../skills/math-verification/SKILL.md) (load only when needed). The coordinator's [parallel execution plan](2026-11-04-audio-parallel-execution-plan-r01.md) limits shared-file writes.

**External source context:** W3C [PROV-O](https://www.w3.org/TR/prov-o/) and [PROV-DM](https://www.w3.org/TR/prov-dm/) distinguish entities, generating/using activities and responsible agents. [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html) defines a specific JSON canonicalization scheme, not simply `json.dumps(sort_keys=True)`. These are research foundations **not** mandatory conformance claims.

### Copyable assignment / prompt

> You are the **Task 1 parallel Kestrel agent** working on `audio-analysis-provenance`, the last module in the 73-skill audio engineering curriculum. You are **not** the coordinator and must not merge PR #2 to main.
>
> **Bootstrap:** Read `AGENTS.md`, `KESTREL.md`, `kestrel/MEMORY_PROTOCOL.md`, `kestrel/VERIFICATION.md`, the current project memory index, the [parallel plan](2026-11-04-audio-parallel-execution-plan-r01.md), [parallel onboarding](2026-11-04-audio-parallel-work-onboarding-r01.md), and [canonical roadmap](2026-11-03-audio-skills-roadmap.md) **from PR #2's branch**. Inspect current `skills/INDEX.md`, relevant DSP/timebase/fixture skills, GitHub PR/CI and other claimed tasks. Current historical baseline is `9a260fa18649cf071dfc0ade21bb049c5f246eca`; do not presume it is still head.
>
> **Deliverable:** Add `skills/audio-analysis-provenance/SKILL.md` with Kestrel-valid metadata, precise activation conditions, practical implementation/audit procedure, primary sources, interoperability limits and failure policies. Add `references/PROVENANCE_CONTRACT.md`, an optional bounded stdlib `scripts/reference_provenance.py` plus independent `tests/test_audio_analysis_provenance_reference.py`, optionally a frozen trace/fixture, and an optional `agents/openai.yaml` if consistent with adjacent skills. Make this a **single audio-specific module**, not a general database, audit platform or media ingestion pipeline.
>
> **Required engineering semantics:** Record the source audio's identity **and what identity was actually verified** (declared ID versus verified content digest); channel layout and sample representation; original sample rate as an exact rational, clock domain, epoch and half-open sample ranges; processing tap/source, transformation chain, parameters (window, FFT, resampler, filter, channel map etc. only where applicable), software/skill/algorithm versions, output units/normalization and uncertainties, truncation/gaps/synthetic silence and known unverified assumptions. Do not silently confuse source and output sample indices, inferred metadata with observed metadata, a missing digest with a verified digest, or downstream display transformations with the original measurement.
>
> **Trace structure:** Define a small, versioned provenance record or bounded acyclic graph; distinguish **entities**, **activities**, and optional responsible **agents** in a W3C-PROV-inspired fashion, but claim W3C compliance only if actually implemented and tested. Permit honest partial records with explicit unknowns; reject contradictory clocks, wrong rate units, duplicate identifiers, missing references, impossible segments and provenance cycles. Handle privacy by default: no raw audio, credentials, unique personal identifiers or full local paths required in fixtures.
>
> **Determinism and limits:** If hashing canonical record bytes, specify encoding, ordering, numeric serialization, digest and covered fields. Never describe Python `json.dumps(sort_keys=True)` as RFC 8785 compliant; either independently test actual JCS compliance or label a custom deterministic encoding honestly. Hashes establish integrity *of bytes*, not truth, trusted capture time, authenticity or software correctness. Avoid external dependencies for normal repository tests.
>
> **Adversarial tests:** Derive expected outputs independently from the implementation. Include at least a simple PCM→analysis→visualization graph, rate conversion 44.1→48 kHz with explicitly separated sample clocks, an epoch gap, truncated input and injected silence, channel order changes, identical semantic records with reordered map keys, changed parameter/digest detection, unknown-origin handling, cycles/duplicates/dangling references, and privacy-sensitive records. Record exactly which outcomes are tested and which are theoretical. Use existing math verification and timebase skills selectively.
>
> **Collaboration:** Work on a unique child branch from the **latest PR #2 audio head**, not default main; prefer a reviewable child PR **targeting the audio development branch** if authorized. Own only `skills/audio-analysis-provenance/` and its focused tests/fixtures/handoff. Propose the minimum `skills/INDEX.md` and project-memory index row required to validate this new skill, but **never rewrite the canonical 73-item roadmap** or overwrite another agent's shared-index changes. The coordinator performs the final index merge and increments the completed count **only after verified integration**. Do not change numerical-stability, the existing DSP references, governing contracts or CI workflows.
>
> **Evidence and delivery:** Run focused tests, `python3 tools/validate_seed.py`, `python3 -m unittest discover -s tests -v` and `git diff --check` when available. Distinguish local, CI and external checks. Return the child branch/PR (if created), exact SHA, files, tests, sources, limitations, follow-up review questions and an indexed Kestrel task-specific handoff with `**Task outcome:** COMPLETE/PARTIAL/BLOCKED` as appropriate. If you cannot publish due to access, provide a patch and mark it unsynchronized. Do **not** claim the curriculum is 16/73 until the coordinator confirms branch integration.

**Scope separation:** No actual W3C PROV/RFC 8785 conformance requirement unless accepted after research; no cryptographic signature platform; no speculative source code changes elsewhere; no real audio hardware or private media.

## Next action

Hand the assignment above to a separate authorized Kestrel agent. Only **after that agent accepts** should it create a unique feature branch, establish task ownership and begin implementation. The coordinator continues independent numerical-stability work and serializes integration. Report acceptance as *assignment claimed*; distinguish it from completed code and verified merge.

## Revisit when

The external agent accepts or declines; its source branch is no longer current; a provenance convention conflicts with other skills; evidence/standards change; a child PR is opened; or integration creates a new completed module.
