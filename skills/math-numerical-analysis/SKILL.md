---
name: math-numerical-analysis
description: Diagnose and prevent numerical cancellation, loss of precision, overflow, underflow, unstable algorithms and misleading tolerances in engineering calculations.
---

# Numerical analysis — trustworthy finite arithmetic

## Activate when

Use when implementing or reviewing floating-point calculations, accumulations, solvers, simulation steps, quantization or precision-sensitive comparisons. Load only the needed companion: [verification](../math-verification/SKILL.md) for evidence, [dimensions](../math-dimensional-analysis/SKILL.md) for quantities, [linear algebra](../math-linear-algebra/SKILL.md) for matrix problems. Shared notation is in the [curriculum](../../docs/MATH_CURRICULUM.md). This skill does not define a production numerical library.

## Required inputs

Identify the mathematical function/problem; valid input domain and shape; quantity and unit of each result; input uncertainty; required output accuracy; and actual storage/intermediate types, rounding, range and backend. A decimal input specification and its rounded binary representation are different inputs. If a requirement is missing, state a bounded assumption before choosing a tolerance.

## Decision procedure

1. **Define the target.** Separate the exact problem from the approximation: measured inputs, represented inputs, discretized model, stopping rule and computed answer. Check domain restrictions before arithmetic. Empty input and invalid shape need a defined result or rejection.
2. **Assess conditioning before blaming the algorithm.** Perturb inputs by their stated uncertainty and inspect output sensitivity, using derivatives or finite perturbations within the valid domain. For scalar `f`, local relative conditioning is `abs(x*f'(x)/f(x))` when defined; use absolute sensitivity near zero. Finite perturbations, multiple inputs, constraints and nonsmooth points need their own analysis. Higher precision cannot recover information absent from the inputs.
3. **Diagnose algorithmic error separately.** Forward error compares the computed answer to the exact answer for the specified input. Backward error asks how much that input must change to make the computed answer exact. A small backward error can coexist with large forward error in an ill-conditioned problem. Compare against exact/high-precision evaluation of the *same represented inputs*, then vary input uncertainty separately.
4. **Choose a method for the observed failure.** Use `log1p`/`expm1` for small increments, rationalization for cancellative formulas, scaled norms for premature overflow, and accurate/pairwise/compensated summation as appropriate. For systems use a suitable library solve rather than an explicit inverse. Confirm the reformulation preserves the domain and boundary semantics; it may move overflow or cancellation elsewhere.
5. **Allocate error in the result's units.** Account for propagated input uncertainty, input representation, model/truncation error, arithmetic error and iteration error without counting one source twice. Add justified worst-case bounds expressed in the same metric; combine statistically only under an explicit dependence model. When no bound is available, label an empirical tolerance as heuristic and state its tested range. Do not widen it merely to pass a failing example.
6. **Specify edge behavior.** Reject, propagate or flag NaN/Inf explicitly. Decide whether signed zero matters, whether gradual underflow is present, and what happens at range limits. Scaling can prevent an intermediate overflow but cannot make an unrepresentable final answer representable. See [diagnostics and adversarial examples](references/DIAGNOSTICS.md).
7. **Verify and report.** Exercise an independently derived reference, a deliberately failing alternative and relevant boundaries. Use the exact [comparison policy](../math-verification/references/FIXTURE_POLICY.md); record backend/version, actual errors, thresholds and checks run. Separate rounding evidence from model accuracy and physical uncertainty.

## Worked contrast: conditioning and stability

For `f(a,b)=a+b`, take exact binary inputs `a=1`, `b=-1+2^-40`. Their sum is `2^-40`. A correctly rounded addition is stable; the componentwise relative condition number is `(abs(a)+abs(b))/abs(a+b) = 2^41-1`. Tiny uncertainty in the two inputs can dominate the small answer even when arithmetic is exact. Changing the summation algorithm does not remove that sensitivity.

By contrast, `g(x)=sqrt(1+x)-1` is well-conditioned in *relative input x* near positive zero: its relative condition number tends to `1`. At binary64 `x=1e-16`, rounding `1+x` to `1` makes the direct formula return `0`, losing the answer near `5e-17`. The equivalent `x/(sqrt(1+x)+1)` retains it. This repairs the evaluation near zero; it is not a universal formula for all magnitudes or domains. The [diagnostics reference](references/DIAGNOSTICS.md) derives both examples and records their limitations.

## Output and acceptance gate

Return the problem/domain/units and representation, conditioning diagnosis, chosen method and reason, error budget or labeled heuristic, finite/boundary policy, and executed evidence with remaining gaps. Acceptance requires at least one independent reference and one relevant counterexample; a good residual or a higher precision setting alone is insufficient. The [fixture catalog](../../tests/fixtures/MATH_FOUNDATION_VECTORS.md) demonstrates selected cases, not every procedure above.

## Technical references

- [Python `math`](https://docs.python.org/3/library/math.html) and [floating-point tutorial](https://docs.python.org/3/tutorial/floatingpoint.html): API behavior, representation and rounding; record the actual Python version used.
- [LAPACK Users' Guide: error bounds and condition estimates](https://www.netlib.org/lapack/lug/node75.html): forward/backward error and conditioning for linear systems.

No cross-runtime accuracy, performance or standards conformance follows from this guidance or its small fixture set.
