# Skill catalog

These are reusable Kestrel procedures, stored centrally. Read the description and
load only the matching `SKILL.md`. They depend on the surrounding repository and
are not standalone installed host plugins.

| Skill | Trigger |
| --- | --- |
| [kestrel-recall](kestrel-recall/SKILL.md) | Begin or resume a project task; retrieve relevant shared context |
| [kestrel-remember](kestrel-remember/SKILL.md) | Save a useful lesson, decision, project profile, or resumable handoff |
| [kestrel-html-conformance](kestrel-html-conformance/SKILL.md) | Lesson 1: create, edit, generate, or ship HTML; validate final artifacts with the official Nu Html Checker and require a verified zero-error gate |
| [audio-dsp-core](audio-dsp-core/SKILL.md) | Architect or harden audio-analysis data paths, FFT input preparation, energy detection, timing, and measurement contracts; verify with deterministic fixtures |
| [audio-window-functions](audio-window-functions/SKILL.md) | Select and calibrate FFT/STFT windows, including coherent gain, ENBW, leakage, periodicity and verification |
| [audio-fft-spectrum](audio-fft-spectrum/SKILL.md) | Build and audit amplitude spectra, calibrated frequency bins, one-sided FFT scaling, and analytic reference tests |
| [audio-power-spectral-density](audio-power-spectral-density/SKILL.md) | Estimate and verify power density, window-energy normalization, Welch averaging, and Parseval integration |
| [audio-rms-crest-factor](audio-rms-crest-factor/SKILL.md) | Measure RMS, mean-square level, sample-peak-to-RMS ratio, and channel/silence semantics |
| [audio-spectrogram-waterfall](audio-spectrogram-waterfall/SKILL.md) | Build sample-timed STFT histories, calibrated heatmaps, bounded waterfall rendering, and synthetic ridge/impulse fixtures |
| [audio-sample-peak](audio-sample-peak/SKILL.md) | Implement channel-specific sample peaks, timestamps, rolling holds, program peaks and reference threshold diagnostics |
| [audio-true-peak](audio-true-peak/SKILL.md) | Analyze intersample reconstruction, boundary error, oversampling and BS.1770-5 evidence; experimental reference only |
| [audio-dsp-test-fixtures](audio-dsp-test-fixtures/SKILL.md) | Generate reproducible sample-timed audio vectors, test metamorphic and callback invariants, and check independent DSP references |

## Core mathematics (independent curriculum)

Load **only** the relevant module; consult [the mathematics curriculum](../docs/MATH_CURRICULUM.md) for dependencies, assumptions, and the implemented conditional audio-to-math routing. Audio skills retain their measurement and calibration contracts.

| Skill | Trigger |
| --- | --- |
| [math-numerical-analysis](math-numerical-analysis/SKILL.md) | Floating point, error budgets, cancellation, overflow, conditioning and precision |
| [math-verification](math-verification/SKILL.md) | Independent numerical oracles, analytic fixtures, invariants, error bounds and regression evidence |
| [math-dimensional-analysis](math-dimensional-analysis/SKILL.md) | Physical quantities, units, rates, scaling, sample time and dimensional consistency |
| [math-linear-algebra](math-linear-algebra/SKILL.md) | Vectors, matrix operations, coordinate transforms, solves and conditioning |
| [math-complex-numbers](math-complex-numbers/SKILL.md) | Complex arithmetic, polar representations, conjugates, Euler exponentials and phasors |
| [math-probability-statistics](math-probability-statistics/SKILL.md) | Sampling, estimators, distributions, variability and uncertainty |

Add future procedures here as they become useful. Keep project-specific recipes
explicit about their applicability and verified revision. A skill may suggest a
method; it does not supply permission to execute it or override project instructions.
