# Adversarial review worksheet and GitHub-ready report

## Intake (keep concise for tiny PRs)

- **Target / base / head:** Exact owner/repo and immutable commit IDs; local dirty-tree state if relevant.
- **Authorization and boundaries:** Review only or implementation explicitly permitted? Protected fixtures / application instructions?
- **Intended invariant:** Who authorized it and where is it independently recorded?
- **Changed surfaces:** APIs, persisted data, config/defaults, numerical comparisons, tests/goldens, lifecycle, dependencies, documentation.
- **Coverage plan:** One meaningful negative case or explicit reason none is needed; baseline contrast when attributing regressions.

## Report (findings first)

**Disposition:** MERGE / REQUEST CHANGES / NEEDS EVIDENCE

**Overall:** COMPLETE / PARTIAL / BLOCKED (scope of review, not universal correctness)

### Findings

For each confirmed finding:

**[AUD-NNN] Title — Severity: critical/high/medium/low**

- **Impact / likelihood:** State scenario and why each is plausible; severity is not just rhetorical emphasis.
- **Location:** Exact path, head revision, line/function; baseline location if relevant.
- **Observation:** What was actually inspected or executed? Include environment, literal input and observed output. Distinguish direct observation from inference.
- **Invariant / expected result:** Independent requirement/source or derivation; specify domain and any tolerance.
- **Discriminating reproduction:** Minimal command, setup, input, expected vs actual, and what would falsify the claim. If NOT RUN, label as a hypothesis instead of a confirmed reproduction.
- **Attribution:** Introduced regression / pre-existing issue / requirement change / environment-dependent / unresolved. Include baseline comparison evidence or reason attribution is unknown.
- **Proposed bounded correction:** Fix contract/implementation/test as warranted, with relevant regression oracle; never silently weaken acceptance.
- **Uncertainty / checks NOT RUN:** Name missing evidence, permissions or environmental differences.
- **Disposition:** Must fix before merge / needs evidence / optional improvement / separate issue.

A *potential* concern goes under **Evidence gaps**, not confirmed Findings. No defects observed? Say **No confirmed findings**; do not invent one.

### Verification and test-integrity ledger

| Claim / invariant | Evidence source and revision | Baseline outcome | Head outcome | Independent oracle? | Limits / NOT RUN |
| --- | --- | --- | --- | --- | --- |
| Replace with actual claim | Source or command | Observed/NOT RUN | Observed/NOT RUN | Yes/No, dependencies | Scope caveat |

Explicitly inspect any altered acceptance tests, numeric tolerances, skipped checks, expected outputs, mocks or fixtures separately from implementation changes. A changed requirement requires authorization independent of the code change.

### Risks and next decisive check

Separate confirmed must-fix defects, low-priority suggestions, and unresolved hypotheses. Include what *would change the disposition*. For no confirmed findings, describe what was reviewed and what remains unverified. A review is not a guarantee.

### Evidence provenance

- **Observed local:** Exact revision, command, environment and raw result.
- **Observed remote:** CI URL and exact commit; do not imply local execution.
- **Reasoned:** State premises and result.
- **Claimed:** Attribution to commit message, user or documentation; independently unverified.

### Exit checklist

- [ ] Diff, tests and acceptance changes inspected at pinned revisions.
- [ ] Findings have independent expectations and discriminate actual wrong behavior from clean behavior.
- [ ] Baseline attribution is evidence-backed, or uncertainty is explicit.
- [ ] No unauthorized modifications to reviewed code, policy or tests.
- [ ] Test runs and skipped tests are reported accurately.
- [ ] Disposition proportional to severity and residual uncertainty.
