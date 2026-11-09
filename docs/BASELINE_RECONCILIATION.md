# Shared baseline reconciliation

Prepared on 2026-11-08 by Flint for the owner's request to reunify the upstream
Kestrel foundation and Cosmic Dance's agent-development baseline.

This change combines the two shared `main` histories. It does not merge the
individual agent homes or activate a Discord/agent runtime.

## Source revisions

| Source | Commit |
| --- | --- |
| Kisuul/KestrelGaming `main` | `dbe0164e3dbdcfa65fd6a4a81434ae0e11eb259c` |
| cosmicdance-4-2-0/KestrelGaming `main` | `4cb17b01d7ac50bd15ed69e84eccee0d32035a8b` |
| Common ancestor | `c268a4d0be121738cbfdb0d7a90de7874299c0f2` |

At these revisions, upstream has 31 unique commits and Cosmic Dance has 13.
The integration commit has both source heads as parents, preserving their
ancestry rather than replacing either history with a snapshot.

Upstream contributes its current common skills, including the PixiJS vendor
and integrity checks, and existing project records. Cosmic Dance contributes
the seven-agent roster, character templates, role-pickup and structure
documentation, structural tests, and Auralprinter project records.
The shared operating contract and permission protocol are unchanged.

## Reconciliation details

- The sole textual merge conflict is `memory/projects/INDEX.md`. Both
  HollowLumen and Auralprinter entries are retained.
- The existing validator rejects five upstream HollowLumen handoffs and one
  Cosmic Dance Auralprinter handoff because explanatory prose follows their
  machine-readable outcome. The outcome is put on its own line; the original
  qualified statement is retained separately. These are formatting repairs,
  not new project-status assessments.
- Two agent documents incorrectly describe Cosmic Dance's already-merged
  ensemble PR #1 as unmerged. They now distinguish the integrated catalog from
  an operational agent runtime.
- Imported Markdown hard breaks use backslashes instead of trailing spaces
  so the combined change passes the repository's whitespace check.
- No tests or validation rules are weakened. No open feature PR is merged.

## Agent homes remain independent

The [roster](../agents/ROSTER_V1.json) continues to locate individual profiles
on Cosmic Dance's `agents/<id>-v1` branches. Latch's journal, specialist skills,
and teaching lab remain on Latch's home branch; they are not silently promoted
into the common catalog by this merge. The same separation applies to the
other six agents and to team/experimental branches.

A shared baseline and an individual home need not have identical heads.
Use the existing [role-pickup procedure](AGENT_PICKUP.md) to pin both revisions
when composing a common contract/skills checkout with an agent home. Updating
the home itself requires a reviewed merge that retains its selected identity,
indexes, profile, tests, and continuity records. Never reset an agent branch
to the shared baseline.

## Bringing both main branches to one commit

1. Review this integration against both source heads and run the normal checks:
   `python3 tools/validate_seed.py`,
   `python3 -m unittest discover -s tests -v`, and
   `git diff --check <upstream-source-head> HEAD`.
2. Recheck both remote heads before landing. If either moved, incorporate and
   review the new commits, then rerun checks; the snapshot above is not a lock.
3. Merge the integration PR into Kisuul's `main` using a **merge commit**.
   Do not squash or rebase this reconciliation: both parent histories need to
   remain ancestors of the resulting shared head.
4. Fetch the actual resulting upstream commit. Confirm Cosmic Dance's current
   `main` is its ancestor, then fast-forward Cosmic Dance's `main` to that exact
   commit through the authorized repository workflow. Do not create a second
   merge commit in the fork or force-update its branch.
5. Verify both remote `main` refs resolve to the same full SHA. Only then is
   shared-baseline synchronization complete. Agent-home synchronization remains
   a separate operation.

Opening the integration PR does not itself synchronize either default branch.
Normal review and owner merge decisions still apply. Existing draft curricula,
team contracts, agent history, and UDB work remain on their current branches.

## Verification limits

The validator and tests check repository structure, examples, and the existing
regressions. They do not certify agent competence, instantiate the organization,
or test the proposed UDB memory integration. Test results for this exact
integration are recorded in the pull request, rather than copied from old runs.
