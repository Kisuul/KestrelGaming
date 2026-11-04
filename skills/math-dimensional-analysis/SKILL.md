---
name: math-dimensional-analysis
description: Check quantity dimensions, physical units, conversion factors, rates and logarithmic references before engineering calculations and API integration.
---

# Dimensional analysis — quantities before numbers

## Activate when

Use when code mixes physical quantities, conversions, sampled time, rates, sensor readings or logarithmic levels. Load only for those boundaries. Follow the shared [curriculum conventions](../../docs/MATH_CURRICULUM.md); application models and calibration remain domain-owned.

## Required inputs

For each value record its **quantity kind** (duration, energy, torque, temperature point, etc.), numeric value, unit, scale/reference, and validity range. Record whether an offset quantity is a point or an interval. For sampled data require the clock/timebase, actual or assumed sample rate, count meaning and timestamp origin. If these are missing, retain a symbolic result or identify the missing input before presenting a physical result.

A dimension describes powers of base quantities; a unit supplies scale; quantity kind supplies meaning. Energy and torque both have dimension `M L² T^-2`, but their shared dimension does not authorize adding them. Angles, cycle counts and sample counts can all have SI dimension one while retaining different semantic labels.

## Procedure

1. **Normalize the schema before arithmetic.** For this package's SI exponent representation use exactly seven finite real exponents in the declared order `(length, mass, time, electric current, thermodynamic temperature, amount of substance, luminous intensity)`. Reject a malformed vector before combining it: `zip` alone silently truncates unequal lengths. Other bases require an explicit mapping; seven entries alone do not establish matching order or meaning.
2. **Select the operation.** Multiplication/division add/subtract exponents; powers multiply them. Addition/subtraction require compatible quantity kinds and conversion to a common unit scale, as well as equal dimensions. Keep scale factors separate from dimension exponents. A dimensionally consistent formula still needs a valid physical model.
3. **Separate points from intervals.** For temperature points, `T_K = t_°C + 273.15`; intervals satisfy `ΔT_K = Δt_°C`. Subtracting two points produces an interval; adding an interval to a point produces a point. Do not apply the point offset to an interval or treat point-plus-point as ordinary quantity addition.
4. **Resolve logarithmic references before taking logs.** A power level is `10 log10(P/P₀)` dB for positive `P,P₀`. An amplitude level may use `20 log10(|A|/A₀)` only when the compared power ratio equals `(|A|/A₀)²` under the stated model and reference conditions. For voltage-like quantities this can require equal impedances. A signed amplitude's sign/phase is separate. Decide explicitly whether zero is represented as `-∞` or rejected; reject negative power/reference and unspecified references. Convert power levels to linear powers before summing powers. Coherent amplitudes require phase information and a different operation.
5. **Check clocks and counts.** At constant rate `f_s > 0`, a buffer of `N` samples represents `N/f_s` seconds of sample intervals, while the span between its first and last sample timestamps is `(N-1)/f_s` for `N ≥ 1`. Frames, samples and clock ticks are not interchangeable; a frame hop of `H` samples has duration `H/f_s`. Nominal rate is an assumption when clock error matters. Label radians and distinguish angular frequency `ω=2πf` from cycles per second.
6. **Verify a known value and a rejection.** Prefer exact rational/decimal definitions for conversion references; round trips alone can preserve a wrong scale. Use [math verification](../math-verification/SKILL.md) for comparison policy and [numerical analysis](../math-numerical-analysis/SKILL.md) for rounding/overflow. Keep measurement uncertainty separate from arithmetic precision.

## Worked and adversarial examples

| Input / tempting mistake | Correct decision and independently checkable result |
| --- | --- |
| `1000` samples, constant `48000` samples/s; use count as seconds | Buffer duration is `1000/48000 = 1/48 s`. First-to-last timestamp span is `999/48000 = 333/16000 s`. Which duration is needed comes from the interface contract. |
| Acceleration `(1,0,-2,0,0,0,0)` times mass `(0,1,0,0,0,0,0)` | Componentwise exponent addition gives force `(1,1,-2,0,0,0,0)`. A six-entry operand must fail before addition, even if its prefix looks valid. |
| Add `2 m` and `3 s`, or energy and torque with equal dimensions | Reject the first by dimension and the second by quantity kind. A unit conversion cannot repair either invalid operation. |
| Convert temperature rise `100 °C` by adding `273.15` | An interval is `100 K`. Only the point `100 °C` is `373.15 K`; subtracting points `100 °C - 0 °C` gives `100 K`. |
| Amplitude ratio `2`, power ratio `4`, with compatible model/references | `20 log10(2)=10 log10(4)≈6.020599913279624 dB`. Equal amplitude ratios with different impedances need not imply this power ratio. |
| Add two independent power contributions each `0 dB re 1 mW` as `0+0` | Linear powers sum to `2 mW`; the total is `10 log10(2)≈3.010299956639812 dB re 1 mW`. Mixing references or summing coherent waves without phase is a different, unresolved problem. |

## Output and acceptance gate

Return the quantity schema, converted expression with units, point/interval or logarithmic model, clock assumptions, numeric result/precision and independent reference check. Include the rejected invalid case and its reason. Accept only when dimensions, kind, scale and reference agree with the intended operation; disclose missing model or calibration information rather than inferring it. The [fixture catalog](../../tests/fixtures/MATH_FOUNDATION_VECTORS.md) covers selected examples, not a complete units engine or validation of physical models.

## References

- [BIPM SI Brochure, 9th edition](https://www.bipm.org/en/publications/si-brochure/) — base quantities, units, quantity equations, temperature and dimension-one quantities; consult the edition/update actually used when definitions matter.
- [NIST SP 811, 2008 edition](https://www.nist.gov/pml/special-publication-811) — unit notation and logarithmic quantities, especially section 8.7; its older numerical constants are not a replacement for current SI definitions.

**Limits:** dimensional consistency does not establish model correctness, clock accuracy, instrument calibration or standards conformance. The seven-component representation is an example schema, not an installed runtime API.
