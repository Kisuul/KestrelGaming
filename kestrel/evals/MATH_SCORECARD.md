# Mathematics trial scoring and ablation protocol

**Status: NOT RUN.** This file defines evaluator-only keys and prospective
decision gates for [MATH_SCENARIOS.md](MATH_SCENARIOS.md). There are no measured
baseline, treatment or efficacy results. Use [SCORECARD.md](SCORECARD.md) unchanged
for each run; these keys refine mathematical correctness, not global permissions.

## Before collecting results

1. Freeze the fixture document commit, exact skill/reference hashes, contract,
   model snapshot, harness version, model settings, runtime image and task files.
   Record the actual model identifier; a mutable display name is insufficient.
2. Place only the selected task, fixture and allowed references in a fresh isolated
   participant workspace. Keep this answer key, hidden checks and other runs outside
   its readable filesystem and context. If isolation cannot be enforced, mark the
   run contaminated and exclude it from the comparison; document the failure.
3. Use three fresh runs per case per arm: 7 cases × 2 arms × 3 repeats = 42 runs.
   Randomize paired baseline/with-skill order with a recorded seed. Use identical
   task text and budget, with no conversation carryover or performance feedback.
   Record decoding seeds when supported; do not pretend repetitions are independent
   samples when the model/harness is deterministic or shared infrastructure couples them.
4. Preregister the exact expanded reference path list for each case. Copy the same
   bytes on every treatment run. Both arms receive the same general Kestrel contract
   and tools; the sole intended difference is the supplied math reference text.
   The reference tokens and reading time count toward treatment cost.
5. Assign randomized run IDs that conceal arm identity from scorers. Have a reviewer
   other than the skill author grade original artifacts before seeing the arm.
   Prefer a second independent scorer; preserve original scores, disagreements and
   adjudication. If author-only scoring is unavoidable, label the result exploratory.

No run is retrospectively removed for low quality. Report timeouts, tool failures,
contamination and missing artifacts with their reasons; replacement runs need a
predeclared policy and new IDs. A missing required environment check makes affected
runtime-specific findings inconclusive rather than silently changing the fixture.

## Evaluator keys

Derive expectations independently before running participant artifacts. Optional
hidden checks go in an evaluator-only harness; do not let the participant revise
them. Compare floating results using explicit finite checks and stated absolute
and relative tolerances. Do not use the participant's own oracle as the sole judge.

| Case | Required result and evidence | Planted misconception / decisive mathematical failure |
| --- | --- | --- |
| B-NUM | Rationalize to `x/(sqrt(1+x)+1)` (or equally sound method), retain zero, reject negative/out-of-range/nonfinite values. For represented `1e-16`, compare to an 80-digit `Decimal.from_float(x)` square-root reference with absolute error ≤ `1e-30`, `rel_tol=0`. Explain local relative condition number `(sqrt(1+x)+1)/(2*sqrt(1+x))`, tending to 1 for positive small x; relative conditioning at x=0 is undefined. | Calls unavoidable zero the correct answer, or describes the well-conditioned nonzero problem as the source of cancellation. Merely comparing the reformulation against the unstable original is inadequate evidence. |
| B-VER | Finite guard plus `math.isclose(actual,-1.0,rel_tol=0,abs_tol=1e-14)` or equivalent absolute test. `-1` passes; `-1+5e-10` fails; NaN/±Inf raise `ValueError`. Demonstrate the original's relative-tolerance leak. | Retains default `rel_tol=1e-9`, widens the threshold or treats invalid inputs as valid comparisons. |
| B-DIM | Validate both lengths and exponent types before arithmetic; six/eight components and booleans reject. Acceleration `(1,0,-2,0,0,0,0)` times mass `(0,1,0,0,0,0,0)` gives `(1,1,-2,0,0,0,0)`. `20 °C + 5 °C interval = 25 °C = 298.15 K`; interval is 5 K, not 278.15 K. Energy and torque share dimensions but differ in quantity kind. | Allows `zip` truncation, adds two absolute kelvin points for the temperature task, or makes dimensional equality sufficient for physical meaning. |
| B-LIN | Exact `x=(1,1)`, `r=A*x_hat-b=(0,-1e-12)` (the opposite declared residual sign is equally valid), `||r||∞=1e-12`, relative forward error 1, `κ∞(A)=1e12`. Indicator `η=||r||∞/(||A||∞||x_hat||∞+||b||∞)=5e-13`; identify its normwise perturbation interpretation. Direct diagonal solve is suitable; a general full-column-rank least-squares problem favors QR, rank-deficient problems need rank policy/SVD. | Equates small residual with accurate solution, ignores conditioning, or recommends normal equations/inversion as a universally stable solve. |
| B-CMP | Use `atan2`/`cmath.phase` after finite/zero checks. `3+4j` phase ≈ 0.9272952180016122 (absolute `2e-15`, relative 0); negative-axis signed zeros give +π and −π, `1j` gives π/2, zero gives `None`. Reject nonfinite components. Modulo-2π equivalence explains the axis values; FFT sign/scaling needs a separate interface convention. | Keeps ratio `atan`, reports zero's phase as measured, or interprets the branch jump as a necessary physical discontinuity. |
| B-STA | Four independent values `[1,2,3,4]`: mean 2.5 V, sample variance `5/3 V²`, plug-in SEM `sqrt(5/12) V`. Naive eight-row sample variance `10/7 V²` gives SEM `sqrt(5/28) V`. Exact 95% coverage and calibrated uncertainty do not follow. | Treats duplicates as new independent information or claims exact Gaussian coverage/calibration without the missing model/evidence. |
| B-MULTI | Each packet lasts `1/50 s`; speeds `1/2` and `3/2 m/s`; mean `1 m/s`, packet sample variance `1/2 (m/s)²`, plug-in SEM `1/2 m/s`. Two independent packets. Exact rational arithmetic can establish conversions; scalar floating results may use absolute `1e-14`, relative 0. Neither calibrated error bound nor 95% coverage is established. | Uses four independent rows, confuses centimetres/metres or ticks/seconds, or certifies `±0.01 m/s` without evidence. |

For B-NUM the high-precision reference is still an approximate oracle: 80 decimal
digits make its numerical error negligible relative to `1e-30` here; record the
precision and verify with a higher precision before trusting the frozen result.
The key's algebra explains conditioning independently of the floating implementation.
For B-LIN use exact rationals for `1e-12`; the task's error quantities need no library
condition estimator. For B-STA exact sums establish the variance fractions; compare
reported square roots with absolute `2e-14` and relative 0. These thresholds apply
only to these inputs and do not specify general algorithm accuracy.

## Per-run decision

Record each required mathematical item as PASS / FAIL / NOT OBSERVED, with a path
or transcript reference. A case passes only if all its required conclusions and
input policies are correct, required artifacts exist, demonstrated checks actually
ran, and no critical failure occurred. Equivalent sound methods and clearly stated
conditional conclusions are acceptable. Do not demand preferred wording or needless
skill citations. Judge numerical outcomes and reasoning rather than verbosity.

Apply the existing scorecard's six 0–2 dimensions and global failure gates. In
addition, any decisive mathematical failure in the table fails that case regardless
of aggregate score. An unexecuted check honestly labeled unexecuted is a gap, not
fabricated evidence, but cannot satisfy a required execution criterion. Distinguish
an incorrect result from a correct result with insufficient evidence.

## Prospective pilot interpretation

Before runs, use these practical thresholds to decide whether to continue evaluation:

- With-skill passes at least 18 of 21 runs, with no global integrity/scope failure.
- Paired pass count improves by at least 3 of 21 over baseline; no scenario has a
  lower with-skill pass count than baseline. A baseline already near ceiling can
  make improvement inconclusive even if both arms perform well.
- Median elapsed time increases no more than 25%, and median total tokens no more
  than 50%, relative to nonzero baseline medians. Report absolute values and every
  timeout as well; unavailable cost measurements remain unavailable.

Meeting all gates is a **promising pilot**, not general efficacy or statistical
significance. Failure identifies revision/evaluation needs, not proof of no value.
Publish per-case paired outcomes, score distributions, critical failures, tool/time/
token costs and scorer disagreements. These seven known tasks are a small convenience
sample; repeated fixed prompts do not establish performance on new problems. Test
held-out task variants before making transfer claims, and distinguish shared model
prior knowledge, reference copying and genuine error detection where observable.
No result from this suite establishes production-library correctness, physical
calibration, standards conformance, formal proof or automatic skill installation.
