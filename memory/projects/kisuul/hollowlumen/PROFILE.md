---
schema: 1
id: 2026-11-05-hollowlumen-profile-a1
kind: profile
scope: project:kisuul/hollowlumen
status: active
evidence: observed
author: kestrel-gpt6-session-2026-11-05
created: 2026-11-05
updated: 2026-11-05
sources: "HollowLumen README; PR #1 merged at 2026-11-05T11:39:21Z; main 4e2ade8a019f45bc39a6ea0d17b949eb4ced97b9; PR #2 merged as 701dd55b983bf244a46187bc8bd8ef90d260ba8d; Stage 2 branches b46ab05157fb66aecc035bdcca0af2a6ecd39ba6 and 9bb8e78cfb71facbadb67bbded5acc9b1f08cf1e; user feedback 2026-11-05."
---

# Kisuul/hollowlumen

## Summary

- **Lumenette Hollow** is a cozy, time-light fantasy life sim about living yarn companions, decorating a cottage, short adventures and low-pressure idle gathering. The [README](https://github.com/Kisuul/hollowlumen/blob/main/README.md) is the product pitch.
- Initially, `main` at `ac0317e` contained only README, despite claiming a playable prototype.
- The first source implementation landed via [PR #1](https://github.com/Kisuul/hollowlumen/pull/1), merged 2026-11-05, with `main` at `4e2ade8a019f45bc39a6ea0d17b949eb4ced97b9` on latest inspection.
- User reports hands-on playtesting found stage-one functionality worked as expected and gives **provisional** sign-off. This is **user-stated acceptance evidence**, not proof of CI/build/accessibility or the original designer's visual approval.
- The original designer approved the **daytime visual reference** and the **nighttime palette choices**, per the user on 2026-11-05. The coherent design language is documented in [HollowLumen PR #2](https://github.com/Kisuul/hollowlumen/pull/2), which is **merged** on 2026-11-05. The authoritative spec is `docs/design/DESIGN_SYSTEM_v1.md`; exact DTCG design tokens are `docs/design/tokens/visual.tokens.json`. Implemented UI, actual astro logic and final fonts remain unverified.
- Implementation: React, Vite, TanStack Router, Tailwind CSS v4 and Zustand; domain logic `src/state/game.js`; see [prototype notes](https://github.com/Kisuul/hollowlumen/blob/main/docs/PROTOTYPE.md).
- Constraints: 1–5 minute optional sessions; no guilt/streak pressure; original yarn-ball art; friendly cosmetics without paid power; mobile-friendly layouts. Native widgets, multiplayer, cloud accounts and payment infrastructure are deferred.
- Unknowns: original designer's preferred exact look; production build/browser/accessibility QA; hosting, licensing, distribution strategy.

## Evidence

- GitHub connector fetched repository state, README, prototype notes, CSS, main commit and PR status on 2026-11-05.
- PR #1 and PR #2 are confirmed merged by GitHub. PR #2 included seven design/tooling files, with no CSS/runtime changes. Stage 2's [theme foundation PR #3](https://github.com/Kisuul/hollowlumen/pull/3) and [solar model PR #4](https://github.com/Kisuul/hollowlumen/pull/4) are separate draft PRs with no gameplay edits.
- Stage-one playtesting and provisional approval were stated by the user in this conversation; test environment details not supplied.
- Existing nine deterministic game tests passed again locally against an exact source snapshot (Node v22.16.0, 2026-11-05). The registry is unreachable; lockfile creation, dependency installation, production build and browser QA remain unverified. See the current Stage 2 handoff.

## Revisit when

P0 build/lockfile becomes reproducible, Stage 2 PRs change or merge, the designer reviews rendered screens, or technical checks contradict these reports.
