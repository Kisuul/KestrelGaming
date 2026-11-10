# Hostile review — KestrelGaming PR #18 baseline reconciliation

**Review date:** 2026-11-10 (UTC)
**Target:** [Kisuul/KestrelGaming PR #18](https://github.com/Kisuul/KestrelGaming/pull/18) at frozen commit `6744244feb3e525702a258ddd828eb64c87a0fac`.
**Target base:** upstream main `dbe0164e3dbdcfa65fd6a4a81434ae0e11eb259c`.
**Imported fork parent:** Cosmic Dance main `4cb17b01d7ac50bd15ed69e84eccee0d32035a8b`.
**Audit isolation:** `audit/pr18-hostile-reconciliation-2026-11-10`; the candidate branch, fork agent-home branches, and both main branches were NOT changed.
**Decision:** **CONDITIONAL GO for the upstream ancestry-preserving merge only**, contingent on owner/publication review and a fresh source-head/CI check. **NOT COMPLETE** for shared-main reunification until the fork is fast-forwarded to the *same exact merge commit*. **NO runtime/agent-readiness certification.**

## What the independent source checks actually established

- The proposed integration commit is a genuine two-parent merge. Parent 1 is the exact stated upstream SHA; parent 2 is the exact stated fork SHA. Integration tree SHA is `2112970174afa9ef775860845c120b0dff011ad9`.
- Full non-truncated Git tree comparisons show **140 upstream blobs**, **72 fork blobs**, **151 distinct source paths** in their union, and **152 blobs** in the integration (one added reconciliation document). **No source path is missing.** All unexpected changes are reviewable against both source commits.
- Upstream `KESTREL.md`, `kestrel/PERMISSIONS.md`, `kestrel/MEMORY_PROTOCOL.md`, skills, validation tooling and workflow bytes are retained. The changed six project handoffs normalize the machine-readable outcome and explicitly preserve the original qualified statement. Their historical project outcomes were **not** revalidated by this audit.
- All seven Cosmic Dance `agents/<id>-v1` branches resolved at review. For each, its branch-local `AGENTS.md`, `KESTREL.md`, `agents/<id>/AGENT.md`, `PROFILE.json`, memory index/profile, and `test_<id>_profile.py` exist. Seven structured `character_id` and declared branch fields match the real branch. Their four profile trait bands each sum to 1. The branch-home skill inventories differ; this is explicitly documented and **not** evidence that recent main skills are present on every home.
- GitHub Actions for the candidate PR head passed on push and PR triggers with the existing **84 tests**. The separate [hostile CI run](https://github.com/Kisuul/KestrelGaming/actions/runs/42781422878) passed 88 tests; its three hostile cases are intentionally assertions of undesirable behavior, **not certification**.

## Findings and counterevidence

### K18-F01 — MEDIUM, CONFIRMED, INHERITED: Catalog registration can be forged by non-links

**Reproduction:** `test_a01_escaped_catalog_link_falsely_registers_imported_memory` and `test_a02_raw_html_pre_catalog_link_falsely_registers_imported_memory` in [audit fixtures](../../tests/test_reconciliation_hostile_audit.py) passed on GitHub Actions. In a disposable full copy of the integration tree, replacing the Auralprinter project-catalog link with either backslash-escaped `\\[label](path)` or a Markdown link nested in an HTML `<pre>` block still yielded `validate_seed.validate(root) == []`. Neither form represents a normal, navigable Markdown catalog link.

**Root cause:** Existing `tools/validate_seed.py` uses regex link matching over Markdown prose and ignores escape/raw-HTML block semantics. Its reachability and record-index gates therefore accept rendered non-links. A reader following the visible catalog cannot reach a record that the validator claims is registered.

**Scope boundary:** The **actual PR #18 catalog entry is valid**, and the validator code did **not change** in this PR. This is a pre-existing validation weakness exposed by hostile mutations, **not** a proven regression from the merge. It should not be used to falsely allege lost imported memory or malicious content in the PR.

**Action:** Add fail-on-bug fixtures for backslash escapes and raw HTML or explicitly constrain/sanitize catalog grammar; validate the actual rendered link set consistently. Do not describe current memory-index validation as cryptographic integrity, secure authorization, or guaranteed navigation.

### K18-F02 — LOW to MEDIUM, CONFIRMED COVERAGE GAP: Static roster checks do not validate live home refs

**Reproduction:** `test_a03_roster_url_can_point_to_nonexistent_branch_and_ci_still_passes` changes only one roster `profile_url` to an intentionally nonexistent branch while retaining its suffix. The targeted roster tests and global structural validator still pass.

**Counterevidence:** Direct independent GitHub inspection of the **unmodified PR** verified all seven real home refs, mandatory character files, matching profile IDs, and normalized trait bands. The release document correctly says this is a **proposed**, unembodied design and that a host must resolve refs at pickup. No currently invalid branch is claimed.

**Action:** Add a separate opt-in/preflight live-ref or pinned-manifest check when making a role availability claim, and document the tool connection/permission needed. Do not misrepresent existing static tests as agent execution or behavioral assurance.

### K18-F03 — HIGH OPERATIONAL DEPENDENCY: Both main branches cannot yet be synchronized by the current connector

**Direct evidence:** At review, upstream `main` remains `dbe0164e3dbdcfa65fd6a4a81434ae0e11eb259c`, Cosmic Dance `main` remains `4cb17b01d7ac50bd15ed69e84eccee0d32035a8b`; PR #18 is still a draft. Connected GitHub permissions on Cosmic Dance are `pull: true, push: false`, while the upstream account has `push: true`.

**Scope boundary:** The PR's own reconciliation document explicitly discloses the limitation and provides the correct two-stage landing sequence. This is **not** a hidden engineering bug. But upstream merge by itself **does not achieve the full shared-main reconciliation objective**.

**Action:** Before merging, identify an operator/connection with authorized fork write access and agree on the exact fast-forward procedure. Recheck both current heads, use an ancestry-preserving upstream merge (not squash/rebase), fast-forward fork main to the same final upstream SHA without force, verify both remote hashes, and record that result.

### K18-F04 — HIGH RELEASE-PRECONDITION / UNVERIFIED PUBLICATION CONTEXT: Imported Auralprinter memory provenance

The PR copies public-visible fork memory for `cosmicdance-4-2-0/auralprinter` into the upstream public repository. Direct GitHub connector reads of the referenced Auralprinter source repository/PR returned 404; this could mean unavailable installation scope, renaming, deletion, or private visibility. **It does not prove the source is private or the imported content is a leak.** The memory documents were already publicly present on the source fork. A limited scan of these three imported Markdown files found **zero** GitHub-token, common cloud-key, email, bearer-auth, or private-key markers; that scan is not privacy or disclosure approval.

**Action:** Authorized maintainer must confirm the public-safe status of Auralprinter project summaries and source citations before widening distribution to upstream; if private or unreviewed, remove or sanitize sensitive material through an appropriately reviewed change. Do not claim historical assertions were independently reverified when the cited source cannot be inspected by this reviewer.

### K18-F05 — LOW / REVIEW NOTE: Historical machine-readable status reformatting

Six handoffs had text after the machine-readable `**Task outcome:**` status, which violated the pre-existing validator. Changes move their qualification to `**Historical outcome detail:**`, update `updated` dates, and note that source claims were not revalidated. Inspection of the patches shows that the qualifications remain present. Source authorship strings are historical and not a fresh attestation of the formatter. Maintain their provenance through Git history and avoid interpreting a format-only update as a new successful project test.

## What did not fail

- Full source-path and merge-parent preservation passed independently.
- The existing skills, shared engineering contract, permission protocol, and CI tooling were not silently replaced by fork variants.
- The current seven proposed agent home references were verified to exist and match profile identity data. No agent runtime or cross-agent behavior was executed; the docs do not claim one was.
- Both original CI runs on the target succeeded. The new hostile fixtures only alter **disposable local copies** of the merged tree. No branch write, merge, release, deployment, permission change, or production operation was performed.
- There is no demonstrated credential leak, exploit of host capabilities, loss of a merge parent, broken actual project-catalog link, or missing original source file.

## Release decision and concrete landing gate

**For upstream Git history integration:** **CONDITIONAL GO**, after ordinary review, explicit approval that the imported Auralprinter notes are public-safe, and rechecking the live source heads. The discovered inherited validator flaws are worthwhile follow-up hardening but do not, by themselves, falsify PR #18's actual ancestry or source-path preservation.

**For the full objective of both shared mains being reunited:** **NOT COMPLETE / HOLD** until an authorized actor executes the fork fast-forward and the two remote main refs match exactly. Until then, do not say the common baseline is synchronized.

**For operational role pickup or ensemble readiness:** **NOT VERIFIED**, since no model hosts were launched, no behavioral experiments or live profile-loading integration checks were run, and existing CI for the seven individual branches was not found during inspection.

Suggested next review actions:
1. Review source/fork main heads and Auralprinter disclosure scope at landing time.
2. Merge PR #18 using GitHub's **merge commit** option only; verify resulting ancestry and exact SHA.
3. With fork write authorization, fast-forward Cosmic Dance main to that exact SHA; verify both refs.
4. Open a separate validator-hardening change with fail-on-bug tests for hidden/non-links, and add a distinct live-ref preflight for roster availability claims.
5. Keep runtime/identity competence claims out of this baseline reconciliation.

**Auditor limitation:** All source checks and GitHub CI used the connected tool account and external execution. This is an adversarial review **in the same assistant session**, not an independently instantiated second AI model or proof of agent continuity.
