---
schema: 1
id: 2026-11-18-udb-type-gate-coverage-c7
kind: handoff
scope: project:idiw-net/universal_discord_bot
status: active
evidence: observed
author: claude-code-session-2026-11-18
created: 2026-11-18
updated: 2026-11-18
sources: "User request 2026-11-18 to redo PR #4 (Codex docs/CI accuracy pass) better; UDB master 61fdf41; local branch ci/type-gate-coverage-20261118; checks run locally with CPython 3.12.11, discord.py 2.7.1, mypy 1.20.2."
---

# UDB: make the verification gate cover what it claims to

## Summary

**Goal and acceptance criteria:** the user said PR #4 (merged 2026-11-14, a
Codex docs-only pass that reworded the CI description and renumbered a
checklist) could be done much better. Redo its remit, accurate verification CI
guidance, against current master. Make every factual claim true, back each one
with a check, and prevent the drift from recurring.

**Task outcome:** PARTIAL

Implemented, verified locally, and opened as
[PR #16](https://github.com/IDIW-NET/Universal_Discord_Bot/pull/16) at the
user's request (commit `cb6b389`). Not merged; the owner reviews and merges.

**Authorized scope and boundaries (historical; recheck on resume):**
verification CI maintenance, which AGENTS.md explicitly permits. No product
behaviour, profiles, dependencies, version metadata, or ROADMAP scope records.

**Target repository, branch, and commit:** `IDIW-NET/Universal_Discord_Bot`,
branch `ci/type-gate-coverage-20261118` (pushed), commit `cb6b389` on top of
`master` at `61fdf41`.

**Memory revision loaded:** KestrelGaming `main` at `504da1d`; no prior UDB records.

## Evidence

**Confirmed observations with sources:**

- CI, `scripts/verify.py`, AGENTS/CONTRIBUTING/README and
  `docs/CAPABILITY_CONTRACTS.md` all hard-coded `mypy bot services modules`.
  Since 0.5.0, `contracts/`, `scripts/`, and the `tests/*_examples` capability
  providers also exist. C1, C2a and C2b changelog entries show the
  `contracts`/example checks being run by hand.
- `contracts/` is in fact covered, because mypy follows imports from
  `modules/`. A planted error there was caught. The initial suspicion that it
  wasn't was wrong.
- **Real gap:** realistic Protocol drift planted in both alternative providers
  (`ticket.create.v1` return widened to Optional; `guild.role_selection.v1`
  parameter retyped) passed the CI mypy gate **and** all 156 tests that
  exercise those providers. Only a widened mypy run caught it.
- `scripts/` was never type-checked; strict mypy found 17 errors in
  `command_hygiene.py`, from two causes: an untyped `**dict[str, object]`
  passed to `discord.Client`, and a `type: ignore` with the wrong error code.
- The rest of `tests/` has 593 strict errors. That is deliberate and out of scope.
- Docs drift: AGENTS.md implied 0.5.0 had not started (PRs #8–#14 merged).
  README said a version bump touches three files with "no other location"; in
  fact `tests/test_version.py` and `tests/test_docs_invariants.py` pin it too,
  and eight docs must name it. PR #4's own changelog lines sat in
  `[Unreleased]` although its merge `8eec490` is an ancestor of the v0.4.5
  merge `d04b893`.

**Decisions and rationale:**

- Make `[tool.mypy] files` in `pyproject.toml` the single source of truth, with
  plain `python -m mypy` everywhere. A hard-coded target list repeated in seven
  places is what drifted. The command stays runnable directly, which satisfies
  the AGENTS.md "don't hide commands behind helpers" rule.
- Add `tests/test_type_check_coverage.py` as a guard. A mutation test showed it
  names a new unregistered top-level package and a new `tests/*_examples`
  package.
- Fix `command_hygiene.py` with exactly the same `discord.Client` call shape;
  no reliance on discord.py treating `application_id=None` as absent.
- Add `.gitattributes` (`* text=auto eol=lf`). On a default Git for Windows
  checkout (`autocrlf=true`) the documented `verify.py` failed
  `ruff format --check` on 228 files that are LF in the repo. Renormalizing
  changed no stored file.
- Lesson for Windows sessions: Git Bash `grep -q $'\r'` does not reliably
  detect CRLF; use `git ls-files --eol`. PowerShell `git commit -F -` with a
  here-string fails (the message becomes a pathspec); commit with
  `-F <file>` instead.
- Leave ROADMAP.md approval records untouched; those are the owner's.

**Changed files and uncommitted state to preserve:** `.github/workflows/verify.yml`,
`pyproject.toml`, `scripts/verify.py`, `scripts/command_hygiene.py`,
`tests/test_ci_workflow.py`, `tests/test_verify_script.py`, new
`tests/test_type_check_coverage.py`, AGENTS.md, CONTRIBUTING.md, README.md,
CHANGELOG.md, `docs/CAPABILITY_CONTRACTS.md`. The working tree is at
`C:\Claude\Universal_Discord_Bot` on the user's machine.

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| `mypy bot services modules` on master | 97 files, pass | CPython 3.12.11, Windows |
| Planted drift in both providers vs. CI gate and 156 related tests | Gate and tests pass (drift missed) | Scratch worktree at `61fdf41` |
| Same drift vs. widened gate | 4 errors in 2 files (caught) | Same |
| `python -m mypy` on branch | 126 files, pass | Same |
| Guard mutation test (new package plus new examples dir) | Both named in failures | Scratch worktree |
| Full `scripts/verify.py` and `scripts/doctor.py` on final tree | 1713 passed; ruff clean (233 formatted); mypy 126 files; all 4 checks; doctor OK 13 | Windows, LF working tree |
| GitHub Actions Verify on PR #16 | In progress when this was written | Linux, Python 3.12 |

**Persistence:** UDB work is pushed and in PR #16. This memory record is on
KestrelGaming branch `memory/udb-type-gate-coverage-20261118`, committed
locally and not pushed.

## Next action

**Open blockers or risks:** CI on PR #16 had not finished when this was
written. Owner review and merge are pending.

**Next useful step:** confirm Verify passes on PR #16 and respond to review.
After merge, mark this handoff `archived` and update the PROFILE's mypy-gate
note.

## Revisit when

The branch is merged or abandoned, or `master` changes the mypy gate or adds a
package before this lands.
