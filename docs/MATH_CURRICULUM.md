# Kestrel core mathematics curriculum

**Scope:** six selectively loaded engineering procedures, supporting arithmetic
fixtures and an unexecuted behavioral evaluation protocol. This package is not a
numerical runtime or an installed host capability. The owner is Kisuul/KestrelGaming.

## Use and shared conventions

Start at the [skill catalog](../skills/INDEX.md). Load a module when the task needs
its concepts; review numerical error and verification before accepting numerical
claims. Cross-links are navigation, not automatic loading or new authority.

Unless the task declares otherwise, use explicit SI quantity kinds and units,
radians, column vectors, matrices acting on the left (`y=Ax`), and zero-based
example indices. Composition `ABx` applies `B` first. State frames and active/passive
meaning for spatial transforms; choose handedness explicitly when orientation matters.
Complex matrices use conjugate transpose `A*`. A real-only convention is not imposed
on complex problems. Storage layout is separate from multiplication order.

The example SI dimension vector order is `(length, mass, time, electric current,
thermodynamic temperature, amount of substance, luminous intensity)`. Require seven
finite real exponents before arithmetic. Preserve semantic labels for dimension-one
angles, samples and counts. Temperature points differ from intervals, and logarithmic
levels require references. Define empty, zero, missing and nonfinite input behavior
at each interface rather than inventing a universal zero result.

Floating fixtures target binary64 with round-to-nearest and gradual underflow;
inspect the actual backend before relying on those properties. Precision, measurement
uncertainty and sampling uncertainty are separate. A comparison budget must state
units, scale, finite-value policy and actual absolute/relative semantics.

## Module contracts and evidence map

Each entrypoint supplies required inputs, a decision procedure, worked success and
failure cases, output/evidence requirements, limits and technical references.

| Module / activate for | Required decision and acceptance gate | Existing reference evidence | Evidence boundary |
| --- | --- | --- | --- |
| [Numerical analysis](../skills/math-numerical-analysis/SKILL.md): scale, rounding, cancellation or precision | Separate input sensitivity from algorithmic stability; choose arithmetic and justify an error budget | NUM-01–05, binary64/near-zero/radix cases | Bounded arithmetic examples, not a universal libm or accuracy guarantee |
| [Verification](../skills/math-verification/SKILL.md): a mathematical correctness claim | Choose a sufficiently independent oracle and negative cases; enforce explicit comparison semantics | VER-01–03, Euler-budget and representation regressions | Tests and identities do not prove a production implementation or agent competence |
| [Dimensional analysis](../skills/math-dimensional-analysis/SKILL.md): units, conversions, sampled time or levels | Check quantity kind, dimensions, scale, reference and point/interval or clock model | DIM-01–04, incompatible-dimension and malformed-length gates | Test-local guards do not implement all kind/type/finite checks or a units engine |
| [Linear algebra](../skills/math-linear-algebra/SKILL.md): matrices, transforms, solves or least squares | Match solver prerequisites; inspect rank, conditioning and residual versus requested solution accuracy | LIN-01–03 and noncommuting transforms | Exact fixtures do not test a production decomposition, rank estimator or solver |
| [Complex numbers](../skills/math-complex-numbers/SKILL.md): polar/rectangular values, phasors or rotations | Declare exponent sign, branches and phase validity; use a suitable error metric | CMP-01–03, zero-phase and strict Euler gate | Python branch examples do not select domain FFT conventions or calibrate phase thresholds |
| [Probability/statistics](../skills/math-probability-statistics/SKILL.md): samples, estimators or uncertainty | Identify the independent unit and sampling model before inferential precision; distinguish interval targets | STA-01–03 and single-observation rejection | Exact enumeration verifies specified models, not real-world assumptions or interval coverage |

See the [fixture policy](../skills/math-verification/references/FIXTURE_POLICY.md)
and [complete 31-case catalog](../tests/fixtures/MATH_FOUNDATION_VECTORS.md) for inputs,
derivations, representations, effective tolerances and negative-case limits. Prose
examples beyond those cases are not silently counted as executable coverage.

## Verification and falsifiable skill evaluation

Repository checks are dependency-free Python 3.9+ source; the completion run uses
CPython 3.12.14 on Linux. Other interpreter versions and backends are unverified.

```sh
python3 tools/validate_seed.py
python3 -m unittest discover -s tests -v
git diff --check
```

Structural validation checks links, records and skill mechanics. The 31 mathematics
tests check small analytic claims, standard-library behavior and test-local guards.
The [completion handoff](../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-03-math-package-completion-r02.md)
records the observed baseline, final commands and results. Historical CI passes are
not evidence for a later source revision.

The [seven behavioral scenarios](../kestrel/evals/MATH_SCENARIOS.md) and separate
[evaluator keys and scorecard](../kestrel/evals/MATH_SCORECARD.md) define reproducible
module and combined tasks, planted misconceptions, acceptance gates and a paired
baseline/with-skill pilot. **These host-level trials are NOT RUN.** The evaluator must
withhold answer keys from the tested agent and record model/harness, context, tools,
budget, outputs, independent scores and cost. No measured improvement or host
activation is claimed by publishing a protocol.

## Cross-domain boundaries

General skills own transferable mathematics; domain procedures own measurement
models, calibration, interfaces and standards. Audio PR #2 is a separate initiative:
[this package](https://github.com/Kisuul/KestrelGaming/pull/3) adds no audio files,
edits no audio backlog, and applies no audio-to-math cross-links. Its merge status
or candidate counts are not inferred from an old memory record.

After compatible bases exist, domain owners can link to these entrypoints without
copying their content. Conceptual examples are:

| Domain topic | Shared mathematics | Stays domain-owned |
| --- | --- | --- |
| Sampled signal timing and detectors | Numerical analysis, units, verification | Signal tap, detector definition, clocks and realtime constraints |
| Windows, FFTs, PSD and STFT displays | Complex numbers, numerical analysis, verification | Transform sign/scaling, coherent gain, ENBW, one-sided bins, calibration and display clocks |
| Graphics transforms and simulation | Linear algebra, units, verification | Frames, handedness, integration model and application error budgets |
| Experimental/measurement data | Statistics, units, numerical analysis | Sampling design, measurement equation, calibration and coverage requirements |

No comment or change to PR #2 is needed to complete this package.

## Further curriculum

The initial six modules are complete as bounded procedural documents. Calculus,
discrete mathematics, Fourier/Laplace/Z transforms, geometry, optimization and advanced
statistics remain demand-driven candidates. They are not missing acceptance gates for
this phase or implicit claims of existing capability. Broader complex analysis is
outside the complex-numbers module. Add a new procedure when a demonstrated repeated
need justifies its inputs, method, failure cases and independent verification.

Next independent work: run the registered behavioral pilot in an authorized harness;
add target-specific numerical integration tests when a production implementation
exists; then assess useful domain links. Formal proof, standards certification,
physical calibration and GPU/realtime behavior need separate evidence.

## Technical sources

- [BIPM SI Brochure, 9th edition](https://www.bipm.org/en/publications/si-brochure/) — quantity and unit definitions; identify the update actually used for normative claims.
- [Python 3.12 standard library](https://docs.python.org/3.12/library/) — demonstrated runtime behavior; the fixture catalog identifies individual APIs.
- [NumPy linear algebra](https://numpy.org/doc/stable/reference/routines.linalg.html) — optional production-backend semantics, not a test dependency.
- [NIST TN 1297, 1994 edition](https://www.nist.gov/publications/guidelines-evaluating-and-expressing-uncertainty-nist-measurement-results-1994-edition) — measurement uncertainty framework, not certification of these examples.
