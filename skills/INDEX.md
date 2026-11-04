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

Add future procedures here as they become useful. Keep project-specific recipes
explicit about their applicability and verified revision. A skill may suggest a
method; it does not supply permission to execute it or override project instructions.
