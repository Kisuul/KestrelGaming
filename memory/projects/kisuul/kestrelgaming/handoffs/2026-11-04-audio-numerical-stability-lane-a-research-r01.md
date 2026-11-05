---
schema: 1
id: 2026-11-04-audio-numerical-stability-lane-a-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: ChatGPT
created: 2026-11-04
updated: 2026-11-04
sources: "Owner conversation 2026-11-04: assigned Lane A, insisted on mathematics rather than Python, approved final skill review and requested Kestrel persistence; Kisuul/KestrelGaming PR #2 audio branch at ee9eb107e78724e23d3aa1ef913e63113adf0211; targeted source inspection and local standalone arithmetic demonstrations."
---

# Lane A handoff — audio numerical stability, mathematics first

## Summary

**Goal and acceptance criteria:** Develop `audio-numerical-stability`, the last outstanding foundation/numerical-DSP skill in Kestrel's 73-module audio curriculum. Teach *transferable numerical mathematics and audio-engineering reasoning*, not Python library usage. A future agent must be able to analyze equations, finite representations, conditioning, stability and error budgets, choose and justify a robust algorithm, and verify it in an unfamiliar language/runtime.

**Task outcome:** PARTIAL — research and final design review COMPLETE; skill implementation, integration, repository validation and agent behavioral trials NOT RUN/NOT DONE.

**Authorization (user-stated):** Owner assigned Lane A to this session and explicitly requested saving this work using Kestrel memory. Lane B (`audio-analysis-provenance`) is a separate parallel assignment; do not duplicate it. PR #2 must remain unmerged into `main` until all 73 modules are complete, independently reviewed and owner-approved. This handoff is not standing permission for unrelated remote changes.

**Target:** Kisuul/KestrelGaming, PR #2, branch `skills/audio-dsp-core-foundation-2026-11-03`, observed head `ee9eb107e78724e23d3aa1ef913e63113adf0211` immediately before the memory update. At inspection, the branch has 15 developed audio modules, 58 pending; `skills/audio-numerical-stability/` does not yet exist. Six separately integrated mathematics skills are not audio-module credits. Recheck all facts and branch heads on resumption.

**Relevant context:** [Canonical audio roadmap](2026-11-03-audio-skills-roadmap.md); [parallel execution plan](2026-11-04-audio-parallel-execution-plan-r01.md); [owner completion gate](../2026-11-04-audio-curriculum-full-completion-gate-r01.md); central math skill `skills/math-numerical-analysis/SKILL.md` and `skills/math-verification/SKILL.md` (relative to repository root). Existing math is authoritative for general methods; this audio skill owns signal semantics, measurement units, scaling conventions and domain-specific numerical policies.

## Observations and verified evidence

- **Source inspection:** `skills/audio-power-spectral-density/scripts/reference_psd.py` computes one-sided power as `multiplier * (abs(value) ** 2) / norm`; `skills/audio-spectrogram-waterfall/scripts/reference_stft.py` uses analogous `factor*abs(z)**2/(fs*square)`. These orders can overflow before division even when the normalized mathematical result is finite. `reference_psd.py` accumulates Welch ordinates into `total[k] += value`, a separate potential intermediate overflow. No change/fix is claimed.
- `skills/audio-fft-spectrum/scripts/reference_dft.py` uses `abs(value) * multiplier / total` for one-sided amplitude and computes window energy as `math.fsum(w*w for w in window)`. The summands can underflow before accurate summation, and multiplication can overflow before division.
- `skills/audio-rms-crest-factor/scripts/reference_levels.py` already employs scaled RMS and log-domain level ratios. Do not reintroduce the historical defects or duplicate its audio-level teaching.
- **Standalone arithmetic experiments actually run locally (Python stdlib, 2026-11-04; not importing the GitHub code):**
  - Rectangular 2-sample PSD with both samples `2^512`, `fs=48000`, `Nfft=2`: direct squared-DFT-magnitude expression raised `OverflowError`; high-precision result for DC PSD is `2^1026/96000 ≈ 7.490388061926316e303` (representable as binary64).
  - 4-sample impulse of `2^1023` with a rectangular window: one-sided interior-bin computation `(2*x)/4` produced `inf`; exact corrected amplitude is `2^1022 ≈ 4.494232837155790e307`.
  - Four uniform window coefficients of `1e-200`: binary64 `sum(w*w)` produced zero, while exact mathematical ENBW is 1 bin. The ultimate squared-energy representation itself may be outside binary64; a scaled/ratio method or explicit supported-domain policy is needed.
  - Sum `2^54 + 1 - 2^54` evaluated left-to-right as binary64 produced 0 although the exact result of these representable inputs is 1.
- **Evidence limits:** These experiments establish failures of representative arithmetic *expressions*, not executions of the current repository's Python scripts or a full Kestrel test suite. They are deliberately extreme synthetic inputs, not proof of errors in normal calibrated PCM. Existing reference CI evidence at the preceding branch checkpoint reported 308 passing repository tests; it does not test this new, not-yet-written skill.
- Relevant existing primary-source leads for later verification: [SciPy periodogram](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.periodogram.html), [SciPy Welch](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html), [LAPACK scaled sum-of-squares](https://www.netlib.org/lapack/explore-html/group__lassq.html), and [Python floating-point documentation](https://docs.python.org/3/tutorial/floatingpoint.html) as *implementation context only*. Confirm precise reference editions, links and claims while authoring.

## Decisions and design specification

**Governing teaching principle (owner-stated):** Mathematical competency must be demonstrated independently of implementation-language competency. Equations, assumptions, derivations, invariants, error/failure conditions and portable algorithms precede any code. Python is an optional reference/CI vehicle; no agent should have to load Python syntax to reason about C++, Rust, C#, JavaScript or fixed-point DSP.

**Selective activation:** Load `audio-numerical-stability` only when audio processing/measurement encounters numeric range, precision, cancellation, reduction, quantization, scaling or backend-dependent correctness. Load the specific shared math skills on demand, never copy the full numerical-analysis curriculum into this audio module.

**Seven competencies:**
1. Declare the signal quantity and exact mathematical target: measured sample units, channel/reference, clock, window and FFT conventions, linear vs logarithmic measurements, normalization and output units.
2. Identify actual numeric representations: signed integer/fixed-point limits, scaling and saturation, float32/float64 and intermediate/accumulator widths, rounding, denormals/flush-to-zero and backend differences.
3. Distinguish inherent problem conditioning, algorithmic stability, model/measurement uncertainty and final representability. Precision cannot restore absent input information.
4. Diagnose intermediate overflow/underflow, cancellation, loss in reductions, PSD/RMS/ENBW/FFT scaling, filter coefficient quantization and stateful accumulation. `fsum` or higher precision alone is not a universal solution.
5. Derive an appropriate scaling, normalization/order-of-operations, compensated/pairwise reduction or other algebraically equivalent strategy; state assumptions, cost and numerical domain.
6. Define explicit behavior for exact silence, subnormal nonzero measurements, NaN/Inf, unsupported range, invalid normalization, zero denominators, and undefined/ill-conditioned results; never silently invent valid-looking measurements.
7. Verify mathematical expectations independently with exact/rational/decimal/analytic fixtures where appropriate; set error budgets in the observable's units, verify near-zero semantics and fixed-point saturation behavior, and report empirical vs proven limits.

**Proposed concise package:** `skills/audio-numerical-stability/SKILL.md`; `references/NUMERICAL_CONTRACT.md`; optional `references/AUDIO_CASES.md`; portable `tests/fixtures/AUDIO_NUMERICAL_STABILITY_VECTORS.md`; bounded optional Python `scripts/reference_numerical_stability.py`; `tests/test_audio_numerical_stability_reference.py`; optional host metadata. Keep mathematical material language-neutral and implementation examples clearly non-normative.

**Required adversarial acceptance suite:** ordinary silence/DC/impulse/coherent-tone cases; the four concrete cases above with independently derived expectations; high/low dynamic-range normalization; Welch accumulation; signed and unsigned integer overflow, fixed-point round/saturate vs wrap; mixed float32/float64 representation; cancellation and near-zero relative error; filter coefficient/pole sensitivity; chunk partition invariance for declared stateful algorithms; invalid/nonfinite inputs; and meaningful negative cases that catch a naive implementation. Specify mathematical domain, units, sample-index conventions, backend/dtype, tolerance derivation and failure policy for every fixture. Scaled formulations must preserve the intended physical measurement and handle an *unrepresentable final result* honestly.

**Independent skills efficacy gate:** At least one language-free written diagnosis/derivation and an unfamiliar runtime scenario, evaluated with and without the skill where feasible. Correct explanation and justified validation matter more than syntax/API recall. Do not claim this behavioral gate has been run until executed.

**Separation of concerns:** Do not modify existing PSD/STFT/FFT/filter source as a hidden side effect of teaching this skill. A production/reference repair is a separate independently tested and reviewed patch. Do not modify Kestrel root contract, Math skills, application repositories, or workflow policy as part of this bounded lesson.

## Verification and persistence

| Check | Outcome | Limits |
| --- | --- | --- |
| Read current branch, math skill, roadmap and targeted audio reference source | Observed as above | Branch can change |
| Isolated arithmetic demonstrations | Executed; values/failures above | Did not import the repository code |
| Proposed skill tests and Kestrel structural validator | NOT RUN for this skill | Skill not yet created |
| Controlled language-neutral agent-use comparison | NOT RUN | Design requirement, not achieved capability |

**Changed files for this memory-only task:** This unique handoff and one additive row in `memory/projects/kisuul/kestrelgaming/INDEX.md`. The remote commit/history, not this record, establishes actual synchronization. No audio skill completed/credited by this write.

## Next action

1. Recheck PR #2 head and claimed task ownership, then implement the concise language-neutral skill and contract on an isolated child branch sourced from the *current* audio branch, following the parallel execution plan. Do not race the provenance lane or overwrite shared indexes.
2. Freeze independently derived portable numeric fixtures, implement only a bounded optional reference oracle, execute focused tests and repository validator/full regression suite, and perform adversarial review.
3. Submit a reviewable child PR targeting the audio branch; coordinator serially integrates, reconciles the canonical roadmap/skill index, and credits the module only after verification. Keep PR #2 out of `main` until the owner 73/73 completion gate.

**Risks:** test/oracle circularity, unportable assumptions about binary64 or denormals, accidental Python-centric lesson framing, semantic changes masked as numeric fixes, and shared-index concurrency.

## Revisit when

The audio branch, numerical source implementations, owner constraints, module count, external numerical references or task ownership changes; on implementation review and any handoff to another agent. Revalidate all historical CI and numerical claims against the actual revision being used.
