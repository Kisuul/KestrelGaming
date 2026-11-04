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
sources: "User continuation on 2026-11-03 to fill Kestrel audio curriculum; pre-batch branch ed37d679ad6561de9a33011df5069fef765c402d; new sample-peak module and reference tests, GitHub Actions verification pending; ITU-R BS.1770-5 and FADGI peak-reference guidance."
---

# Audio-analysis skill library — implementation handoff and running backlog

## Summary

**Goal and acceptance criteria:** Grow Kestrel's reusable, selectively loaded audio engineering skills incrementally. Each completed module needs exact Kestrel skill frontmatter, an indexed trigger, an actionable procedure with real mathematical/standards references, explicit limitations, and proportionate validation. Maintain a checkable backlog and distinguish draft guidance from executed tests and actual host integration.

**Task outcome:** PARTIAL

**Authorized scope and boundaries (historical; recheck on resume):** User explicitly requested implementation on the existing audio-skill branch, in manageable batches, with a running log in Kestrel memory. Kestrel is the skill library. Do not rewrite KESTREL.md/AGENTS.md or imply changes to external audio applications. Branch publication for PR review is intended; merging to main remains a separate decision.

**Target repository, branch, and commit:** Kisuul/KestrelGaming; `skills/audio-dsp-core-foundation-2026-11-03`; PR #2. Historical spectrogram implementation head `5db19722d453c2447c015ecc85fcc795a11161ad`, verified in GitHub Actions run `41759127730`. This handoff evidence edit is a later branch commit; recheck actual HEAD on resuming.

**Memory revision loaded:** `ed37d679ad6561de9a33011df5069fef765c402d`, including project-scoped handoff and skill catalog. Verified current PR #2 branch is open and contains the six completed foundation and specialist modules; user authorized continued curriculum work.

## Evidence

**Confirmed observations with sources:** PR #2 remains open on the existing audio skill branch; earlier STFT skill passed 72 GitHub repository tests on run `41759127730`, with later handoff-only update verified on run `41759283838`. Current batch adds a distinct `audio-sample-peak` skill, per-channel rolling/program peak reference code, analytical fixtures and test coverage. New batch CI must be checked before claiming a pass.

**Hypotheses and assumptions:** Nine families with eight candidate skills each (72 additions) form a useful *candidate taxonomy*, not an accepted mandatory scope. Two are developed in this batch; some remaining candidates may be renamed, combined, split, or retired after research. A successful mathematical fixture is not proof of production integration, acoustic calibration, realtime performance, or formal standard compliance.

**Decisions and rationale:** Start with shared FFT/window calibration because later skills depend on exact definitions. Keep the skill library centrally indexed and selectively loaded. The spectrogram oracle uses **left-aligned, complete, unpadded frames**, hop in samples, center sample at start+(M-1)/2, and explicit amplitude/PSD modes; this is not identical to every library's centered/padded STFT. Include pure-stdlib oracles for analytic fixtures rather than relying on production code as its own oracle.

**Changed files and uncommitted state to preserve:** Current batch changes `skills/audio-sample-peak/` (skill, calibration contract, optional host metadata, reference tracker), `tests/test_audio_sample_peak_reference.py`, `skills/INDEX.md`, and this existing indexed handoff. No target-app code, operating contract, root agent instructions, or CI policy modified.

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| `python -m unittest -v test_audio_fft_reference.py` | 7 tests passed | Local isolated copy of reference script and tests; check GitHub CI on committed versions |
| `python -m py_compile reference_dft.py test_audio_fft_reference.py` | Passed | Local isolated copy |
| Kestrel structural validator and full regression suite | Both GitHub Actions steps passed in run `41756464057` | Commit `035cb2b03d7cfdb84b8690f1d5ef0be3c6d5148a`; no production analyzer exercised |
| New PSD and RMS deterministic reference tests | GitHub CI run `41757356509` passed; full suite ran 60 tests, OK | Against `a18c90e1ff416ba085a9b2272fcb2f513a7f0885`; not a production DSP or instrument test |
| Spectrogram STFT and waterfall fixtures | GitHub Actions run `41759127730`: structural checks passed and 72 tests, OK | Commit `5db19722d453c2447c015ecc85fcc795a11161ad`; only mathematical/reference fixtures; no GUI visual regression, gap detector or production latency measured |
| Sample-peak reference fixtures and peak-hold behavior | Not run at first batch commit; pending CI | Require sample-index timing, multi-channel hold and reference threshold tests; no true-peak/clipping verdict implied |
| DSP instrument compliance | Not assessed | No normative conformance claim |

**Persistence:** Skills (DSP, window, FFT, PSD, RMS, STFT) and this handoff are saved in the existing PR #2 feature branch. STFT module was committed in `5db19722d453c2447c015ecc85fcc795a11161ad`, and this handoff evidence update is a subsequent memory-only branch commit. The branch is **not** integrated into `main` unless merged.

## Running backlog

**Status key:** `BRANCH` = committed to review branch (not necessarily merged); `PENDING` = not yet implemented; `PLANNED` = scope subject to review.

**Current developed skills (7 of 73 candidates total, including the existing foundation):**

- `audio-dsp-core` — BRANCH; central signal path and measurement contracts; earlier batch, PR #2.
- `audio-window-functions` — BRANCH (this batch); periodic/symmetric windows, calibration and ENBW.
- `audio-fft-spectrum` — BRANCH (this batch); amplitude DFT, one-sided bins, calibration and oracle.
- `audio-power-spectral-density` — BRANCH (this batch); density normalization, integrated power, Welch averaging and reference fixtures; CI tests passed for `a18c90e`.
- `audio-rms-crest-factor` — BRANCH (this batch); sample RMS, mean square, sample crest and silence/channel reference fixtures; CI tests passed for `a18c90e`.
- `audio-spectrogram-waterfall` — BRANCH (this batch); STFT sample-time frames, calibrated PSD/amplitude histories and visualization integrity; GitHub Actions `41759127730` passed on `5db1972`.
- `audio-sample-peak` — BRANCH (this batch); sample maxima, earliest tie, per-channel program/rolling peak, exact hold expiry and threshold semantics; new CI pending.
- **Outstanding: 66 candidates**, including at least the following nine-family backlog.

### Foundation and numerical DSP (7 pending)

`audio-sample-formats`, `audio-timebase-sync`, `audio-resampling`, `audio-channel-mapping`, `audio-filter-design`, `audio-stream-buffering`, `audio-numerical-stability`.

### Levels, loudness, and dynamics (6 pending)

`audio-vu-metering`, `audio-ppm-metering`, `audio-true-peak`, `audio-program-loudness`, `audio-loudness-range`, `audio-envelope-dynamics`.

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

**Open blockers or risks:** Check new `audio-sample-peak` commit and CI before merging or resuming; previous STFT CI does not prove the latest code. The reference rolling maximum is a trailing sample-count window, not a display envelope with separate release ballistics; threshold hits do not establish recorded clipping. The reference is O(frames*M*Nfft) and supports complete left-aligned frames but not gap detection, GPU rendering, live reconfiguration or app-level visual regression. Actual target-app integration, sound-level calibration and production timing remain untested. No calibration, real-time benchmarking, third-party instrument comparison, or end-to-end host activation has been performed. The simple reference DFT is O(N^2) and for small analytical fixtures only; it does not establish performance or entire-system correctness. Scope boundaries among candidate skills remain provisional. Agent-host activation is explicitly separate from committing Kestrel skill files.

**Next useful step:** After verifying CI on `audio-sample-peak`, implement `audio-true-peak` separately, scoped to ITU-R BS.1770-5 intersample reconstructed-peak estimation, oversampling/filter response, boundary/latency handling, reference vectors and accuracy limits. If validation cannot meet conformance criteria, keep a clear *experimental estimator* label. Alternatively develop `audio-dsp-test-fixtures` to strengthen independent oracles before advanced measurement skills. Continue updating this handoff and keep all 66 other candidates visible.

## Revisit when

At every new batch, on PR merge/rebase, when any standard or authoritative reference changes, or if fixtures reveal incorrect math. Re-read current instructions and revision rather than assuming this backlog is binding authority.
