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
sources: "User request of 2026-11-03 to implement the Kestrel audio skills incrementally and maintain a running log; branch skills/audio-dsp-core-foundation-2026-11-03 at 00de8633c83e6bf1103f624b5ac513387e40e96b; SciPy documentation for window and FFT conventions; seven local Python regression fixtures executed 2026-11-03."
---

# Audio-analysis skill library — implementation handoff and running backlog

## Summary

**Goal and acceptance criteria:** Grow Kestrel's reusable, selectively loaded audio engineering skills incrementally. Each completed module needs exact Kestrel skill frontmatter, an indexed trigger, an actionable procedure with real mathematical/standards references, explicit limitations, and proportionate validation. Maintain a checkable backlog and distinguish draft guidance from executed tests and actual host integration.

**Task outcome:** PARTIAL

**Authorized scope and boundaries (historical; recheck on resume):** User explicitly requested implementation on the existing audio-skill branch, in manageable batches, with a running log in Kestrel memory. Kestrel is the skill library. Do not rewrite KESTREL.md/AGENTS.md or imply changes to external audio applications. Branch publication for PR review is intended; merging to main remains a separate decision.

**Target repository, branch, and commit:** Kisuul/KestrelGaming; `skills/audio-dsp-core-foundation-2026-11-03`. Starting head `00de8633c83e6bf1103f624b5ac513387e40e96b`; inspect Git history/PR #2 for newest commit after this handoff was written.

**Memory revision loaded:** `00de8633c83e6bf1103f624b5ac513387e40e96b`, including memory protocol, state protocol, project profile, skill index, and original DSP-core skill.

## Evidence

**Confirmed observations with sources:** Original branch contains `audio-dsp-core` and PR #2. Prior PR CI passed. This batch adds `audio-window-functions` and `audio-fft-spectrum`, reference documents, a deliberately slow Python DFT oracle, and unit tests. Seven isolated numerical tests were run in a local Python environment and passed; GitHub CI and final branch comparison must be checked after publishing this batch.

**Hypotheses and assumptions:** Nine families with eight candidate skills each (72 additions) form a useful *candidate taxonomy*, not an accepted mandatory scope. Two are developed in this batch; some remaining candidates may be renamed, combined, split, or retired after research. A successful mathematical fixture is not proof of production integration, acoustic calibration, realtime performance, or formal standard compliance.

**Decisions and rationale:** Start with shared FFT/window calibration because multiple later skills depend on exact definitions. Keep the skill library centralized and selectively loaded. Include executable pure-stdlib reference checks rather than depending on a production DSP implementation as its own oracle.

**Changed files and uncommitted state to preserve:** `skills/INDEX.md`; both new skill directories and their references/host metadata; `skills/audio-fft-spectrum/scripts/reference_dft.py`; `tests/test_audio_fft_reference.py`; this handoff; project memory index. All intended for the existing PR branch; no application repository changes.

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| `python -m unittest -v test_audio_fft_reference.py` | 7 tests passed | Local isolated copy of reference script and tests; check GitHub CI on committed versions |
| `python -m py_compile reference_dft.py test_audio_fft_reference.py` | Passed | Local isolated copy |
| Kestrel structural validator and full regression suite | Not yet run for this new batch at handoff authoring | Inspect PR workflow; do not infer success |
| DSP instrument compliance | Not assessed | No normative conformance claim |

**Persistence:** This handoff and skills are proposed in branch PR #2; confirm remote branch commit after writing. This is **not** integrated into `main`.

## Running backlog

**Status key:** `BRANCH` = committed to review branch (not necessarily merged); `PENDING` = not yet implemented; `PLANNED` = scope subject to review.

**Current developed skills (3 of 73 candidates total, including the existing foundation):**

- `audio-dsp-core` — BRANCH; central signal path and measurement contracts; earlier batch, PR #2.
- `audio-window-functions` — BRANCH (this batch); periodic/symmetric windows, calibration and ENBW.
- `audio-fft-spectrum` — BRANCH (this batch); amplitude DFT, one-sided bins, calibration and oracle.
- **Outstanding: 70 candidates**, including at least the following nine-family backlog.

### Foundation and numerical DSP (7 pending)

`audio-sample-formats`, `audio-timebase-sync`, `audio-resampling`, `audio-channel-mapping`, `audio-filter-design`, `audio-stream-buffering`, `audio-numerical-stability`.

### Levels, loudness, and dynamics (8 pending)

`audio-vu-metering`, `audio-ppm-metering`, `audio-sample-peak`, `audio-true-peak`, `audio-rms-crest-factor`, `audio-program-loudness`, `audio-loudness-range`, `audio-envelope-dynamics`.

### Spectra and frequency-domain analysis (7 pending)

`audio-power-spectral-density`, `audio-spectrogram-waterfall`, `audio-fractional-octave-rta`, `audio-multiresolution-spectrum`, `audio-spectral-descriptors`, `audio-harmonic-analysis`, `audio-cepstral-analysis`.

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

**Open blockers or risks:** Check the published branch, PR diff, and GitHub CI on the new batch. The simple reference DFT is O(N^2) and for small analytical fixtures only; it does not establish performance or entire-system correctness. Scope boundaries among candidate skills remain provisional. Agent-host activation is explicitly separate from committing Kestrel skill files.

**Next useful step:** Implement `audio-power-spectral-density` next (separate power normalization and Welch averaging, with independent noise/Parseval checks); then `audio-sample-peak` / `audio-rms-crest-factor` or `audio-spectrogram-waterfall`. Update this *same* handoff record and project index after each meaningful batch, preserving actual commit IDs and checks. Check for user priorities at the next conversation if their direction has changed.

## Revisit when

At every new batch, on PR merge/rebase, when any standard or authoritative reference changes, or if fixtures reveal incorrect math. Re-read current instructions and revision rather than assuming this backlog is binding authority.
