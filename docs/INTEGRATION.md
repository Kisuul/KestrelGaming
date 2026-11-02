# Use shared Kestrel memory from another project

Keep KestrelGaming outside the application checkout. The application remains the
source of truth for its code and project rules; KestrelGaming holds the shared
contract, agent knowledge, skills, and handoffs.

## 1. Make the memory repository accessible

Use an existing authenticated GitHub connector or a separate clone with access to
[Kisuul/KestrelGaming](https://github.com/Kisuul/KestrelGaming). Do not place access
tokens in URLs, prompts, project files, or memory.

For a local environment, an example layout is:

```text
work/
  KestrelGaming/   shared memory checkout
  my-project/     application checkout
```

Clone only if a suitable checkout does not already exist:

```sh
git clone https://github.com/Kisuul/KestrelGaming.git
```

Optionally set `KESTREL_HOME` to the absolute memory-checkout path in your session.
This is a locator, not an auto-loader. Agents may also read files through a GitHub
connector without a local clone. Fetch related files at the same commit where possible;
record the resolved memory revision for substantial work so mutable `main` is not
mistaken for a fixed snapshot.

## 2. Supply a small bootstrap pointer

Use [the project-pointer example](PROJECT_POINTER.md) in session instructions or
merge it into the application's existing `AGENTS.md` when that edit is authorized.
Preserve all existing instructions. If no project edit is wanted, supply the pointer
through the agent host's supported session/project-instruction mechanism.

The agent must actually read the linked entrypoint and contract. A Markdown link,
environment variable, or file in an unrelated directory does not automatically load
anything. Confirm access in the intended host before relying on recall.

Do not copy `kestrel/`, `memory/`, or `skills/` into the application repository.
These skills use relative links into the whole memory checkout. They are repository
procedures, not an automatically installed ChatGPT/Codex plugin; a host adapter must
preserve that context if it exposes them as native skills.

## 3. Register the project here when useful

Inspect the target repository's canonical owner/name, current instructions, and source.
Create a profile from [the template](../kestrel/templates/PROJECT.md) under
`memory/projects/<owner>/<repo>/PROFILE.md`, with lowercase path components.
Create its `INDEX.md` and link it from [the project catalog](../memory/projects/INDEX.md).

Record only observed facts and user-stated requirements. Leave unknown behavior
explicitly unknown. Link architecture decisions to their authoritative project files.
Registration does not require changes to the target repository.

## 4. Work and save here

Use [recall](../skills/kestrel-recall/SKILL.md) at startup and
[remember](../skills/kestrel-remember/SKILL.md) when a task produces durable value.
Validate and synchronize records through the authorized workflow. A branch or local
checkout is not automatically visible to agents reading the default branch.

If memory cannot be read, continue independent work and report that limitation.
If it cannot be written, provide a concise handoff and its intended path without
claiming that it was saved. Do not create a fallback memory tree in the project.

## 5. Check the integration

In a disposable workspace, exercise a simple recall and save:

1. Have an agent identify the target owner/repository and the resolved memory revision.
2. Ask it to retrieve a relevant record and verify a changeable claim against source.
3. Have it prepare a new scoped lesson or handoff here, including its index entry.
4. Run validation, inspect the diff, and confirm the application has no memory files.
5. Synchronize only when already authorized, then read the saved record from the
   destination branch to verify persistence.

Use [the behavioral scenarios](../kestrel/evals/SCENARIOS.md) for deeper trials.
The static validator cannot prove that a host follows the contract.

## Migrating from a per-project seed

Preserve existing project-specific instructions and source docs. Move authorized
agent-only records to the matching scope here, translate metadata, preserve provenance,
and link replacements. Replace only the obsolete bootstrap portion with the short
pointer after checking for collisions. Do not delete old records until their useful
content is accounted for and that cleanup is in scope.
