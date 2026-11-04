---
name: math-linear-algebra
description: Specify and verify vector and matrix operations, coordinate transformations, linear solves and conditioning for graphics, simulation and numerical code.
---

# Linear algebra — explicit transforms and solvable systems

## Activate when

Use for vectors, matrices, projections, coordinate changes, transforms, linear systems, eigenproblems or least squares. Use [numerical analysis](../math-numerical-analysis/SKILL.md) for conditioning and [verification](../math-verification/SKILL.md) for independent cases.

## Procedure

1. State dimensions/shapes, orientation and coordinate frame, storage order versus *mathematical* multiplication order, and units. Baseline is real column vectors and `y = A x`; transformations compose right-to-left (`A(Bx)`). State handedness and active/passive meaning for spatial transforms.
2. Define dot products, matrix products, transpose, norms and determinant only where their domain is meaningful. For complex spaces distinguish transpose from conjugate transpose.
3. For `Ax=b`, inspect rank/conditioning, scale and units, and choose a factorization or library solver rather than materializing `A^-1 b`. For overdetermined/underdetermined systems declare least-squares or regularization policy.
4. For eigenvectors, singular values and decompositions specify symmetry/Hermitian assumptions, sorting, normalization and nonuniqueness. Do not promise a unique basis in repeated-eigenvalue subspaces.
5. Verify by exact small systems, independent residual `r=Ax-b`, composition order tests and degenerate/near-singular cases. A small residual alone cannot guarantee accurate `x`.

## Worked example

For `A=[[3,1],[1,2]]` and `b=[9,8]`, `det(A)=5` and `x=[2,3]`. Direct substitution gives `Ax=[9,8]`. Two matrix transforms that do not commute must not be silently reordered during optimization.

## Acceptance gate

Shapes, units and multiplication convention are documented; at least one exactly solvable fixture and a singular or conditioned negative case are evaluated; any numerical solver claims are limited to tested conditions.

## References

- [NumPy linear algebra documentation](https://numpy.org/doc/stable/reference/routines.linalg.html) — solve, decompositions and condition estimation.
- [SciPy `linalg`](https://docs.scipy.org/doc/scipy/reference/linalg.html) — numerical solvers; optional backend, not required by the standard-library fixtures.

**Limits:** examples are real low-dimensional; matrix library conventions and floating-point errors vary.
