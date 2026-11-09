---
schema: 1
id: 2026-11-05-hollowlumen-stage2-foundations-e1
kind: handoff
scope: project:kisuul/hollowlumen
status: active
evidence: observed
author: kestrel-gpt6-session-2026-11-05
created: 2026-11-05
updated: 2026-11-08
sources: "HollowLumen main 701dd55b983bf244a46187bc8bd8ef90d260ba8d; merged PR #2; new draft PR #3 head b46ab05157fb66aecc035bdcca0af2a6ecd39ba6; new draft PR #4 head 9bb8e78cfb71facbadb67bbded5acc9b1f08cf1e; local Node game tests and isolated V8 logic checks 2026-11-05."
---

# Stage 2 — independent theme and solar foundations

## Summary

**Goal and acceptance criteria:** Advance planned Stage 2 after design-spec merge, with baseline P0 tests, independent P1 theme and P2 solar math branches, and a hard P3 scene-integration gate until required verification passes.

**Task outcome:** PARTIAL

**Historical outcome detail:** PARTIAL. Two independent draft implementation PRs created. P0 domain tests pass, but reproducible dependency install/build remains BLOCKED by unavailable registry. P3 Home/Pip integration **not started**.

**Authorized scope/boundaries (historical; recheck on resume):** User said proceed along the agreed staged plan. Authorized in-scope branches/PRs and tests; no code merges, deployment, irreversible release or game-economy modifications.

**Target repo and revisions:** [Kisuul/hollowlumen](https://github.com/Kisuul/hollowlumen), main `701dd55b983bf244a46187bc8bd8ef90d260ba8d`; [PR #3](https://github.com/Kisuul/hollowlumen/pull/3) `feat/stage2-theme-foundation` at `b46ab05157fb66aecc035bdcca0af2a6ecd39ba6`; [PR #4](https://github.com/Kisuul/hollowlumen/pull/4) `feat/stage2-solar-model` at `9bb8e78cfb71facbadb67bbded5acc9b1f08cf1e`.

**Memory revision loaded:** KestrelGaming main `0fedc7d5abc5c0d714ada03228cf8c7a5be48b4d`, after the former design-memory PR #15 merged.

Formatting maintenance on 2026-11-08 separated the machine-readable outcome
from its original qualification. Historical project claims were not revalidated.

## Evidence

**P0 observations:** Current main design PR #2 merged. Original 12-file gameplay source snapshot matched original commit's intended manifest. `node --test tests/*.test.js` under Node v22.16.0 passed **9/9**. React/Vite packages are not installed or cached. Offline package-lock dry-run returned `ENOTCACHED` for `@tailwindcss/vite`; git/network/npm registry DNS unavailable, so no build or lockfile could be verified. The issues endpoint returned **410: issues disabled**; use PR/memory task records, not a fictitious issue.

**P1 theme:** Draft PR #3 adds only `src/theme/preferences.js`, `src/theme/theme-tokens.css`, `tools/build-theme-css.mjs`, `tests/theme.test.js` and an engineering work note. It **does not import the stylesheet into the current app or change UI/game saves**. The renderer/appearance state integration belongs to Lane C. Code Mode JavaScript checks on fetched exact source passed 4/4 test cases plus generated CSS equality.

**P2 solar:** Draft PR #4 adds only a pure `src/solar/solar.js`, `tests/solar.test.js`, and engineering note. It implements fictional 45°N seasonal solar elevation, bounded lighting weights, calendar validation, DST-aware approximate local-standard-time mapping and day length. Independent JavaScript execution of all 10 committed test cases passed; summer/winter theoretical daylight approx 15.62/8.77 hours at 45°N. The model does **not** implement location-accurate astronomical sunrise, lunar cycles or weather.

**No gameplay changes:** Both PRs are exactly one commit ahead and zero behind main, with distinct file sets. Neither changes `src/state/game.js`, `src/state/useGame.js`, `src/App.jsx`, `src/main.jsx` or the stylesheet.

| Command/check actually performed | Observed result | Limits |
| --- | --- | --- |
| `node --test tests/*.test.js` on original source snapshot | PASS 9/9 | Local Node 22.16.0; before new branches |
| `npm install --package-lock-only --ignore-scripts --offline --dry-run` | ENOTCACHED at npm registry entry | No lockfile produced |
| Exact committed P1 source evaluated via V8 test harness | 4/4 tests passed; generator output matches committed CSS | Not Node test runner / production bundler |
| Exact committed P2 source evaluated via V8 test harness | 10/10 test cases passed | Not Node test runner / production bundler |
| GitHub compare for both feature branches | Both 1 ahead / 0 behind; non-overlapping files | No merge or browser check |
| `npm run build` on new branches | NOT RUN | Dependencies unavailable |
| Full `python3 tools/validate_seed.py` on memory | NOT RUN | Needs complete synchronized checkout |

**Persistence:** App code committed to two feature branches/draft PRs. This handoff is on a separate Kestrel memory PR, not integrated until reviewed. No user geography or personal data was collected.

## Next action

**Blocker:** P0 reproducible production build and reviewed npm lockfile. The GitHub repository has Issues disabled, so track through PR descriptions and this handoff.

**Next bounded work:** In a network-enabled trusted checkout, inspect dependency lifecycle scripts, generate/review a lockfile, then run `node tools/validate-design-tokens.mjs`, `node tools/build-theme-css.mjs --check`, `node --test tests/*.test.js` and `npm run build` against each branch. Keep a representative Stage 1 save and smoke-test five-tab browser behavior. Escalate failures with evidence rather than merging by assumption.

**P3 hold:** Do not wire Home/Pip lighting until P0 is green and P1/P2 pass their full Node/browser gates. Then integrate via a **new** scene branch, with temporary 24-hour preview and no game-clock/economy coupling.

## Revisit when

Any PR head, source schema, dependency lockfile, runtime environment, desired solar semantics or original designer visual feedback changes. Reconfirm exact current branch and review status before relying on this snapshot.
