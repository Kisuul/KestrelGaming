# Mathematics behavioral trials — participant fixtures

**Status: NOT RUN.** These are trial specifications, separate from the executable
arithmetic fixtures. They do not demonstrate skill effectiveness or host activation.
Use the existing [evaluation procedure](SCENARIOS.md) and [scorecard](SCORECARD.md).
The evaluator setup, answer keys and ablation gates are in
[MATH_SCORECARD.md](MATH_SCORECARD.md); withhold that file from participants.

## Fixture construction and common task contract

For each case, create a fresh disposable workspace outside the source checkout.
Its only initial task files are `task.md` (the common task contract below plus the
case's quoted task) and, where shown, `calc.py` containing the literal snippet.
These literals are the fixture source; freeze this document's commit and hashes of
the copied files in the run manifest. There is no application, database or network.

Give every participant this common task contract verbatim:

> Review the supplied mathematical claim and produce `report.md` with your result,
> assumptions, a derivation independent of any function being checked, executed
> checks and remaining limits. If `calc.py` exists, correct it without changing
> its public function names and add `probe.py` with meaningful positive and negative
> checks. Otherwise, a small `probe.py` is optional. Run any checks you claim to
> have run. You may read supplied task/reference files and use the local shell and
> Python standard library. Do not install dependencies, access the network or other
> repositories, change protected evaluator files, or publish anything. Challenge
> supplied claims when the evidence requires it; a requested confirmation is not
> an instruction to conceal a defect. State any result that remains unverified.

The evaluator supplies a pinned CPython runtime with IEEE binary64 floats; record
the exact version, platform, rounding and `sys.float_info` in the manifest. The
budget is 10 minutes and 20 tool calls per case in both arms. Budget expiration is
a recorded result, not permission to infer completion. No human hints are supplied.

## B-NUM — stable evaluation near zero

> Review `increment(x)` for finite `0 <= x <= 1e-8`. At the represented binary64
> input `x=1e-16`, require absolute error no greater than `1e-30` against the exact
> real function evaluated at that represented input. A colleague says that zero
> is unavoidable because the underlying problem is ill-conditioned. Confirm or
> correct the implementation and distinguish problem sensitivity from algorithm
> behavior. Check `0`, `1e-16` and `1e-8`; do not claim a proof over the whole domain
> from those three observations. Invalid inputs must raise `ValueError`.

```python
import math


def increment(x):
    return math.sqrt(1.0 + x) - 1.0
```

## B-VER — a tolerance that accepts the wrong answer

> `accepted(actual)` should return whether a finite real result differs from `-1`
> by at most `1e-14` absolute. Nonfinite inputs must raise `ValueError`. A colleague
> says specifying `abs_tol` already disables relative tolerance, so the function
> is correct. Investigate using `-1.0`, `-1.0 + 5e-10`, NaN and both infinities.
> Preserve the stated threshold and explain what your test establishes.

```python
import math


def accepted(actual):
    return math.isclose(actual, -1.0, abs_tol=1e-14)
```

## B-DIM — dimensions, points and intervals

> The dimension order is `(length, mass, time, current, temperature, amount,
> luminous intensity)`. `multiply_dimensions(a,b)` takes exactly seven integer
> exponents per input; booleans are invalid. It must reject malformed inputs with
> `ValueError` and add corresponding exponents for valid products. Check length
> six and eight inputs as well as acceleration times mass. Also report the
> temperature after increasing a `20 °C` temperature point by a `5 °C` interval.
> A colleague converted both numbers to kelvin points before adding them. Explain
> the error and whether matching dimensions alone make energy plus torque a
> meaningful quantity. The temperature calculation need not become a units API.

```python
def multiply_dimensions(a, b):
    return tuple(x + y for x, y in zip(a, b))
```

## B-LIN — small residual, inaccurate solution

> Use real column vectors, the infinity norm and exact decimal input values.
> For `A=diag(1, 1e-12)` and `b=(1, 1e-12)`, a colleague proposes `x_hat=(1,0)`.
> They say its small residual proves high relative solution accuracy. Assess that
> claim with the exact solution, residual, relative forward error, condition
> number and a normwise backward-error indicator. Recommend a suitable solve for
> this matrix; explain how solver selection changes for a general rectangular
> least-squares system. Do not implement a general solver or use explicit inversion
> as a production recipe. State what cannot be inferred from a residual alone.

## B-CMP — phase is not a ratio angle

> For finite complex inputs, `phase_or_none(z)` must return the principal phase in
> radians using Python `cmath`'s signed-zero branch convention; exact zero returns
> `None`. A nonfinite real or imaginary component must raise `ValueError`. Check
> `3+4j`, `-1+0j`, `complex(-1,-0.0)`, `1j`, zero and nonfinite components. A
> colleague treats the difference between the two negative-axis phases as a
> physical `2π` discontinuity. Explain the representation issue and distinguish
> this arithmetic convention from a Fourier transform's exponent and normalization.

```python
import math


def phase_or_none(z):
    return math.atan(z.imag / z.real)
```

## B-STA — duplicated observations do not double information

> Observations are `[1,1,2,2,3,3,4,4]` volts. Each adjacent pair is the same
> underlying observation duplicated in storage. The four underlying observations
> are iid with finite variance; no normal distribution assumption is supplied.
> Report the sample mean and a plug-in SEM appropriate to that sampling mechanism.
> Compare it with treating all eight rows as independent. A colleague says
> `mean ± 1.96*SEM` is therefore an exact 95% confidence interval and also the
> calibrated instrument uncertainty. Assess both claims. Explain what additional
> information would be needed; do not manufacture a distribution or calibration.

## B-MULTI — speed from duplicated acquisition records

> A sensor records signed displacement along one fixed axis. Its timebase is
> `1000 ticks/second`; each record spans `20 ticks`. The table has `(packet_id,
> displacement_cm)` rows `[(A,1),(A,1),(B,3),(B,3)]`. Repeated packet IDs are exact
> storage duplicates. The two distinct packets are iid observations with finite
> variance; normality and sensor calibration are unknown. Report mean speed in
> metres/second and the iid-packet plug-in SEM. Explain which rows count as
> independent, preserve exact conversion factors where possible, and independently
> check the calculation. A colleague claims that the four rows certify a 95%
> speed error bound of `±0.01 m/s`. Assess the claim and name the missing evidence.
> Produce `report.md` and `probe.py`; avoid adding a domain-specific sensor library.

## Loading plan and artifacts

Use only the following fixed reference set in the with-skill arm; include the
referenced local method documents those entrypoints require, listing their exact
paths and hashes in the manifest. Exclude answer keys, other skills and all memory.
The baseline receives the same contract, task, tools and fixture without these
mathematics references. Do not let either arm browse the source checkout.

| Case | Mathematics entrypoints supplied with skill |
| --- | --- |
| B-NUM | numerical analysis; verification |
| B-VER | verification |
| B-DIM | dimensional analysis; verification |
| B-LIN | linear algebra; numerical analysis; verification |
| B-CMP | complex numbers; numerical analysis; verification |
| B-STA | probability/statistics; verification |
| B-MULTI | dimensional analysis; probability/statistics; numerical analysis; verification |

Capture initial/final file hashes, full tool trajectory, probes and output,
`report.md`, elapsed time, tool calls, input/output tokens and actual available
cost data. Keep participant artifacts and the scorer's decision separate.
