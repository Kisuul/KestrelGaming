# Kestrel core mathematics curriculum

**Status:** independent foundation initiative; candidate modules committed for review on a separate mathematics branch, not a declaration of installed host capability.
**Owner repository:** Kisuul/KestrelGaming.
**Relationship:** [Audio curriculum PR #2](https://github.com/Kisuul/KestrelGaming/pull/2) is separate; its 73 candidates (8 developed on its branch, 65 remaining) are not counted here.

## Purpose and activation

Build reusable mathematical reasoning and verification for audio, graphics, physics, simulation, data, and programming. Mathematics defines general methods and invariants; specialist skills own their measurement models, code integration and standards requirements. Read the [skill index](../skills/INDEX.md), activate only what the task uses, and consult [verification](../kestrel/VERIFICATION.md). Skill text is not an executable package or authorization.

General convention unless a task declares another one: SI quantities with explicit unit references; radians for trigonometric arguments; real column vectors; matrices acting on the left (`y = A x`); right-handed coordinates only when an oriented 3D context requires a choice; zero-based indices in examples; linear-domain calculations before specified logarithmic conversion. Binary64 means the host actually provides IEEE 754 binary64 semantics; validate platform behavior rather than assuming all languages/backends match. State any changed convention at the interface boundary.

## Candidate families (not a promise of exhaustive coverage)

| Family | Scope | Implementation criterion |
| --- | --- | --- |
| Mathematical foundations | Algebra, functions, notation, domains, quantities, dimensional analysis | Add when cross-domain tasks expose repeated failures |
| Numerical analysis | Floating point, precision, rounding, conditioning, stability, error propagation | Initial skill |
| Linear algebra | Vectors, matrices, eigenvalues, factorizations, transformations | Initial skill; advanced decompositions deferred |
| Calculus | Derivatives, integrals, quadrature, finite differences | Future candidate, driven by demand |
| Complex analysis | Complex arithmetic, polar/phasors, exponentials | Initial complex-numbers skill; broader analysis deferred |
| Discrete mathematics | Logic, sets, graphs, combinatorics, recurrences | Future candidate |
| Probability and statistics | Sampling, distributions, estimators, uncertainty, intervals | Initial skill; inference details need explicit model |
| Transform mathematics | Fourier, Laplace, Z, convolution, correlation | Future; domain skills retain chosen transform calibration |
| Geometry | Frames, projections, rotations, coordinates | Future; use linear algebra where sufficient |
| Optimization | Objectives, gradients, constraints, convergence | Future |
| Mathematical verification | Invariants, exact examples, external oracles, numerical error budgets | Initial skill |

## First phase: engineering review and dependencies

| Priority | Skill | Why an engineer needs it | Boundary / caveat |
| --- | --- | --- | --- |
| P0 | [math-numerical-analysis](../skills/math-numerical-analysis/SKILL.md) | Cancellation, summation, finite representation, scale, conditioning | Not a universal accuracy guarantee |
| P0 | [math-verification](../skills/math-verification/SKILL.md) | Reproducible counterexamples and error-bounded evidence | Tests are not formal proofs or instrument certification |
| P1 | [math-dimensional-analysis](../skills/math-dimensional-analysis/SKILL.md) | Units, rate conversions, domain-specific quantity labels | Dimensionless does not mean interchangeable (dB, rad, counts) |
| P1 | [math-linear-algebra](../skills/math-linear-algebra/SKILL.md) | Geometry transforms, simulation state, least squares | Matrix order, conditioning, singularity must be declared |
| P1 | [math-complex-numbers](../skills/math-complex-numbers/SKILL.md) | Phasors, spectral representations, rotations | Complex conventions do not define FFT normalization |
| P1 | [math-probability-statistics](../skills/math-probability-statistics/SKILL.md) | Sampling variability, measurement uncertainty | Sampling assumptions and coverage differ by application |

These six are **narrow procedural modules** and can be adopted independently. Numerical analysis and verification are the **first required review gates** for numerical work; other modules are only activated when their concepts are needed. Cross-links among skills are advisory and do not cause automatic loading.

## Verification evidence and fixture policy

See [math verification fixture policy](../skills/math-verification/references/FIXTURE_POLICY.md) and [frozen test-vector derivations](../tests/fixtures/MATH_FOUNDATION_VECTORS.md). The dependency-free `tests/test_math_foundations.py` exercises selected exact, analytic and metamorphic cases using the Python standard library. Run:

```sh
python3 tools/validate_seed.py
python3 -m unittest discover -s tests -v
git diff --check
```

These checks do not prove all math in the prose, all floating-point implementations, cross-language semantics, sampling models, standards compliance, or host skill activation. Pin software, configuration and tolerance policy whenever asserting reproducibility.

## Audio curriculum integration plan (deferred edits, not merged)

PR #2 is not in `main` at this writing. Do **not** copy its audio skills onto this mathematics branch just to edit them, and do not modify its 73-candidate backlog. After suitable merge/review, integrate the following one-way conceptual links **from audio into math** while keeping audio calibration procedures local:

| Audio skill in PR #2 | Shared math foundation | Remains owned by audio |
| --- | --- | --- |
| `audio-dsp-core` | numerical analysis; dimensional analysis; verification | Signal tap, timing, realtime constraints, detector contracts |
| `audio-window-functions` | numerical analysis; verification | Coherent gain, ENBW, window semantics |
| `audio-fft-spectrum`, `audio-power-spectral-density` | complex numbers; numerical analysis; verification | DFT sign/scaling, one-sided bins, PSD normalization |
| `audio-rms-crest-factor`, `audio-sample-peak`, `audio-true-peak` | numerical analysis; verification; statistics when uncertainty is stated | Crest/sample/true peak definitions, algorithm, calibration, compliance claims |
| `audio-spectrogram-waterfall` | dimensional analysis; linear algebra when needed; verification | STFT frame clocks, display history semantics |

Until then, the links above are **integration instructions**, not an assertion that PR #2 audio files already refer back to these math skills. An audio PR review comment may point to the math PR without changing its code or count.

## Roadmap and review gates

1. **Now:** publish P0 numerical-analysis and verification guidance with executable analytically checkable fixtures; review the four P1 skills for engineering value; keep examples bounded, not universal.
2. **On review:** verify CI and independently inspect the exact checked commit; resolve conceptual inaccuracies; check index and memory navigation.
3. **After audio and math reach compatible bases:** add targeted one-way links in audio skill files, without transporting domain calculations into math.
4. **Demand driven:** transforms, calculus, geometry, discrete mathematics, optimization and advanced statistics; prioritize demonstrated failures and reusable needs, not taxonomy completeness.

**Acceptance evidence to gather:** index discoverability, dependency boundaries, six practical reviews, arithmetic fixtures, branch-scoped memory, audio bridge plan, and explicit unverified claims. Formal standards certification, physical calibration and GPU/realtime behavior are out of scope.

## Primary technical sources

- [BIPM, SI Brochure (9th edition, updated 2026)](https://www.bipm.org/en/publications/si-brochure/) — units and definitions.
- [Python `math` documentation](https://docs.python.org/3/library/math.html) — `fsum`, `hypot`, `isclose` semantics in the test runtime.
- [NumPy linear algebra reference](https://numpy.org/doc/stable/reference/routines.linalg.html) — operations, conditioning and decompositions (optional production backend, not test dependency).
- [NIST Technical Note 1297](https://www.nist.gov/publications/guidelines-evaluating-and-expressing-uncertainty-nist-measurement-results-1994-edition) — uncertainty reporting framework.
