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
sources: "User authorized 2026-11-03 audit remediation of the Kestrel audio skills; branch implementation through c786a713d97c6983e36aeb0692823a61d1978243; GitHub Actions run 41767618425 passed 95 repository tests and structural checks; independent SciPy 1.17.0 / NumPy 2.3.5 frozen golden vectors."
---

# Audio-analysis skill library — implementation handoff and running backlog

## Summary

**Goal and acceptance criteria:** Grow Kestrel's reusable, selectively loaded audio engineering skills incrementally. Each completed module needs exact Kestrel skill frontmatter, an indexed trigger, an actionable procedure with real mathematical/standards references, explicit limitations, and proportionate validation. Maintain a checkable backlog and distinguish draft guidance from executed tests and actual host integration.

**Task outcome:** PARTIAL

**Authorized scope and boundaries (historical; recheck on resume):** User explicitly requested implementation on the existing audio-skill branch, in manageable batches, with a running log in Kestrel memory. Kestrel is the skill library. Do not rewrite KESTREL.md/AGENTS.md or imply changes to external audio applications. Branch publication for PR review is intended; merging to main remains a separate decision.

**Target repository, branch, and commit:** Kisuul/KestrelGaming; `skills/audio-dsp-core-foundation-2026-11-03`; PR #2. Sample-peak implementation head `d76a2780f49ecf262dc9d41e72eb230036446d2d` was verified in workflow `41762257230`. This updated handoff is a subsequent memory-only commit; check the live head and CI on resuming.

**Memory revision loaded:** Audit remediation resumed from PR #2 at `51a27e3d94202b01bf58e52b1541b9849bc81bcc`, using the indexed project handoff and independent review r01; user explicitly authorized this correction batch.

## Evidence

**Confirmed observations with sources:** PR #2 remains open on the existing audio skill branch. Commit `d76a2780f49ecf262dc9d41e72eb230036446d2d` added distinct `audio-sample-peak` technical guidance, per-channel rolling/program peak reference code, and analytical fixtures. GitHub Actions run `41762257230` passed Kestrel structural checks and **84 repository tests**, including 12 new sample-peak tests. This is evidence for mathematical reference behavior and indexing, not target-app accuracy, clipping diagnosis or true-peak conformance.

**Hypotheses and assumptions:** Nine families of candidate audio skills form a useful *provisional taxonomy*, not an unchangeable mandate. Seven of 73 candidate skills are now developed on PR #2; 66 remain proposed. Some remaining candidates may be renamed, combined, split or retired after research. Reference fixtures do not prove production integration, acoustic calibration, realtime performance or standard compliance.

**Decisions and rationale:** Keep Kestrel skills central, individually discoverable, with executable pure-stdlib small-fixture oracles. Prior spectrogram oracle uses left-aligned, complete, unpadded frames and explicitly defined sample-clock coordinates. The new sample-peak skill separates current-block maxima, maximum-since-reset, and rolling maximum over the last H actual samples, with earliest-tie index, per-channel isolation and explicit reference hit/exceedance counts. Clipping diagnosis and ITU true peak deliberately remain distinct.

**Changed files and uncommitted state to preserve:** Latest audit-remediation batch changed the RMS and sample-peak reference scripts and tests, associated skill/reference guides, the FFT spectrum cross-skill trigger, and added `tests/test_audio_external_goldens.py` plus `tests/fixtures/AUDIO_EXTERNAL_GOLDENS.md`. It also updates this existing indexed audit and handoff; no target-app or governing contract files changed.

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| `python -m unittest -v test_audio_fft_reference.py` | 7 tests passed | Local isolated copy of reference script and tests; check GitHub CI on committed versions |
| `python -m py_compile reference_dft.py test_audio_fft_reference.py` | Passed | Local isolated copy |
| Kestrel structural validator and full regression suite | Both GitHub Actions steps passed in run `41756464057` | Commit `035cb2b03d7cfdb84b8690f1d5ef0be3c6d5148a`; no production analyzer exercised |
| New PSD and RMS deterministic reference tests | GitHub CI run `41757356509` passed; full suite ran 60 tests, OK | Against `a18c90e1ff416ba085a9b2272fcb2f513a7f0885`; not a production DSP or instrument test |
| Spectrogram STFT and waterfall fixtures | GitHub Actions run `41759127730`: structural checks passed and 72 tests, OK | Commit `5db19722d453c2447c015ecc85fcc795a11161ad`; only mathematical/reference fixtures; no GUI visual regression, gap detector or production latency measured |
| Sample-peak reference fixtures and peak-hold behavior | GitHub Actions run `41762257230`: Kestrel structural checks passed; 84 repository tests, OK (12 new sample-peak tests) | Implementation commit `d76a2780f49ecf262dc9d41e72eb230036446d2d`; no production/app/true-peak validation performed |
| Audit remediation and independent library golden tests | GitHub Actions `41767618425`, implementation head `c786a713d97c6983e36aeb0692823a61d1978243`: 95 tests passed, structural checks passed | Frozen SciPy/NumPy vectors generated outside Kestrel and committed; no dynamic SciPy CI, host integration or formal instrument compliance |
| DSP instrument compliance | Not assessed | No normative conformance claim |

**Persistence:** Seven audio skills, their procedures, reference material, tests and this persistent indexed handoff are saved in the existing PR #2 branch. The new sample-peak implementation is `d76a2780f49ecf262dc9d41e72eb230036446d2d`, and this evidence correction is a following memory-only commit. Nothing is integrated into `main` until PR #2 is merged.

### Latest milestone: audit remediation verified

**User authorization:** `Have at it` following the independent hostile audit;
same existing review branch, no `main` merge.

**Fixes (verified at `c786a713d97c6983e36aeb0692823a61d1978243`):**
finite log-domain dB calculations, scaled RMS and explicit binary64
underflow flags, sample-peak long-block/short-hold guidance and fixtures,
existing PSD skill cross-link, document-specific AES17-2020 preview, and
five externally generated SciPy/NumPy golden test scenarios. GitHub
Actions `41767618425` ran **95 tests, OK**, and structural checks passed.
Original preceding head had 84 tests.

See [independent audio skills audit r01 and r02 findings](../2026-11-03-audio-skills-independent-audit.md)
for exact revisions, resolved findings and untested limitations.

**Skill tally unchanged:** 7 developed / 66 candidates pending.
The audit remediation improved existing modules; it did not create a
new audio skill. No production DSP, dynamic external-library CI or
formal BS.1770 instrument validation was performed.

## Running backlog

**Status key:** `BRANCH` = committed to review branch (not necessarily merged); `PENDING` = not yet implemented; `PLANNED` = scope subject to review.

**Current developed skills (7 of 73 candidates total, including the existing foundation):**

- `audio-dsp-core` — BRANCH; central signal path and measurement contracts; earlier batch, PR #2.
- `audio-window-functions` — BRANCH (this batch); periodic/symmetric windows, calibration and ENBW.
- `audio-fft-spectrum` — BRANCH (this batch); amplitude DFT, one-sided bins, calibration and oracle.
- `audio-power-spectral-density` — BRANCH (this batch); density normalization, integrated power, Welch averaging and reference fixtures; CI tests passed for `a18c90e`.
- `audio-rms-crest-factor` — BRANCH (this batch); sample RMS, mean square, sample crest and silence/channel reference fixtures; CI tests passed for `a18c90e`.
- `audio-spectrogram-waterfall` — BRANCH (this batch); STFT sample-time frames, calibrated PSD/amplitude histories and visualization integrity; GitHub Actions `41759127730` passed on `5db1972`.
- `audio-sample-peak` — BRANCH (this batch); sample maxima, earliest tie, per-channel program/rolling peak, exact hold expiry and threshold semantics; CI `41762257230` passed on `d76a278`.
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

**Open blockers or risks:** Revalidate newest branch/CI before resuming or merging; `41767618425` covers implementation head `c786a71`, not this memory-only evidence commit or later edits. Live SciPy differential CI, host integration and instrument conformance remain open. The reference rolling maximum is a trailing sample-count window, not a display envelope with separate release ballistics; threshold hits do not prove recorded clipping. No visual meter integration, oversampled true-peak test, hardware calibration or realtime performance profiling has been done. The reference is O(frames*M*Nfft) and supports complete left-aligned frames but not gap detection, GPU rendering, live reconfiguration or app-level visual regression. Actual target-app integration, sound-level calibration and production timing remain untested. No calibration, real-time benchmarking, third-party instrument comparison, or end-to-end host activation has been performed. The simple reference DFT is O(N^2) and for small analytical fixtures only; it does not establish performance or entire-system correctness. Scope boundaries among candidate skills remain provisional. Agent-host activation is explicitly separate from committing Kestrel skill files.

**Next useful step:** The bounded audit remediation is verified on the implementation commit. Continue with `audio-true-peak`, first investigating ITU-R BS.1770-5, the oversampling/reconstruction and latency/filter tradeoffs, and independent test vectors; mark an initial estimator experimental until conformance evidence exists. Separately extend the five pinned external goldens into optional dynamic SciPy differential/property tests. Preserve all 66 pending candidate skills and update this handoff at each verified milestone.

## Revisit when

At every new batch, on PR merge/rebase, when any standard or authoritative reference changes, or if fixtures reveal incorrect math. Re-read current instructions and revision rather than assuming this backlog is binding authority.
