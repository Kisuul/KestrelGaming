---
name: math-dimensional-analysis
description: Check quantity dimensions, physical units, conversion factors, rates and logarithmic references before engineering calculations and API integration.
---

# Dimensional analysis — quantities before numbers

## Activate when

Use when code mixes units, physical quantities, sampled time, rates, distances, amplitudes, sensor readings or scaled measurements. The **unit and meaning** belong with a numeric observation; an unlabeled numeric value is not a measurement.

## Procedure

1. Name quantities and units at each input/output boundary. Use SI base dimensions (`L, M, T, I, Θ, N, J`) or a clearly declared alternative; keep numerical scale factor separate from dimensional exponent.
2. Verify units for multiplication, division and powers by exponent arithmetic. Addition/subtraction require compatible quantities and conversion to a shared unit; identical dimensions alone may not imply meaningful addition (e.g. torque vs energy).
3. Handle offset quantities (°C vs K) and logarithmic quantities (dB) using the correct affine/reference relationships, not simple multiplication. State whether a ratio refers to amplitude (typically `20 log10`) or power (typically `10 log10`), and the reference for its level. Do not add logarithmic levels as if they were linear powers.
4. Record frequency/time conventions and explicit sampling rate; distinguish seconds, sample counts, frame counts and clock ticks. Radians are dimensionless in SI but must be labeled where semantically important.
5. Validate conversions against exact definitions when available, then use [math-verification](../math-verification/SKILL.md) for reference fixtures and [numerical analysis](../math-numerical-analysis/SKILL.md) for overflow/precision.

## Worked example

`1000 samples / 48000 samples·s^-1 = 1/48 s ≈ 0.0208333333333333 s`. The sample count is not itself a duration, and changing sample rate changes the duration. Acceleration dimension: `L T^-2`; multiplying by mass yields force dimension `M L T^-2`. Temperature points require an offset: `0 °C = 273.15 K`, while a temperature interval of `100 °C` equals `100 K`. With the same reference and the correct amplitude-power relationship, `20 log10(2) = 10 log10(4) ≈ 6.0206 dB`; this does not license adding unrelated dB values.

## Acceptance gate

Every public value has a unit/reference, conversions are reversible within stated precision, affine/logarithmic exceptions are documented, and a test would reject an incompatible dimension or reference.

## References

- [BIPM SI Brochure, 9th edition (updated 2026)](https://www.bipm.org/en/publications/si-brochure/) — current SI definitions.
- [NIST SP 811](https://www.nist.gov/pml/special-publication-811) — usage and unit notation.

**Limits:** dimensional consistency is necessary but not sufficient for physical correctness; these examples do not constitute a units engine.
