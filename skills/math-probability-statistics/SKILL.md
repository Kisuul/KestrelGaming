---
name: math-probability-statistics
description: Distinguish population and sample statistics, estimator bias, sampling variability, distributions, confidence intervals and measurement uncertainty.
---

# Probability and statistics — uncertainty with stated assumptions

## Activate when

Use for descriptive summaries, random simulation, signal/noise samples, estimators, significance tests, confidence or coverage intervals, prediction and reported measurement uncertainty. For numerical precision consult [numerical analysis](../math-numerical-analysis/SKILL.md); for testing consult [verification](../math-verification/SKILL.md).

## Procedure

1. Specify population, sampling mechanism, random variable, units, repeated observations, independence/dependence, missingness and whether the goal is describing observed samples, estimating a parameter or predicting future values. Seeded pseudorandom tests are deterministic *checks*, not evidence that physical randomness meets a distribution.
2. Declare the estimator and denominator: population mean/variance versus sample mean and unbiased sample variance (`n-1` only under the usual iid/common-mean assumptions). Handle `n=0` and `n=1`, nonfinite inputs and weights explicitly.
3. Distinguish standard deviation (scatter of observations), standard error (uncertainty of an estimator), numerical error and measurement uncertainty. The common `s/sqrt(n)` standard error needs an appropriate independence model; autocorrelation reduces effective sample size.
4. Choose distribution assumptions and diagnostics before inferential claims. State statistic, one-/two-sidedness, confidence level, interval construction and whether repeated-sampling coverage assumptions apply. Do not equate a confidence interval to a posterior probability for a fixed parameter.
5. For physical measurements, inventory systematic and random contributors, correlations, calibration, coverage factor and reporting convention; use [NIST TN 1297](https://www.nist.gov/publications/guidelines-evaluating-and-expressing-uncertainty-nist-measurement-results-1994-edition) where appropriate, without claiming metrological compliance from sample SD alone.
6. Verify small exact examples and enumeration/simulation with documented assumptions. For a production statistical inference, review model fit and sensitivity rather than only a passing unit test.

## Worked example

For observations `[1,2,3,4,5]`, sample mean is `3`, unbiased sample variance is `2.5`, sample SD is `sqrt(2.5)`, and iid-assumption plug-in standard error of the mean is `sqrt(2.5/5)=sqrt(0.5)≈0.7071`. This is **not by itself** a valid confidence interval or a calibrated instrument uncertainty.

## Acceptance gate

The model, estimator, denominator and unit are explicit; a small independently derived example passes; correlation/bias/coverage caveats appear when relevant; statistical precision is not conflated with floating-point accuracy.

## References

- [Python `statistics`](https://docs.python.org/3/library/statistics.html) — sample/population conventions.
- [NIST TN 1297](https://www.nist.gov/publications/guidelines-evaluating-and-expressing-uncertainty-nist-measurement-results-1994-edition) — uncertainty components and reporting.
- [SciPy `stats`](https://docs.scipy.org/doc/scipy/reference/stats.html) — optional distributions and inference routines.

**Limits:** five-number example does not validate an iid assumption, nominal interval coverage or any physical instrument.
