# Maintaining Kestrel common memory

Keep changes small enough that the next agent can understand why a record exists.
Use [the memory protocol](kestrel/MEMORY_PROTOCOL.md) and the narrowest useful scope.
Source-backed memory and reusable procedures belong here; application edits belong
in their own repositories.

## Update procedure

1. Inspect the working tree and current remote branch before editing. Preserve others'
   work. Use an isolated branch or worktree when concurrent tasks would collide.
2. Read the relevant index and existing records. Add or update a focused record,
   maintaining its evidence, dates, and revisit condition. Update its scope index too.
3. Read the full diff, including new files. Review changes to the contract, agent
   entrypoint, permissions, protocols, and CI deliberately; memory updates must not
   silently rewrite the operating contract.
4. Run `python3 tools/validate_seed.py`, `python3 -m unittest discover -s tests -v`,
   and `git diff --check`. These are structural checks, not behavioral certification.
5. Commit and synchronize through the owner's authorized workflow. Use a branch and
   review when required; do not bypass repository controls. Existing task authorization
   remains valid, so do not repeatedly ask for the same permission.
6. Confirm the remote commit and destination branch before saying memory is shared.

## Concurrent writers

Prefer separate record files over a shared rolling log. A writer may add a unique
suffix to avoid filename/ID collisions. Index conflicts should retain both useful
links; record conflicts require reading both claims and their evidence.

For an ordinary clone, fetch the remote and integrate its updates before a normal
fast-forward push. If the push is rejected, inspect the new commits and reconcile;
never force-push to erase another writer. API clients should base trees on the current
tree and use an expected-head check when moving the branch ref. A mismatch means
inspect and rebuild, not retry blindly. Never include unrelated staged files.

## Skill changes

Each reusable skill has a concise `SKILL.md` with `name` and `description` frontmatter,
an actionable procedure, and explicit relevant references. Register it in
[the skill index](skills/INDEX.md). Keep the whole repository available because these
skills refer to its shared protocols. Optional `agents/openai.yaml` files provide host
display metadata; they do not install or execute a skill.

Test any added script by running it. Use realistic read/resume/write trials when a
procedure changes materially, and distinguish those trials from the structural tests.
Do not present draft procedures or unrun evaluation scenarios as proven capability.
