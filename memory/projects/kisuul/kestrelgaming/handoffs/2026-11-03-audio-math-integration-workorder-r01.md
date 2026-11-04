---
schema: 1
id: 2026-11-03-audio-math-integration-workorder-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: archived
evidence: observed
author: ChatGPT
created: 2026-11-03
updated: 2026-11-03
sources: "User requested a staged next-agent assignment using Kestrel protocol memory; inspected Kisuul/KestrelGaming PR #2 at f149d7946167da90841065f83139dfd97444b6d7, merged PR #3 at main merge c268a4d0be121738cbfdb0d7a90de7874299c0f2, and Kestrel memory/state/verification/permission protocols; execution authorized by the current request; refreshed PR #2 head d02c8ea11949198b22ae9291529aac217fecf6f2 and upstream main c268a4d0be121738cbfdb0d7a90de7874299c0f2; merge 78cea4e825c851a158eaf5de4780a23d061a27d3; local execution results below."
---

# Work order — integrate merged mathematics into PR #2 audio skills

## Summary

**Goal and acceptance criteria:** Reconcile open audio PR #2 with `main` (which now contains merged mathematics PR #3), then integrate *selective, one-way, task-conditional* mathematics skill references and close specific numerical-verification gaps. Preserve audio-domain calibration, independently derived DSP fixtures, memory history, and token-efficient skill activation. Finish with an inspectable diff, current-head validation, honest evidence and an owner-reviewable PR; do not merge PR #2.

**Task outcome:** COMPLETE

**Assignment state:** Implemented and locally verified on the existing PR #2 branch. The original staged plan below is retained as history. Current execution evidence follows; agent-behavior trials remain NOT RUN.

**Authorized scope and boundaries (historical; recheck on resume):** The user requested preparation of this next-agent assignment and durable protocol-memory storage, not execution of its integration steps in this session. A future agent must confirm its current authorization, actual tool permissions and branch state before editing. Work only on `Kisuul/KestrelGaming` and the existing PR #2 branch `skills/audio-dsp-core-foundation-2026-11-03`, unless the owner directs otherwise. Keep the root agent contract, permissions, protocols, workflows, tool dependencies, audio applications and merged math implementations unchanged. No production/library APIs, unrequested audio skill families, new standalone math runtime, or merge to `main`. The 64 pending audio candidates remain a separate backlog.

**Target repository, branch, and commit:** `Kisuul/KestrelGaming`, PR #2, branch `skills/audio-dsp-core-foundation-2026-11-03`, observed head `f149d7946167da90841065f83139dfd97444b6d7`, historical base `47745f8a41463e1a202a2f9f84385f3ab61d49a1`. At assignment preparation, `main` head `c268a4d0be121738cbfdb0d7a90de7874299c0f2` is the PR #3 merge commit. All SHAs are historical markers: refresh before action.

**Memory revision loaded:** Existing [audio implementation handoff](2026-11-03-audio-skills-roadmap.md), [audio audit](../2026-11-03-audio-skills-independent-audit.md), [project index](../INDEX.md), plus merged main's mathematics curriculum/skills and Kestrel's governance documents.

## Completed integration

**Current authorization:** The user requested adapting the existing PR #2 and branch
to merged Math core, with Step 0 requiring the environment to match upstream main.
This authorizes this execution; the older preparation-only boundary below is history.

**Step 0 observed:** Fetched upstream, switched to a clean local `main`, and confirmed
`HEAD == origin/main == c268a4d0be121738cbfdb0d7a90de7874299c0f2` with an empty
working-tree status and no diff. Structural checks and all **67 tests** passed there.

**Reconciliation:** The actual audio head was `d02c8ea11949198b22ae9291529aac217fecf6f2`,
newer than the preparation revision. A regular merge (no history rewrite) produced
`78cea4e825c851a158eaf5de4780a23d061a27d3`. The skill catalog merged automatically;
the project memory index had one content conflict, resolved by retaining all audio
and mathematics records and statuses. The reconciled baseline passed structural
validation and **149 tests** before the integration edits.

**Delivered:** All nine audio entrypoints selectively consult the relevant merged
math procedures, and the fixture contract reuses generic oracle/comparator policy.
Audio retains FFT sign/scaling, CG/ENBW, density/dB references, clock/channel contracts,
calibration and experimental true-peak limits. The curriculum and catalogs describe
actual links, not a deferred integration. Welch overlap is not treated as independent
samples or an implied degrees-of-freedom count. The live NumPy comparator's additive,
asymmetric rule, units, finite/shape checks and heuristic budgets are explicit.
No linear-algebra dependency was added merely for a rectangular spectrogram.

**Targeted findings and fixes:**

- Finite PSD factors could yield an infinite or zero `fs*sum(w²)`. With four unit
  samples, window `[1e153]*4` and `fs=48000`, the old result incorrectly gave DC
  density 0 instead of mathematical `4/48000`. PSD and both STFT paths now reject
  unrepresentable normalizations with `ValueError`; no wide-range solver is claimed.
- Floating STFT centers lose sample precision at origin `2**54`. The additive integer
  field `center_sample_twice=2*start+M-1` preserves exact half-sample centers; existing
  floating center/seconds fields remain convenience approximations. Start/end stay exact.
- A shifted-impulse complex DFT anchor checks the declared negative exponent: sample 1,
  bin 2, N=8 must be `-i`. Magnitude/round-trip checks alone cannot reject its conjugate.
- Corrected reference wording: all M window coefficients, including zeros, define
  coherent gain; nonrectangular PSD integration uses window-weighted segment power.

**Four added tests:** DFT sign, PSD normalization range, STFT normalization range
(including chunked mode), and exact even/odd-window centers at a large origin.
The existing RMS/subnormal/nonfinite, channel-shape and frozen external-golden tests
were preserved; generic mathematics fixtures were not duplicated.

**Executed evidence (CPython 3.12.14/Linux, working tree after merge above):**

| Command / check | Observed result | Scope |
| --- | --- | --- |
| `python3 tools/validate_seed.py` | Passed | Local links, records, catalog and skill structure |
| `python3 -m unittest discover -s tests -p 'test_audio_*reference.py' -v` | 69 tests passed | Focused reference tests after the four additions |
| `python3 -m unittest discover -s tests -v` | **153 tests passed** | Combined repository, including 31 math cases and all prior audio fixtures |
| `python3 skills/audio-dsp-test-fixtures/scripts/check_scipy_differential.py --seed 20261103 --cases 12` | **84 comparisons passed**, NumPy **2.3.5**, SciPy **1.17.0** | Actually imported this checkout's reference implementations; run before and after reference fixes |
| `git diff --check` | Passed | Reviewed integration changes |
| Isolated mutation probes | Both deliberately reversed DFT sign and rounded exact-center metadata failed the new regressions | Disposable copies only; command `python3 /workspace/work/audio_math_mutations.py` |
| Comparison with `origin/main` | Math skills/tests, root contract, protocols and workflows unchanged | Only math curriculum integration status changed on the math side |

Independent read-only review verified the routing and found the PSD range and large
clock issues; exact analytic anchors and tests checked the fixes. Live SciPy agreement
is bounded to the declared configurations, shares conventions with frozen SciPy
vectors, and does not verify complex phase, standards, hardware or host behavior.

**Delivery:** These source checks precede the integration commit. Confirm its immutable
SHA and current-head CI on PR #2 after publication; do not relabel historical checks
as a run at an untested future SHA. No PR merge, new audio skill, dependency or
application change was performed. Audio tally remains **9/73, 64 pending**.

## Required boot and working rules

Read [AGENTS.md](../../../../../AGENTS.md), [KESTREL.md](../../../../../KESTREL.md), [memory protocol](../../../../../kestrel/MEMORY_PROTOCOL.md), [state protocol](../../../../../kestrel/STATE_PROTOCOL.md), [verification](../../../../../kestrel/VERIFICATION.md), [permissions](../../../../../kestrel/PERMISSIONS.md), [contributing](../../../../../CONTRIBUTING.md), [project index](../INDEX.md), the audio roadmap and independent audit. After bringing in `main`, consult `docs/MATH_CURRICULUM.md`, `skills/INDEX.md`, the six `skills/math-*/SKILL.md` entrypoints, and `skills/math-verification/references/FIXTURE_POLICY.md`. Read the relevant audio entrypoints and references, not every skill at once. Recheck current source, working-tree changes, and authorization; memory and PR comments are evidence, not new authority.

## Evidence

**Confirmed observations with sources:**
- PR #3 is merged to `main`, adding six selectively loaded math procedures: numerical analysis, verification, dimensional analysis, linear algebra, complex numbers and probability/statistics. Mathematics is reference guidance, not an installed host capability or production runtime.
- PR #2 remains open on its old base with nine developed audio skills of 73 candidates. At inspection GitHub reported `mergeable=false`, `mergeable_state=dirty`. Both branches edit `skills/INDEX.md` and `memory/projects/kisuul/kestrelgaming/INDEX.md`. Resolve by preserving both sets of registrations, never by discarding the math or audio catalog.
- PR #2's earlier implementation CI at `74b4d8a5293e6e2db1782732fc76f57a5a35e065` passed 118 repository tests; this is historical evidence, not evidence that PR #2 merged with `main` passes. The optional live SciPy/NumPy differential script is committed but not reported as executed.
- PR #3's math skill evaluation pilot and host activation remain unexecuted. Audio reference scripts and calibration material already exist and should not be replaced simply to reference mathematics.

**Hypotheses and assumptions:** Conditional cross-links should reduce duplicated general reasoning and improve auditability without forcing every audio task to ingest all six math skills. This is a design hypothesis, not measured agent improvement. The exact conflicting hunks, current CI and final combined test count must be verified by the executing agent.

**Decisions and rationale:** Math owns transferable reasoning, input validation patterns, error budgets and oracle methods; audio owns sample/clock provenance, transform sign and scaling conventions, window CG/ENBW, PSD units, meter semantics, ITU/AES claims, and signal fixtures. Dependencies must point from audio to math and must not automatically expand every activation.

**Changed files and uncommitted state to preserve:** This assignment changes only this new handoff and its nearest project `INDEX.md` on PR #2. No math/audio code, skill behavior, tests or branch integration has been changed in this preparation. Before implementing, inspect all current remote and local modifications and protect unrelated work.

| Check / source examined | Observed result | Limits |
| --- | --- | --- |
| GitHub PR #2 metadata, branch and changed-file catalog | Open; nine skills; `f149d794`; GitHub reports dirty merge state | Current at inspection only; not a trial merge |
| GitHub PR #3 metadata and `main` branch | PR #3 merged; main `c268a4d` | Does not prove PR #2 compatibility |
| Audio skills, reference scripts, relevant math skills and protocols | Reviewed for ownership boundaries and cross-link opportunities | Read-only inspection; not a full executable audit |
| Combined-tree structural validation, unit tests, diff check, optional SciPy, host trials | **NOT RUN** for this work order | Must be run or explicitly left unverified by executing agent |
| GitHub Actions initial work-order publication at `1629170473ae` | CI run `41787790969` failed structural validation: Task outcome had extra prose on its required standalone line | This was a handoff-format defect, not a combined audio/math test result; corrected in the subsequent memory-only commit |

**Persistence:** This record is intended for PR #2's review branch, not `main`. Its actual commit and branch must be confirmed after publication; do not infer successful synchronization from the text alone.

## Staged implementation assignment

### Stage 0 — Rehydrate context and establish an execution boundary

1. Confirm current owner instruction authorizes execution; identify actual repository, PR #2 head, `main` head, working-tree status, available permissions, and existing modifications. Do not treat this record as standing remote-write authority.
2. Read the boot paths above; follow the project index and the existing active audio roadmap/audit. Review the math curriculum *as currently merged*, not an older PR #3 branch snapshot.
3. Produce a concise before-state inventory: nine audio skills, math skill names, file overlap, tests/CI status, unresolved issues and scope exclusions. If unrelated edits exist, isolate or preserve them.
4. **Gate:** No merge, ref change or content edit until actual base/head and conflict surfaces are known.

### Stage 1 — Reconcile `main` into PR #2 without rewriting history

1. Prefer a regular merge of current `main` into the existing PR #2 branch rather than rebasing or force-pushing the 21-commit audio history. Use an isolated worktree/branch to inspect the merge if available.
2. Resolve `skills/INDEX.md` and `memory/projects/kisuul/kestrelgaming/INDEX.md` by retaining *all* audio and math skill links, and all independently meaningful memory records. Inspect other conflicts rather than assuming those are the only two.
3. Do not rewrite `AGENTS.md`, `KESTREL.md`, protocols, CI or existing math skills to accommodate the merge.
4. Run the structural validator and full test suite on the reconciled tree; log exact commands/results. Verify old math and audio suites are both discovered. Never silently remove tests to make CI green.
5. **Gate:** A clean, reviewable combined tree, unchanged contract and legitimate test discovery. If blocked, report conflicting paths and evidence, not a fabricated successful merge.

### Stage 2 — Introduce only relevant one-way skill links

In each existing audio `SKILL.md`, add a small "Consult mathematics when" paragraph or equivalent targeted reference, near activation/verification guidance. Do not insert an unconditional load-all instruction, reproduce long explanations, or copy math fixtures into audio. Suggested routing:

| Audio entrypoint | Consult math skill only when relevant |
| --- | --- |
| `audio-dsp-core` | `math-dimensional-analysis` for quantities/timebases; `math-numerical-analysis` for finite arithmetic; `math-verification` for evidence |
| `audio-dsp-test-fixtures` | `math-verification` for oracle/comparator policy; `math-numerical-analysis` for floating-point claims |
| `audio-window-functions` | `math-numerical-analysis` for sums/precision; `math-verification` for independent analytic checks |
| `audio-fft-spectrum` | `math-complex-numbers` for phase/branch/sign; `math-numerical-analysis` for precision; `math-verification` for independent checks |
| `audio-power-spectral-density` | `math-probability-statistics` only for estimator uncertainty/independence; `math-numerical-analysis` and `math-verification` when checking calculation |
| `audio-rms-crest-factor` | `math-numerical-analysis` for scaling/underflow; `math-verification` for fixtures |
| `audio-spectrogram-waterfall` | `math-dimensional-analysis` for time/frequency axes; `math-verification` for STFT time and calibration fixtures |
| `audio-sample-peak` | `math-numerical-analysis` for extreme/invalid values; `math-verification` for timestamp and state claims |
| `audio-true-peak` | `math-numerical-analysis` for interpolation/error limits; `math-verification` for independent bounds and negative cases |

Do **not** load `math-linear-algebra` for a spectrogram solely because its output is a rectangular data array. Reserve it for an actual matrix solve, transformation or related operation. Keep each audio domain's sign/normalization/reference/calibration contract in the audio skill.

**Gate:** A cold-start agent can discover an audio skill from `skills/INDEX.md`, load its audio instructions first, and follow only the math procedures actually needed for the task. Links resolve after merge and do not imply automatic activation or new permissions.

### Stage 3 — Reuse math verification policy without collapsing audio fixtures

1. In `audio-dsp-test-fixtures`, delegate generic tolerance/shape/finite/oracle requirements to `math-verification` and its `FIXTURE_POLICY.md` where it increases clarity. Keep the DSP fixture schema, exact sample-index policy, channel generation, frozen SciPy goldens, and production/standards boundaries in audio.
2. Record oracle provenance: analytic identity vs frozen SciPy external result vs live SciPy differential vs metamorphic invariant. Do not count a second wrapper around the same implementation as independent.
3. Review approximate comparisons: explicitly state absolute and relative tolerances, units, shape, finite policies, near-zero behavior, and which thresholds are heuristic. Ensure `math.isclose` default `rel_tol` is not silently accepted for an absolute-only gate. Respect that NumPy `allclose` has its own comparison semantics.
4. Preserve exact integer sample origins, chunk invariance and negative input checks. Do not require a new general-purpose numerical library.
5. **Gate:** The DSP test procedures can explain what a pass proves and what it cannot prove, independently of tool output cosmetics.

### Stage 4 — Add only high-value counterexamples or regression tests

Prioritize the gaps demonstrated by review; avoid mechanically duplicating all 31 math fixtures:
- One wrong FFT scaling or sign/phase convention must fail a DSP-specific check even if a round trip succeeds.
- PSD power/density normalization and decibel semantics must reject an amplitude/power confusion; overlapping Welch segments must not be represented as independent statistical draws.
- Tiny, large, subnormal or nonfinite audio samples must preserve documented RMS/peak/true-peak behavior and distinguish measurement absence from silence.
- Malformed shape or channel data must fail before pairwise iteration truncates or hides data.
- Timing/units checks must preserve integer sample origins and frame start/center/hop semantics, including gaps and even/odd FFT lengths.

Choose a small set based on actual uncovered behavior. For each added test, identify a plausible incorrect result that it rejects; protect frozen goldens. Prefer documentation-only links if existing tests already cover the risk. Never weaken a previous gate just to pass CI.

**Gate:** Every new test is tied to an observed risk, fails the proposed wrong case, and preserves existing reference semantics. No new production DSP or standards-certification claims.

### Stage 5 — Verification and optional differential evidence

1. Execute `python3 tools/validate_seed.py`, `python3 -m unittest discover -s tests -v`, and `git diff --check` on the combined tree. Record runtime, source revision, actual counts/failures, and any environment differences.
2. If NumPy/SciPy are already available in an authorized isolated environment, run `python3 skills/audio-dsp-test-fixtures/scripts/check_scipy_differential.py --seed 20261103 --cases 12`. If not available, mark **NOT RUN** and do not install dependencies without appropriate authority.
3. Inspect the full diff, including all new/modified memory records; verify no accidental application, contract, CI, dependency or root-permission changes. Confirm combined changes do not alter math-skill meaning.
4. Optional, separate agent-level evaluation: compare bounded audio tasks with versus without mathematical references, with answer keys isolated, equivalent budgets and captured token/time cost. Do not claim measured benefit unless those trials execute. The 42-run math pilot remains separate and unexecuted until actually run.
5. **Gate:** Only actual commands, current-head CI, and independently reviewed evidence may support a pass statement. No historical passing test count may be advertised as a new combined-tree result.

### Stage 6 — Documentation, protocol memory and review-ready delivery

1. Update `docs/MATH_CURRICULUM.md` only to reflect *actually implemented* one-way audio links and continued domain ownership. Update the PR #2 description to acknowledge that PR #3 is merged, if within the current approved workflow.
2. Update the existing audio roadmap handoff with the reconciled exact branch SHA and integrated state; preserve historical audit evidence and the 9/73 tally unless an independently authorized new skill was actually completed.
3. Update **this** handoff with changed files, execution evidence, blockers, remaining gaps, current outcome and actual remote commit. Keep it indexed in `memory/projects/kisuul/kestrelgaming/INDEX.md`; use `status: archived` when closed and durable lessons are captured.
4. Give the owner a concise implementation report: changes by module, resolved conflicts, exact commands/results and GitHub CI, new negative tests, optional differential status, and remaining work. Leave PR #2 open; no auto-merge, release or PR #3 rewrites.
5. **Gate:** Reviewer can distinguish what changed, what ran, and what remains unverified without trusting this handoff alone.

## Acceptance and stop conditions

**GO for owner review** only if both skill catalogs and memory indexes preserve math and audio entries, relative Markdown links resolve, domain formulas/calibration remain owned by audio, all required tests actually pass on the combined tree, no unrelated policy/workflow/application changes appear, and the handoff clearly records actual results.

**STOP / PARTIAL** if branch reconciliation threatens unrelated work, a link or acceptance test must be deleted to make validation pass, a numerical claim has no defensible tolerance/oracle, execution permissions are missing, or new contradictory math/audio instructions require owner judgment. Report the exact blocker and smallest safe next action.

**Do not expand scope** to the remaining 64 audio candidates, add the future `audio-timebase-sync` skill, implement a new numerical runtime, perform production Auralprint changes, or claim ITU/AES/physical calibration. `audio-timebase-sync` can use the established dimensional/numerical/verification pattern in a *later* authorized assignment.

## Next action

Publish the validated integration to the existing PR #2 branch, record its confirmed
head/CI on the PR, and leave it open for owner review. Any later audio-timebase-sync
module, further 64-candidate backlog work, production integration or behavioral trial
needs its own task and evidence. Host activation, agent improvement, realtime load,
physical calibration and normative compliance remain unverified.

## Revisit when

On next-agent pickup, a PR #2 head or main head changes, a merge conflict is resolved, a verification run yields new evidence, review reveals an uncovered mathematical failure, or the owner changes integration scope. Revalidate facts against live source and replace NOT RUN with actual evidence only after execution.
