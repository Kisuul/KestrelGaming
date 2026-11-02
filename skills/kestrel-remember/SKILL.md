---
name: kestrel-remember
description: Save useful Kestrel lessons, decisions, project context, or resumable task handoffs in the shared Kisuul/KestrelGaming memory repository. Use after meaningful work or before interruption; distinguish evidence from inference and keep agent memory out of application repositories.
---

# Preserve useful Kestrel knowledge

1. Read [the memory protocol](../../kestrel/MEMORY_PROTOCOL.md) and
   [state protocol](../../kestrel/STATE_PROTOCOL.md). Identify what a later agent will
   need that cannot be recovered cheaply from current project source.
2. Inspect [the indexes](../../memory/INDEX.md) and existing records. Select the narrowest
   scope: shared knowledge, exact owner/repository, or an established agent identity.
   Update an existing fact only when it is the same fact; otherwise add a focused record.
3. Use [MEMORY](../../kestrel/templates/MEMORY.md),
   [PROJECT](../../kestrel/templates/PROJECT.md), or
   [HANDOFF](../../kestrel/templates/HANDOFF.md). Fill all metadata and remove placeholders.
   Record exact sources/revisions, actual check outcomes, uncertainty, and revisit triggers.
   For handoffs, distinguish work implemented from work verified and work synchronized.
4. Save within KestrelGaming, even while working on another repository. Link back to
   project-owned source instead of copying a competing version. Exclude credentials,
   raw transcripts, and unnecessary personal details.
5. Resolve contradictions by evidence. Preserve uncertainty as `draft`; supersede with
   an explicit replacement link when justified. Register the record in its scope index
   and register any new project/agent index in its catalog.
6. Follow [contributing](../../CONTRIBUTING.md): inspect the complete diff, run the
   validator and relevant tests, and reconcile concurrent remote changes. Synchronize
   only through the task's existing authorization; do not request it again if already given.
7. Report the file and confirmed destination commit, or say **local only / not saved**
   if synchronization was unavailable. Do not claim that other agents can recall an
   unintegrated branch by default. Do not add fallback journals to the application repo.

Skip a memory write when it would merely preserve routine chatter or duplicate readily
available source. Extract a skill only when there is a reusable procedure with clear
conditions and honest evidence of what has and has not been exercised.
