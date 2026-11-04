---
name: math-probability-statistics
description: Choose descriptive or inferential statistics, check sampling and dependence assumptions, and distinguish estimator variability, prediction and measurement uncertainty.
---

# Probability and statistics — uncertainty with a stated model

## Activate when

Use for samples, random simulation, estimators, intervals, hypothesis tests, prediction or measurement uncertainty. Use [numerical analysis](../math-numerical-analysis/SKILL.md) for arithmetic precision and [verification](../math-verification/SKILL.md) for exact enumeration and model checks. Statistical uncertainty and floating-point error are different quantities.

## Required inputs

Obtain the target population or process, observation units, sampling/repetition mechanism, sample size, time/cluster structure, missing-data handling and the quantity to estimate. Distinguish independent experimental units from repeated readings of the same unit. Ask for missing information when it determines the validity of the intended inference; descriptive summaries can still be reported with that limitation.

## Decision procedure

1. **Choose the question.** Describing observed data requires a defined summary. Estimating a population parameter requires a sampling/model argument. Predicting a future observation additionally requires a predictive distribution. Reporting physical measurement uncertainty requires a measurement equation and uncertainty contributors. Do not answer one question with an interval for another.
2. **Validate inputs and estimator semantics.** State units, exclusions, nonfinite policy and any weights before calculation. Do not silently replace missing values with zero or assume that deleting them preserves representativeness. A mean needs at least one observation; sample variance needs at least two. Frequency, reliability and survey weights have different meanings and variance formulas; `n-1` is not a universal weighted denominator.
3. **Check the model before computing precision.** Identify selection bias, common causes, time correlation, clustering, censoring and missingness. If iid finite-variance observations are defensible, `s^2=sum((xi-xbar)^2)/(n-1)` is unbiased for the common variance and `s/sqrt(n)` estimates the mean's standard error. These are sufficient assumptions, not facts established by a five-point example. If dependence exists, use a justified covariance/cluster/time-series model or resampling scheme that preserves it. If the model is unknown, report descriptive results and mark inferential uncertainty unverified.
4. **Select and qualify inference.** State the estimand, interval/test construction, confidence level, one-/two-sidedness and any multiple-comparison or selection policy. An exact Student-t interval for a mean assumes iid normal observations with an unknown variance. Asymptotic or bootstrap alternatives have their own conditions; small `n` and a passing normality test do not establish them. A frequentist confidence level describes repeated-sampling coverage of the procedure, not posterior probability for a fixed parameter. Bayesian credible intervals require a stated likelihood and prior; prediction intervals concern future values and generally include observation variability.
5. **Separate measurement uncertainty.** Inventory random and systematic contributors, corrections, calibration information, correlations, uncertainty propagation and the reporting/coverage convention. Repetition cannot reveal every common offset. For a differentiable measurement model, first-order covariance propagation uses `J Cov(inputs) J^T`; check whether linearization is adequate. A reported coverage factor alone does not prove a coverage probability or metrological compliance.
6. **Verify the arithmetic and challenge the model.** Use exact small enumeration or analytic moments, then test a plausible violation such as dependence or selection. Seeded pseudorandom simulation checks a specified model; it does not establish that real observations follow it. Inspect sensitivity to exclusions, dependence and distributional assumptions, keeping numerical and sampling error separate.

## Worked examples and failure cases

**Descriptive versus inferential (STA-01).** For `[1,2,3,4,5]` in a stated unit, `xbar=3`, squared deviations sum to `10`, population-form variance of these five values is `10/5=2`, and sample variance is `10/4=2.5` in squared units. Under an iid sampling interpretation, the plug-in SEM is `sqrt(2.5/5)=sqrt(0.5)` in the original unit. The data alone establish none of the sampling assumptions or interval coverage.

**Exact unbiasedness check (STA-02).** Two independent replacement draws from `{0,1}`, each equiprobable, give `00,01,10,11`. Their sample variances are `0,1/2,1/2,0`, whose mean is `1/4`, matching the generating distribution's variance. This proves this finite example, not unbiasedness under arbitrary dependence or missingness.

**Two readings can be one independent draw (STA-03).** Let `Y` take `-1` or `+1` with equal probability and observe `(Y,Y)`. Each possible observed sample (`(-1,-1)` or `(1,1)`) has `s^2=0` and naive plug-in SEM `0`. Yet the sample mean is `Y`, with variance `1`; even the known-variance iid formula would incorrectly give `1/2`. Generally,

`Var(xbar) = [sum_i Var(Xi) + 2 sum_{i<j} Cov(Xi,Xj)] / n^2`.

Here two variance terms contribute `2` and twice the single covariance contributes another `2`, giving `4/4=1`. Positive dependence can inflate variance and negative dependence can reduce it. Do not replace this calculation with an unexplained “effective sample size,” or treat identical readings as proof of certainty.

**Missingness and small samples.** Deleting unobserved high values may bias a mean even when its computed SEM is tiny. With one observation the mean exists but sample variance does not; with repeated identical observations, zero sample scatter does not establish zero population or measurement uncertainty. Record the exclusion rule and unresolved model instead of manufacturing an interval.

## Deliver and acceptance gate

Report the population/process, independent unit, sample size and dependence structure, estimator/denominator, units, exclusions, model assumptions and diagnostics. For any interval include its target, construction and coverage interpretation; for measurements include uncertainty contributors and correlations. Supply one independent arithmetic check and one adverse-model check, distinguishing executed tests from proposed inference validation; the [fixture catalog](../../tests/fixtures/MATH_FOUNDATION_VECTORS.md) records bounded examples STA-01/02/03. Accept inferential precision only when its assumptions and sensitivity support the intended claim.

## References

- [Python `statistics`](https://docs.python.org/3/library/statistics.html) — descriptive sample/population conventions; these APIs do not validate sampling assumptions.
- [NIST e-Handbook: confidence limits for a mean](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm) — normal-model Student-t interval and its interpretation.
- [NIST TN 1297, 1994 edition](https://www.nist.gov/publications/guidelines-evaluating-and-expressing-uncertainty-nist-measurement-results-1994-edition) — measurement uncertainty components, covariance and reporting.

**Limits:** these examples do not establish nominal coverage, a valid dependence model, representative sampling or instrument calibration. Distribution fitting, advanced inference and domain measurement models need task-specific review.
