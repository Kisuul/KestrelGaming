---
name: math-linear-algebra
description: Choose and verify vector and matrix operations, coordinate transforms, linear solves and least squares with explicit shapes, rank and conditioning.
---

# Linear algebra — explicit transforms and justified solves

## Activate when

Use for matrix/vector operations, coordinate changes, linear systems or least squares. Load [numerical analysis](../math-numerical-analysis/SKILL.md) when precision or conditioning matters and [verification](../math-verification/SKILL.md) to design independent checks. Shared notation is in [the curriculum](../../docs/MATH_CURRICULUM.md); matrix storage order does not determine mathematical multiplication order.

## Required inputs

Obtain `A`'s shape `(m,n)`, the shape of `b` or other operands, scalar type/precision, units, coordinate frames and the requested result. State whether the problem is an exact solve, least squares, minimum norm or regularized estimation. Record data uncertainty and the application's acceptable solution error before selecting a solver tolerance.

## Procedure

1. **Check the interface.** For `Ax=b`, require `b` to have `m` rows; distinguish a vector `(m,)` from multiple right-hand sides `(m,k)`. Reject ragged/incompatible shapes and unintended broadcasting. Define empty inputs and nonfinite policy explicitly. Baseline is column vectors, `y=Ax`, and composition `A(Bx)` acting right-to-left. For spatial transforms state frames, handedness and active/passive meaning. Check that units agree in every sum; scaling must preserve the intended physical metric.
2. **Choose the mathematical problem and factorization.** Use a tested library and its documented status/rank diagnostics. Select from the table below; do not form an inverse to solve a system. Determinants and Cramer's rule are useful exact small-case derivations, not reliable numerical rank tests or general solver recipes.
3. **Assess rank and sensitivity.** For square nonsingular `A`, use a stated norm and condition estimate `kappa(A)=||A|| ||A^-1||`. For singular values, declare any effective-rank threshold, its scale/units and whether it is heuristic or derived from input uncertainty. Numerical rank depends on that choice; a tiny nonzero determinant is not a policy. Rescaling may improve computation while changing the interpretation of norms or least-squares weights, so report it.
4. **Compute and check independently.** Recompute `r=b-A xhat` from the original inputs with sufficient precision. Report both an absolute residual and, when the denominator is nonzero, `eta=||r||/(||A|| ||xhat||+||b||)` in a consistent norm. This is a normwise backward-error measure; a small value does not establish a small forward error. If the denominator is zero, report the absolute residual and zero-data case directly instead of dividing. For invertible exact `A` and nonzero `b`, `||xhat-x||/||x|| <= kappa(A) ||r||/||b||`; rounded residuals, uncertain data and estimated conditioning limit its use.
5. **Check the requested semantics.** Compare a small exact fixture and a singular/ill-conditioned negative case. For ordinary unweighted least squares check residual orthogonality `A* r≈0` as well as the objective; this stationary condition alone does not establish rank or uniqueness. For complex matrices `A*` means conjugate transpose. If a task needs eigenproblems, specify Hermitian/symmetry assumptions, normalization and nonuniqueness of repeated-eigenvalue subspaces, then use a suitable library routine; the fixtures here do not verify an eigensolver.

| Problem / established prerequisite | Usual choice | Check or boundary |
| --- | --- | --- |
| Square, nonsingular, otherwise general | LU with pivoting | Factorization status, residual and conditioning; pivoting does not cure ill-conditioning |
| Square Hermitian positive definite (real case: symmetric positive definite) | Cholesky | Establish the assumption and handle factorization failure; symmetry alone is insufficient |
| Overdetermined, full column rank, ordinary least squares | QR | Declare the objective and weights; forming `A* A` squares the 2-norm condition number |
| Rank uncertain/deficient or underdetermined | SVD or rank-revealing QR | State rank cutoff and solution policy; SVD supports an explicitly chosen minimum-Euclidean-norm solution |
| Regularized estimation | Method matching the stated penalty/constraints | Regularization changes the problem; report the parameter and bias tradeoff |

## Worked decisions and counterexamples

**Well-conditioned exact check (LIN-01).** For `A=[[3,1],[1,2]]`, the leading principal minors `3` and `5` are positive, so real symmetric `A` is positive definite and Cholesky is appropriate. For `b=[9,8]`, exact substitution verifies `x=[2,3]` and `r=[0,0]`. The rational fixture checks this algebra, not a production Cholesky implementation.

**Small residual, wrong answer (LIN-03).** Let `epsilon=1/10^12`, `A=diag(1,epsilon)`, `b=(1,epsilon)`, and exact `x=(1,1)`. The candidate `xhat=(1,0)` has `r=(0,epsilon)`. In the infinity norm, `||r||/||b||=10^-12` and `eta=5*10^-13`, yet `||xhat-x||/||x||=1`; `kappa_inf(A)=10^12`. A residual-only threshold of `10^-9` accepts a completely wrong second component. Check conditioning and component/application error before accepting it. Every stated value follows from diagonal multiplication and exact rational arithmetic.

**Singular does not specify the outcome (LIN-02).** `A=[[1,2],[2,4]]` has rank one. With `b=(3,6)` it has infinitely many solutions (`x0+2*x1=3`); with `b=(3,7)` it has no exact solution. Choose rejection, least squares or a documented regularized/minimum-norm policy rather than claiming that a solver returned the unique exact answer.

**Composition order.** Scaling the x coordinate by two and then rotating `(1,0)` by 90 degrees gives `(0,2)`; reversing the operations gives `(0,1)`. Preserve frames and multiplication order when optimizing code.

## Deliver and acceptance gate

Report shapes, frames, units, precision, the objective, chosen solver and prerequisites, rank policy, conditioning evidence, residuals and application error criteria. Include independent exact and adverse checks, solver failures and any unverified backend claims; the [fixture catalog](../../tests/fixtures/MATH_FOUNDATION_VECTORS.md) records bounded examples LIN-01/02/03. Accept a result only when those checks support the requested solution accuracy; algebraic fixtures do not certify a numerical library across arbitrary inputs.

## References

- [NumPy linear algebra reference](https://numpy.org/doc/stable/reference/routines.linalg.html) — solve, condition estimates and decompositions; optional backend.
- [NumPy `lstsq`](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html) — rank cutoff and minimum-norm least-squares semantics.
- [SciPy `cholesky`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.cholesky.html) — Hermitian positive-definite prerequisite.

**Limits:** no general solver, rank estimator or eigensolver is implemented here. Rank, regularization and physical error budgets remain task decisions.
