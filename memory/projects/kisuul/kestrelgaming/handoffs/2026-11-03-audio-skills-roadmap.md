---
schema: 1
id: 2026-11-03-audio-skills-roadmap
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: ChatGPT
created: 2026-11-03
updated: 2026-11-03
sources: "User instructions on 2026-11-03 to implement Kestrel skills incrementally and update memory; STFT/spectrogram implementation 5db19722d453c2447c015ecc85fcc795a11161ad; GitHub Actions run 41759127730, 72 repository tests passed and structural checks passed; SciPy ShortTimeFFT documentation."
---

# Audio-analysis skill library — implementation handoff and running backlog

## Summary

**Goal and acceptance criteria:** Grow Kestrel's reusable, selectively loaded audio engineering skills incrementally. Each completed module needs exact Kestrel skill frontmatter, an indexed trigger, an actionable procedure with real mathematical/standards references, explicit limitations, and proportionate validation. Maintain a checkable backlog and distinguish draft guidance from executed tests and actual host integration.

**Task outcome:** PARTIAL

**Authorized scope and boundaries (historical; recheck on resume):** User explicitly requested implementation on the existing audio-skill branch, in manageable batches, with a running log in Kestrel memory. Kestrel is the skill library. Do not rewrite KESTREL.md/AGENTS.md or imply changes to external audio applications. Branch publication for PR review is intended; merging to main remains a separate decision.

**Target repository, branch, and commit:** Kisuul/KestrelGaming; `skills/audio-dsp-core-foundation-2026-11-03`; PR #2. Historical spectrogram implementation head `5db19722d453c2447c015ecc85fcc795a11161ad`, verified in GitHub Actions run `41759127730`. This handoff evidence edit is a later branch commit; recheck actual HEAD on resuming.

**Memory revision loaded:** `f657bf554c1f4af998596c8815bae8e3b9cb3e34`, including latest indexed handoff, current skill catalog, memory protocols and relevant FFT/window/PSD guidance. User authorized continuation of the planned spectrogram batch.

## Evidence

**Confirmed observations with sources:** PR #2 remains open on the existing audio skill branch. Commit `5db19722d453c2447c015ecc85fcc795a11161ad` added `audio-spectrogram-waterfall`, a time-frequency/rendering reference document, optional host metadata, a tiny deliberately slow STFT oracle, and deterministic fixtures. GitHub Actions run `41759127730` passed Kestrel structural checks and the full **72-test** repository regression suite. This verifies the reference math and index structure, not a rendered waterfall or production audio pipeline.

**Hypotheses and assumptions:** Nine families with eight candidate skills each (72 additions) form a useful *candidate taxonomy*, not an accepted mandatory scope. Two are developed in this batch; some remaining candidates may be renamed, combined, split, or retired after research. A successful mathematical fixture is not proof of production integration, acoustic calibration, realtime performance, or formal standard compliance.

**Decisions and rationale:** Start with shared FFT/window calibration because later skills depend on exact definitions. Keep the skill library centrally indexed and selectively loaded. The spectrogram oracle uses **left-aligned, complete, unpadded frames**, hop in samples, center sample at start+(M-1)/2, and explicit amplitude/PSD modes; this is not identical to every library's centered/padded STFT. Include pure-stdlib oracles for analytic fixtures rather than relying on production code as its own oracle.

**Changed files and uncommitted state to preserve:** This batch: `skills/audio-spectrogram-waterfall/SKILL.md`, its `references/STFT_WATERFALL_CONTRACT.md`, `agents/openai.yaml`, `scripts/reference_stft.py`, `tests/test_audio_stft_reference.py`, `skills/INDEX.md` and this same handoff. No target audio application, root governing contract, or CI policy edited.

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| `python -m unittest -v test_audio_fft_reference.py` | 7 tests passed | Local isolated copy of reference script and tests; check GitHub CI on committed versions |
| `python -m py_compile reference_dft.py test_audio_fft_reference.py` | Passed | Local isolated copy |
| Kestrel structural validator and full regression suite | Both GitHub Actions steps passed in run `41756464057` | Commit `035cb2b03d7cfdb84b8690f1d5ef0be3c6d5148a`; no production analyzer exercised |
| New PSD and RMS deterministic reference tests | GitHub CI run `41757356509` passed; full suite ran 60 tests, OK | Against `a18c90e1ff416ba085a9b2272fcb2f513a7f0885`; not a production DSP or instrument test |
| Spectrogram STFT and waterfall fixtures | GitHub Actions run `41759127730`: structural checks passed and 72 tests, OK | Commit `5db19722d453c2447c015ecc85fcc795a11161ad`; only mathematical/reference fixtures; no GUI visual regression, gap detector or production latency measured |
| DSP instrument compliance | Not assessed | No normative conformance claim |

**Persistence:** Skills (DSP, window, FFT, PSD, RMS, STFT) and this handoff are saved in the existing PR #2 feature branch. STFT module was committed in `5db19722d453c2447c015ecc85fcc795a11161ad`, and this handoff evidence update is a subsequent memory-only branch commit. The branch is **not** integrated into `main` unless merged.

## Running backlog

**Status key:** `BRANCH` = committed to review branch (not necessarily merged); `PENDING` = not yet implemented; `PLANNED` = scope subject to review.

**Current developed skills (6 of 73 candidates total, including the existing foundation):**

- `audio-dsp-core` — BRANCH; central signal path and measurement contracts; earlier batch, PR #2.
- `audio-window-functions` — BRANCH (this batch); periodic/symmetric windows, calibration and ENBW.
- `audio-fft-spectrum` — BRANCH (this batch); amplitude DFT, one-sided bins, calibration and oracle.
- `audio-power-spectral-density` — BRANCH (this batch); density normalization, integrated power, Welch averaging and reference fixtures; CI tests passed for `a18c90e`.
- `audio-rms-crest-factor` — BRANCH (this batch); sample RMS, mean square, sample crest and silence/channel reference fixtures; CI tests passed for `a18c90e`.
- `audio-spectrogram-waterfall` — BRANCH (this batch); STFT sample-time frames, calibrated PSD/amplitude histories and visualization integrity; GitHub Actions `41759127730` passed on `5db1972`.
- **Outstanding: 67 candidates**, including at least the following nine-family backlog.

### Foundation and numerical DSP (7 pending)

`audio-sample-formats`, `audio-timebase-sync`, `audio-resampling`, `audio-channel-mapping`, `audio-filter-design`, `audio-stream-buffering`, `audio-numerical-stability`.

### Levels, loudness, and dynamics (7 pending)

`audio-vu-metering`, `audio-ppm-metering`, `audio-sample-peak`, `audio-true-peak`, `audio-program-loudness`, `audio-loudness-range`, `audio-envelope-dynamics`.

### Spectra and frequency-domain analysis (5 pending)

`audio-fractional-octave-rta`, `audio-multiresolution-spectrum`, `audio-spectral-descriptors`, `audio-harmonic-analysis`, `audio-cepstral-analysis`.

### Oscilloscopes and phase (8 pending)

`audio-oscilloscope`, `audio-scope-triggering`, `audio-vectorscope`, `audio-stereo-correlation`, `audio-mid-side-analysis`, `audio-phase-coherence`, `audio-cross-correlation`, `audio-group-delay`.

### Temporal and music structure (8 pending)

`audio-onset-detection`, `audio-beat-tracking`, `audio-rhythm-analysis`, `audio-pitch-tracking`, `audio-tuning-analysis`, `audio-chroma-harmony`, `audio-event-segmentation`, `audio-temporal-fusion`.

### Quality and distortion diagnostics (8 pending)

`audio-test-signals`, `audio-thd-thdn`, `audio-intermodulation`, `audio-noise-snr-sinad`, `audio-transfer-response`, `audio-clipping-detection`, `audio-dropout-detection`, `audio-codec-artifacts`.

### Acoustics and spatial measurements (8 pending)

`audio-spl-metering`, `audio-microphone-calibration`, `audio-impulse-response`, `audio-room-acoustics`, `audio-speaker-alignment`, `audio-spatial-localization`, `audio-surround-analysis`, `audio-loopback-latency`.

### Speech, perception, and intelligent analysis (8 pending)

`audio-voice-activity`, `audio-formant-analysis`, `audio-speech-intelligibility`, `audio-perceptual-quality`, `audio-psychoacoustics`, `audio-sound-classification`, `audio-source-separation`, `audio-denoising-evaluation`.

### Validation, visualization, and infrastructure (8 pending)

`audio-reference-validation`, `audio-dsp-test-fixtures`, `audio-measurement-uncertainty`, `audio-visualization-integrity`, `audio-color-scale-design`, `audio-realtime-integration`, `audio-offline-analysis`, `audio-analysis-provenance`.

## Next action

**Open blockers or risks:** Recheck the *newest* branch commit and CI before merging or resuming; `41759127730` verifies only the earlier STFT implementation head, not later handoff edits. The reference is O(frames*M*Nfft) and supports complete left-aligned frames but not gap detection, GPU rendering, live reconfiguration or app-level visual regression. Actual target-app integration, sound-level calibration and production timing remain untested. No calibration, real-time benchmarking, third-party instrument comparison, or end-to-end host activation has been performed. The simple reference DFT is O(N^2) and for small analytical fixtures only; it does not establish performance or entire-system correctness. Scope boundaries among candidate skills remain provisional. Agent-host activation is explicitly separate from committing Kestrel skill files.

**Next useful step:** After verifying CI on the spectrogram batch, implement a small `audio-sample-peak` module with per-channel peak, peak hold, overload/clip policy, timestamp and channel fixtures; then consider `audio-true-peak` as a separate, oversampled estimator or `audio-dsp-test-fixtures` for broadly reusable oracle harnesses. Preserve candidate scope boundaries, update this same handoff and never infer audio-app integration from standalone oracle tests.

## Revisit when

At every new batch, on PR merge/rebase, when any standard or authoritative reference changes, or if fixtures reveal incorrect math. Re-read current instructions and revision rather than assuming this backlog is binding authority.
