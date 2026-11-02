# State and continuity protocol

KestrelGaming is the durable memory home. Use task notes when work is substantial,
interrupted, or likely to pass between sessions. Skip records with no future value.

## Save

1. Distill what the next agent needs: goal, actual scope, current revision, discoveries,
   decisions, changed files, checks and outcomes, blockers, and the next useful action.
2. Use the [handoff template](templates/HANDOFF.md). Save under
   `memory/projects/<owner>/<repo>/handoffs/<unique-id>.md` **in this repository**.
   Index it in that project's `INDEX.md`. Use [the memory protocol](MEMORY_PROTOCOL.md)
   for metadata, naming, evidence, and freshness.
3. Split reusable knowledge from temporary progress: a lasting lesson belongs in a
   separate project or shared record; a repeatable procedure may become a skill.
4. Inspect the diff and run validation. Save through the already-authorized workflow;
   do not request authorization again when the current task already supplies it.
5. Report the resulting path and commit when synchronized. A local file or unpushed
   commit is **local only**. A branch is not the shared default branch until integrated.

Runtime task state may complement these files. Do not put `.kestrel-work/`, agent
journals, or duplicate skill systems in the application repository. Use runtime
scratch outside both repositories for disposable logs and experiments.

If write access is unavailable, provide the concise handoff in the task response or
an already-authorized durable destination, identify the intended path here, and state
that shared memory was not updated. Do not stop unrelated authorized project work.

## Resume

1. Read the current request, contract, relevant indexes, and the matching handoff.
2. Inspect the actual project location, branch, commit, working tree, and instructions.
   Resolve differences between remembered and current state before acting on them.
3. Distinguish a proposed plan, an implemented change, an executed check, and a remote
   save. Do not infer one from another. Historical authorization is not a new grant.
4. Protect unrelated changes. Recheck stale evidence where it affects the task.
5. Continue from the highest-value authorized action. Update the handoff at meaningful
   milestones; close it with an explicit outcome when done.

## Concurrent work

Give separate tasks separate files. Update an existing handoff only for that same
task. Before synchronizing, inspect the latest remote state and merge both agents'
useful information. Never force-push, overwrite a conflicting record blindly, or
resolve disagreement by declaring the newest text true. See [contributing](../CONTRIBUTING.md).

After repeated failures, reconsider the evidence and change the diagnosis or test.
Memory should prevent repeated failed approaches, not preserve an endless transcript.
