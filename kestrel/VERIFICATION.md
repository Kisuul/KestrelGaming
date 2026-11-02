# Verification and evidence integrity

## Verification contract

For nontrivial changes, write or identify acceptance criteria before implementation. Distinguish requested behavior from an implementation choice. If criteria are implicit, state reasonable assumptions as such.

## Verification ladder

Select checks according to impact, not a mandated checklist:

1. **Diff inspection** — What changed? Were user edits preserved? Did tests, lockfiles, CI, migrations, or policies change unexpectedly?
2. **Focused checks** — Unit tests or reproductions nearest the change, syntax/type/lint where applicable.
3. **Integration checks** — Cross-boundary behavior, data compatibility, expected callers, failure paths.
4. **Negative checks** — Invalid inputs, error and boundary conditions, permission failures, regression cases.
5. **Independent checks** — Where risk warrants it, use a reviewer, protected acceptance tests, an isolated test environment, or a test oracle not generated from the implementation being judged.
6. **Environment fidelity** — Clearly distinguish local, staging, production, mocks, and simulated results. State environmental differences that limit conclusions.

A build succeeding is not proof of intended behavior; passing tests establish only the conditions checked.

## Integrity rules

- Do not alter or delete relevant acceptance tests just to get a pass.
- If tests must change because requirements changed, document the reason; review the changes independently from the implementation.
- Do not infer that a failure was pre-existing without checking a baseline or other supporting evidence.
- Record failing checks as failures, even if unrelated to this change.
- Avoid claiming performance, security, compatibility, or data correctness without corresponding evidence.
- Never claim tool execution that did not occur.

## Evidence log (use for substantial tasks)

| Criterion or claim | Evidence / command / source | Observed result | Limits |
| --- | --- | --- | --- |
| Example: expired session returns 401 | `pytest tests/auth/test_expiry.py -q` | Example only — NOT RUN | Local test; production not evaluated |

*Delete illustrative rows when creating a real report.*

## Completion gate

`COMPLETE` requires material acceptance criteria supported by proportionate verification. `PARTIAL` covers unfinished or materially unverified work. `BLOCKED` means no further meaningful authorized progress is currently possible. State what was not checked and why.
