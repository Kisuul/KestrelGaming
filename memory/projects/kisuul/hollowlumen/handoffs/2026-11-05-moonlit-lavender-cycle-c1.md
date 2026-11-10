---
schema: 1
id: 2026-11-05-hollowlumen-night-cycle-c1
kind: handoff
scope: project:kisuul/hollowlumen
status: archived
evidence: observed
author: kestrel-gpt6-session-2026-11-05
created: 2026-11-05
updated: 2026-11-08
sources: "User-reported approval of day reference and request for dark mode plus realistic day/night cycle; HollowLumen draft PR #2 head ec201b71281e993026d3c463c41267eda80b159f; NOAA/USNO/W3C source references linked in design doc."
---

# Moonlit Lavender palette and solar cycle

**Historical task snapshot (archived):** The original proposal preceded the user-reported approval of night palette choices. For the approved palettes and remaining implementation risks, see [Visual System v1.0 handoff](2026-11-05-visual-system-v1-complete-d1.md). Historical observations below are preserved as originally recorded.

## Summary

**Goal and acceptance criteria:** Propose a companion night palette consistent with approved daylight visual reference, alongside a realistic, privacy-preserving day/night scene lighting system that does not alter gameplay incentives.

**Task outcome:** PARTIAL

**Historical outcome detail:** PARTIAL — full night concept committed to [HollowLumen PR #2](https://github.com/Kisuul/hollowlumen/pull/2), pending original designer approval and code implementation.

**Authorized scope and boundaries (historical; recheck on resume):** User asks to prepare a dark palette and consider realistic night/day system. Documentation only; no authorization to change production gameplay logic, access GPS automatically or deploy.

**Target repository, branch, and commit:** `Kisuul/hollowlumen`; `design/pastel-twilight-craft-v0-1`; head `ec201b71281e993026d3c463c41267eda80b159f`. Design doc: [NIGHT_MODE_v0.1.md](https://github.com/Kisuul/hollowlumen/blob/design/pastel-twilight-craft-v0-1/docs/design/NIGHT_MODE_v0.1.md).

**Memory revision loaded:** KestrelGaming `bfda4efd156d5a182c4481bfe43d3d9c7b375b49` at this task's start.

Formatting maintenance on 2026-11-08 separated the machine-readable outcome
from its original qualification. Historical project claims were not revalidated.

## Evidence

**Confirmed observations with sources:** User reports that original designer approves the prior **daylight image reference**. Designer wants realistic night/day; user asks for a dark palette. Existing CSS uses an undifferentiated light theme; no day/night engine exists at inspected main commit.

**Hypotheses and assumptions:** "Moonlit Lavender" tokens, twilight choreography, a fictional 45°N valley and default local-clock sync are proposals. Exact astronomy, darker surfaces, fonts and scene effects have NOT been accepted or executed.

**Decisions and rationale:** Separate scene lighting from UI theme. Use continuous solar elevation with seasonal declination and civil/nautical/astronomical twilight (-6/-12/-18 degrees), rather than fixed 18:00 rules. Use fictional coordinates to avoid GPS by default; optional real-location model would require explicit user consent. Manual interface light/dark/auto override remains available. Time-of-day must not gate rewards or punish short sessions.

**Changed files and uncommitted state:** HollowLumen PR #2 now contains two design docs. The prior day style-guide status was updated to accurately reflect user-reported visual reference approval. No CSS or game logic changes. Night visual art is only speculative and its textual labels should not be used as authoritative token values.

| Check actually performed | Result | Limits |
| --- | --- | --- |
| GitHub fetch and PR status | Day PR #2 open/draft; two design docs on feature branch | No merge performed |
| WCAG relative luminance formula | Night pair ratios 15.08:1 main text, 11.18:1 action, 8.85:1 secondary text | Solid samples, not rendered accessibility audit |
| Reference check | NOAA solar-position equations; USNO twilight definitions; WCAG 2.2 | Astronomy engine not yet coded or tested |

**Persistence:** Design docs saved on branch and in PR #2. This memory note is preserved separately from the application repository.

## Next action

**Open blockers and risks:** Need design acceptance for night palette and whether world time should default to a fictional seasonally accurate clock or user opt-in actual sunrise. Approximate fictional time is not the local sunrise at a real user location.

**Next useful step:** User/designer approve nighttime visual; then in a separate implementation branch add a pure solar-phase model, CSS theme token system, preview slider and test suite, before changing the actual cottage renderer.

## Revisit when

PR #2 is approved or updated, dark-mode artwork is revised, or stage-two code begins. Verify current branch and dependencies before acting.
