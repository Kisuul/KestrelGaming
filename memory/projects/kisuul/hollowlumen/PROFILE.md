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
sources: "Repository main ac0317e250bef11c1f12abebe7be023aa41ecb47 and README.md; PR #1 head 917ca66cc811052898349f25de0d7c25255d70e6."
---

# Kisuul/hollowlumen

## Summary

- Project: **Lumenette Hollow**, a cozy fantasy life sim with living yarn companions, cottage decorations, short wander activities, and low-pressure offline gathering. The [original README](https://github.com/Kisuul/hollowlumen/blob/main/README.md) is the authoritative product pitch.
- On inspection of main at `ac0317e`, only `README.md` was present although it described a playable prototype.
- First code was added on the separate feature branch `feat/playable-hollow-v0-1` at `917ca66`; [draft PR #1](https://github.com/Kisuul/hollowlumen/pull/1) is open against `main`.
- The prototype uses React, Vite, TanStack Router, Tailwind CSS v4 and Zustand; pure, testable game mechanics are in `src/state/game.js`. The [prototype status document](https://github.com/Kisuul/hollowlumen/blob/feat/playable-hollow-v0-1/docs/PROTOTYPE.md) distinguishes implementation from aspiration.
- Product constraints: optional short sessions; no pressure/streaks; original yarn-creature art; fair, non-paywall monetization if ever added; mobile-friendly interface; real native widgets and multiplayer deferred.
- Known unknowns: final visual direction and original designer acceptance; package install/build/browser quality; hosting, backend, licensing and commercial rights.

## Evidence

- Observed via connected GitHub repository metadata, default-branch listing, README, commit comparison and PR creation on 2026-11-05.
- Remote feature-branch contents matched the local working source for all 12 added files.
- Local `node --test tests/*.test.js`: 9/9 tests passed; JSX syntax parsing of three files passed.
- **Not verified:** dependency installation, production browser build, interactive QA and any cloud deployment. The local environment could not resolve the npm registry.
- Do not infer that descriptions of native widgets, friend visits, and paid packs are implemented. They are scoped future features or simulations.

## Revisit when

When PR #1 changes, the original designer clarifies goals, production dependencies are installed, the app is tested on devices, or release and licensing decisions are made.
