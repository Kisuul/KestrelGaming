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
sources: "User authorized 2026-11-03 continuation of Kestrel audio curriculum while mathematics PR #3 stays separate; new audio-dsp-test-fixtures skill and reference tests at 74b4d8a5293e6e2db1782732fc76f57a5a35e065; GitHub Actions 41775340813 structural validator and 118 repository tests passed; optional SciPy differential script committed but not executed in project CI."
---

# Audio-analysis skill library — implementation handoff and running backlog

## Summary

**Goal and acceptance criteria:** Grow Kestrel's reusable, selectively loaded audio engineering skills incrementally. Each completed module needs exact Kestrel skill frontmatter, an indexed trigger, an actionable procedure with real mathematical/standards references, explicit limitations, and proportionate validation. Maintain a checkable backlog and distinguish draft guidance from executed tests and actual host integration.

**Task outcome:** PARTIAL

**Authorized scope and boundaries (historical; recheck on resume):** User explicitly requested implementation on the existing audio-skill branch, in manageable batches, with a running log in Kestrel memory. Kestrel is the skill library. Do not rewrite KESTREL.md/AGENTS.md or imply changes to external audio applications. Branch publication for PR review is intended; merging to main remains a separate decision.

**Target repository, branch, and commit (historical fixture milestone):** Kisuul/KestrelGaming; `skills/audio-dsp-core-foundation-2026-11-03`; PR #2. Fixture-bank test implementation head `74b4d8a5293e6e2db1782732fc76f57a5a35e065`, GitHub Actions `41775340813` (118 tests passed); this handoff update is a subsequent memory-only commit. Recheck live branch head and CI when resuming.

**Memory revision loaded:** PR #2 branch `7a627f72ec63248db92c5e683bb3ca695e8b60d6` with eight audio skills and the prior verified true-peak experimental module. User explicitly redirected work back to audio while independent mathematics PR #3 proceeds separately.

## Evidence

### Current milestone — merged Math core integration

The current user authorized adapting existing PR #2 to merged mathematics. Step 0
verified a clean upstream main at `c268a4d`; regular merge `78cea4e` preserved the
existing audio branch history and both catalogs. Nine audio entrypoints now link
conditionally to the relevant math procedures, keeping calibration and conventions
in audio. PSD normalization range guards, an exact doubled STFT center and four
negative/analytic tests address concrete review findings. The full local suite passed
**153 tests** on CPython 3.12.14; the live differential CLI actually imported this
checkout and passed **84 comparisons** (12 cases, seed 20261103; NumPy 2.3.5,
SciPy 1.17.0). This supersedes earlier *not run* statements for that specific CLI,
not the broader unverified application/standards/agent-behavior claims.

See the [completed integration record](2026-11-03-audio-math-integration-workorder-r01.md)
for exact starting heads, merge resolution, changed paths, commands and limits.
Published integration is `a933450ad4ae3f8a0cca8efce38a7decb4056c5f`; PR CI
[41789060842](https://github.com/Kisuul/KestrelGaming/actions/runs/41789060842)
passed structural validation and all 153 tests. A following memory-only commit records
this evidence; consult current-head CI separately. The curriculum remains
**9 developed / 64 pending**; integration adds no new skill.


**Confirmed observations with sources:** PR #2 remains open on the existing audio skill branch. Commit `d76a2780f49ecf262dc9d41e72eb230036446d2d` added distinct `audio-sample-peak` technical guidance, per-channel rolling/program peak reference code, and analytical fixtures. GitHub Actions run `41762257230` passed Kestrel structural checks and **84 repository tests**, including 12 new sample-peak tests. This is evidence for mathematical reference behavior and indexing, not target-app accuracy, clipping diagnosis or true-peak conformance.

**Hypotheses and assumptions:** Nine families of candidate audio skills form a useful *provisional taxonomy*, not an unchangeable mandate. Nine of 73 candidate skills are developed on PR #2; 64 remain proposed. Some remaining candidates may be renamed, combined, split or retired after research. Reference fixtures do not prove production integration, acoustic calibration, realtime performance or standard compliance.

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

**Persistence:** Nine audio skills, their procedures, reference material, tests and this persistent indexed handoff are saved in the existing PR #2 branch. The new sample-peak implementation is `d76a2780f49ecf262dc9d41e72eb230036446d2d`, and this evidence correction is a following memory-only commit. Nothing is integrated into `main` until PR #2 is merged.

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

### New audio-true-peak module — verified experimental reference

The next authorized curriculum increment adds `audio-true-peak`: a bounded
experimental finite-buffer Lanczos-windowed sinc estimator, specification
references, and numerical fixtures. The oracle reports sample peaks, global
zero-extended oversampled-grid peaks, separately supported interior peaks,
and exact integer subsample positions. **It does not implement Annex 2's
example four-phase FIR and must not be described as a compliant dBTP meter.**
Full application/device integration, true-peak conformance and dynamic
cross-library comparisons are still outstanding. GitHub Actions run
`41768969111` on `9bf8ac2f017b8d740c9285f19522eda65e8abba1`
passed structural checks and the full **106-test** suite (11 new true-peak
fixture tests). This validates limited analytic reference behavior only.

### Latest batch — reusable DSP test fixtures (verified)

**User authorization:** Resume the audio curriculum on existing PR #2; leave
mathematics PR #3 to its separate team. No crossover code or integration edits.

**Scope:** `skills/audio-dsp-test-fixtures/` with a focused `SKILL.md`,
`references/FIXTURE_CONTRACT.md`, optional agent metadata,
`scripts/fixture_bank.py` deterministic generator,
`scripts/check_scipy_differential.py` optional live SciPy comparison tool,
and `tests/test_audio_dsp_fixture_bank.py`. Registered centrally in
`skills/INDEX.md`.

**Actual evidence:** The first commit `e6780f1` created the skill and
generator; intermediate CI failed because its references pointed to a test
file not yet present. The follow-up implementation commit
`74b4d8a5293e6e2db1782732fc76f57a5a35e065` added that test file and
the differential tool. GitHub Actions run `41775340813` passed Kestrel
structural checks plus **118 repository tests, OK** (12 additional fixture
tests). The fixture generator was also exercised in a local basic smoke
test. No external DSP application was modified.

**Important limits:** Standard CI runs only stdlib tests. The optional live
SciPy/NumPy differential script is present but **has not been run on this
repository implementation**; frozen external SciPy golden fixtures from
the prior audit are still exercised by standard CI. Do not claim measured
real-time, instrument, device or standards correctness.

**Audio curriculum tally:** 9 developed / 73 candidates, 64 pending.
Mathematics PR #3 is independent and was not modified.

## Running backlog

**Status key:** `BRANCH` = committed to review branch (not necessarily merged); `PENDING` = not yet implemented; `PLANNED` = scope subject to review.

**Current developed skills (9 of 73 candidates total, including the existing foundation):**

- `audio-dsp-core` — BRANCH; central signal path and measurement contracts; earlier batch, PR #2.
- `audio-window-functions` — BRANCH (this batch); periodic/symmetric windows, calibration and ENBW.
- `audio-fft-spectrum` — BRANCH (this batch); amplitude DFT, one-sided bins, calibration and oracle.
- `audio-power-spectral-density` — BRANCH (this batch); density normalization, integrated power, Welch averaging and reference fixtures; CI tests passed for `a18c90e`.
- `audio-rms-crest-factor` — BRANCH (this batch); sample RMS, mean square, sample crest and silence/channel reference fixtures; CI tests passed for `a18c90e`.
- `audio-spectrogram-waterfall` — BRANCH (this batch); STFT sample-time frames, calibrated PSD/amplitude histories and visualization integrity; GitHub Actions `41759127730` passed on `5db1972`.
- `audio-sample-peak` — BRANCH (this batch); sample maxima, earliest tie, per-channel program/rolling peak, exact hold expiry and threshold semantics; CI `41762257230` passed on `d76a278`.
- `audio-true-peak` — BRANCH (this batch); **experimental** zero-extended Lanczos reference, distinct sample/intersample and interior/edge peaks, analytic timing fixtures. Not BS.1770 conformant; CI `41768969111` passed on `9bf8ac2` (106 repository tests).
- `audio-dsp-test-fixtures` — BRANCH (this batch); deterministic bounded PCM generation with sample/channel metadata, uint32-seeded noise, callback partitions, 12 analytic/metamorphic regression tests, optional SciPy differential CLI. GitHub Actions `41775340813` passed 118 tests at `74b4d8a`.
- **Outstanding: 64 candidates**, including at least the following nine-family backlog.

### Foundation and numerical DSP (7 pending)

`audio-sample-formats`, `audio-timebase-sync`, `audio-resampling`, `audio-channel-mapping`, `audio-filter-design`, `audio-stream-buffering`, `audio-numerical-stability`.

### Levels, loudness, and dynamics (5 pending)

`audio-vu-metering`, `audio-ppm-metering`, `audio-program-loudness`, `audio-loudness-range`, `audio-envelope-dynamics`.

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

### Validation, visualization, and infrastructure (7 pending)

`audio-reference-validation`, `audio-measurement-uncertainty`, `audio-visualization-integrity`, `audio-color-scale-design`, `audio-realtime-integration`, `audio-offline-analysis`, `audio-analysis-provenance`.

## Next action

Review the completed math integration on PR #2 against its current head and CI; do
not merge without owner direction. Source changes and live differential evidence are
recorded in the completed integration handoff. The optional comparator is still not
part of dependency-free CI. Production/device/GUI integration, runtime activation,
realtime behavior, physical calibration and ITU/AES conformance remain unverified.

For a later authorized curriculum batch, `audio-timebase-sync` remains a candidate;
use the merged dimensional/numerical/verification procedures where needed. The
backlog stays at 64 pending candidates, and no efficacy claim follows from math links.

## Revisit when

At every new batch, on PR merge/rebase, when any standard or authoritative reference changes, or if fixtures reveal incorrect math. Re-read current instructions and revision rather than assuming this backlog is binding authority.
