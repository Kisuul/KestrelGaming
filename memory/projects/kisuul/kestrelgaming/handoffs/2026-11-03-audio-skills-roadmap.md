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
sources: "User requests on 2026-11-03 to incrementally implement Kestrel audio skills and resume from memory; live branch 14dcdd2eb3ed9afa0d1dad0049cd1a3672b36db1; SciPy periodogram/Welch and ITU-R BS.1770 references; proposed PSD/RMS skill batch; CI validation pending on new commit."
---

# Audio-analysis skill library — implementation handoff and running backlog

## Summary

**Goal and acceptance criteria:** Grow Kestrel's reusable, selectively loaded audio engineering skills incrementally. Each completed module needs exact Kestrel skill frontmatter, an indexed trigger, an actionable procedure with real mathematical/standards references, explicit limitations, and proportionate validation. Maintain a checkable backlog and distinguish draft guidance from executed tests and actual host integration.

**Task outcome:** PARTIAL

**Authorized scope and boundaries (historical; recheck on resume):** User explicitly requested implementation on the existing audio-skill branch, in manageable batches, with a running log in Kestrel memory. Kestrel is the skill library. Do not rewrite KESTREL.md/AGENTS.md or imply changes to external audio applications. Branch publication for PR review is intended; merging to main remains a separate decision.

**Target repository, branch, and commit:** Kisuul/KestrelGaming; `skills/audio-dsp-core-foundation-2026-11-03`. Initial head `00de8633c83e6bf1103f624b5ac513387e40e96b`; first skill-expansion commit `035cb2b03d7cfdb84b8690f1d5ef0be3c6d5148a`. Resume from the live PR #2 branch head, not this historical SHA.

**Memory revision loaded:** `14dcdd2eb3ed9afa0d1dad0049cd1a3672b36db1`, including the current handoff, project index, DSP, window and FFT skills; current user request explicitly resumes this task.

## Evidence

**Confirmed observations with sources:** PR #2 remains open on the existing audio skill branch. Prior DSP/window/FFT batch has green GitHub workflow checks (`41756464057`). Current resumed batch adds `audio-power-spectral-density` and `audio-rms-crest-factor`, independent references, Python small-fixture oracles, and deterministic unit tests. Its commit and verification must be checked before reporting success.

**Hypotheses and assumptions:** Nine families with eight candidate skills each (72 additions) form a useful *candidate taxonomy*, not an accepted mandatory scope. Two are developed in this batch; some remaining candidates may be renamed, combined, split, or retired after research. A successful mathematical fixture is not proof of production integration, acoustic calibration, realtime performance, or formal standard compliance.

**Decisions and rationale:** Start with shared FFT/window calibration because multiple later skills depend on exact definitions. Keep the skill library centralized and selectively loaded. Include executable pure-stdlib reference checks rather than depending on a production DSP implementation as its own oracle.

**Changed files and uncommitted state to preserve:** This batch: `skills/INDEX.md`, `skills/audio-power-spectral-density/` (skill, reference, agent metadata and oracle), `skills/audio-rms-crest-factor/` (skill, reference, metadata and oracle), `tests/test_audio_psd_reference.py`, `tests/test_audio_levels_reference.py`, and this same handoff. Existing other files are unchanged. Intended for existing PR #2 branch; no application repository changes.

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| `python -m unittest -v test_audio_fft_reference.py` | 7 tests passed | Local isolated copy of reference script and tests; check GitHub CI on committed versions |
| `python -m py_compile reference_dft.py test_audio_fft_reference.py` | Passed | Local isolated copy |
| Kestrel structural validator and full regression suite | Both GitHub Actions steps passed in run `41756464057` | Commit `035cb2b03d7cfdb84b8690f1d5ef0be3c6d5148a`; no production analyzer exercised |
| New PSD and RMS deterministic reference tests | Not yet run at handoff authoring | Check CI after publishing new batch; do not invent results |
| DSP instrument compliance | Not assessed | No normative conformance claim |

**Persistence:** The skills and handoff were saved to review branch PR #2, initially in commit `035cb2b03d7cfdb84b8690f1d5ef0be3c6d5148a`; this handoff verification edit is a subsequent branch commit. Neither is integrated into `main` unless PR #2 is merged.

## Running backlog

**Status key:** `BRANCH` = committed to review branch (not necessarily merged); `PENDING` = not yet implemented; `PLANNED` = scope subject to review.

**Current developed skills (5 of 73 candidates total, including the existing foundation):**

- `audio-dsp-core` — BRANCH; central signal path and measurement contracts; earlier batch, PR #2.
- `audio-window-functions` — BRANCH (this batch); periodic/symmetric windows, calibration and ENBW.
- `audio-fft-spectrum` — BRANCH (this batch); amplitude DFT, one-sided bins, calibration and oracle.
- `audio-power-spectral-density` — BRANCH (this batch); density normalization, integrated power, Welch averaging and reference fixtures; verification pending.
- `audio-rms-crest-factor` — BRANCH (this batch); sample RMS, mean square, sample crest and silence/channel reference fixtures; verification pending.
- **Outstanding: 68 candidates**, including at least the following nine-family backlog.

### Foundation and numerical DSP (7 pending)

`audio-sample-formats`, `audio-timebase-sync`, `audio-resampling`, `audio-channel-mapping`, `audio-filter-design`, `audio-stream-buffering`, `audio-numerical-stability`.

### Levels, loudness, and dynamics (7 pending)

`audio-vu-metering`, `audio-ppm-metering`, `audio-sample-peak`, `audio-true-peak`, `audio-program-loudness`, `audio-loudness-range`, `audio-envelope-dynamics`.

### Spectra and frequency-domain analysis (6 pending)

`audio-spectrogram-waterfall`, `audio-fractional-octave-rta`, `audio-multiresolution-spectrum`, `audio-spectral-descriptors`, `audio-harmonic-analysis`, `audio-cepstral-analysis`.

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

**Open blockers or risks:** Review the latest branch diff and CI again before merging or resuming; the cited CI pass covers a particular commit, not future edits. The simple reference DFT is O(N^2) and for small analytical fixtures only; it does not establish performance or entire-system correctness. Scope boundaries among candidate skills remain provisional. Agent-host activation is explicitly separate from committing Kestrel skill files.

**Next useful step:** After verifying CI on this batch, implement `audio-spectrogram-waterfall` with sample-accurate STFT frames, overlap, window choices, color semantics, and synthetic ridge/impulse fixtures. Then consider `audio-sample-peak`/`audio-true-peak` or `audio-dsp-test-fixtures`. Always update this same handoff, preserve actual checks/commits and recheck project priorities.

## Revisit when

At every new batch, on PR merge/rebase, when any standard or authoritative reference changes, or if fixtures reveal incorrect math. Re-read current instructions and revision rather than assuming this backlog is binding authority.
