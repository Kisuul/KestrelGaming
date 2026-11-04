---
schema: 1
id: 2026-11-03-audio-skills-roadmap
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: ChatGPT
created: 2026-11-03
updated: 2026-11-04
sources: "User 2026-11-04 authorized audio-resampling implementation with careful independent verification and project memory update; commit a388abdbb54ec601ed80b943ec33c3be8f5b6511 passed GitHub Actions 41800254484 with 211 tests and structural checks; local Python 3.13.5 NumPy 2.3.5 SciPy 1.17.0 independent differential passed 3669 samples across 24 seeded cases; SciPy resample_poly and upfirdn documentation."
---

# Audio-analysis skill library — implementation handoff and running backlog

## Summary

**Goal and acceptance criteria:** Grow Kestrel's reusable, selectively loaded audio engineering skills incrementally. Each completed module needs exact Kestrel skill frontmatter, an indexed trigger, an actionable procedure with real mathematical/standards references, explicit limitations, and proportionate validation. Maintain a checkable backlog and distinguish draft guidance from executed tests and actual host integration.

**Task outcome:** PARTIAL

**Authorized scope and boundaries (historical; recheck on resume):** User explicitly requested implementation on the existing audio-skill branch, in manageable batches, with a running log in Kestrel memory. Kestrel is the skill library. Do not rewrite KESTREL.md/AGENTS.md or imply changes to external audio applications. Branch publication for PR review is intended; merging to main remains a separate decision.

**Target repository, branch, and commit:** Kisuul/KestrelGaming, `skills/audio-dsp-core-foundation-2026-11-03`, open PR #2. `audio-resampling` implementation head `a388abdbb54ec601ed80b943ec33c3be8f5b6511` passed GitHub Actions `41800254484` (211 repository tests and structural checks). This follow-up is a memory-only evidence commit: verify its own CI when available and recheck live branch head on pickup.

**Memory revision loaded:** PR #2 branch `3d1708c01facfcbe35e83c4619740221a55b42fb` with eleven indexed audio skills, merged Math foundation integration and 189 passing repository tests. User explicitly authorized a carefully verified twelfth audio module, while preserving Kestrel's persistent memory.

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
this evidence; consult current-head CI separately. That math-integration milestone preserved **9 developed / 64 pending**; the subsequent verified timebase module reached **10 developed / 63 pending**, and the new PCM milestone brings the current tally to **11 developed / 62 pending**.


**Confirmed observations with sources:** PR #2 remains open on the existing audio skill branch. Commit `d76a2780f49ecf262dc9d41e72eb230036446d2d` added distinct `audio-sample-peak` technical guidance, per-channel rolling/program peak reference code, and analytical fixtures. GitHub Actions run `41762257230` passed Kestrel structural checks and **84 repository tests**, including 12 new sample-peak tests. This is evidence for mathematical reference behavior and indexing, not target-app accuracy, clipping diagnosis or true-peak conformance.

**Hypotheses and assumptions:** Nine families of candidate audio skills form a useful *provisional taxonomy*, not an unchangeable mandate. Twelve of 73 candidate skills are developed on PR #2; 61 remain proposed. Some remaining candidates may be renamed, combined, split or retired after research. Reference fixtures do not prove production integration, acoustic calibration, realtime performance or standard compliance.

**Decisions and rationale:** Keep Kestrel skills central, individually discoverable, with executable pure-stdlib small-fixture oracles. Prior spectrogram oracle uses left-aligned, complete, unpadded frames and explicitly defined sample-clock coordinates. The new sample-peak skill separates current-block maxima, maximum-since-reset, and rolling maximum over the last H actual samples, with earliest-tie index, per-channel isolation and explicit reference hit/exceedance counts. Clipping diagnosis and ITU true peak deliberately remain distinct.

**Changed files and uncommitted state to preserve:** The new bounded SRC increment added `skills/audio-resampling/SKILL.md`, `references/RESAMPLING_CONTRACT.md`, optional `agents/openai.yaml`, `scripts/reference_resampling.py`, optional `scripts/check_scipy_resampling.py`, `tests/test_audio_resampling_reference.py`, frozen `tests/fixtures/AUDIO_RESAMPLING_EXTERNAL_GOLDENS.md`, an indexed entry, and this existing handoff update. No audio application, Kestrel governing contract, Math skill implementation, workflows or dependencies were changed.

| Command or check actually performed | Observed result | Environment / limits |
| --- | --- | --- |
| `python -m unittest -v test_audio_fft_reference.py` | 7 tests passed | Local isolated copy of reference script and tests; check GitHub CI on committed versions |
| `python -m py_compile reference_dft.py test_audio_fft_reference.py` | Passed | Local isolated copy |
| Kestrel structural validator and full regression suite | Both GitHub Actions steps passed in run `41756464057` | Commit `035cb2b03d7cfdb84b8690f1d5ef0be3c6d5148a`; no production analyzer exercised |
| New PSD and RMS deterministic reference tests | GitHub CI run `41757356509` passed; full suite ran 60 tests, OK | Against `a18c90e1ff416ba085a9b2272fcb2f513a7f0885`; not a production DSP or instrument test |
| Spectrogram STFT and waterfall fixtures | GitHub Actions run `41759127730`: structural checks passed and 72 tests, OK | Commit `5db19722d453c2447c015ecc85fcc795a11161ad`; only mathematical/reference fixtures; no GUI visual regression, gap detector or production latency measured |
| Sample-peak reference fixtures and peak-hold behavior | GitHub Actions run `41762257230`: Kestrel structural checks passed; 84 repository tests, OK (12 new sample-peak tests) | Implementation commit `d76a2780f49ecf262dc9d41e72eb230036446d2d`; no production/app/true-peak validation performed |
| Audit remediation and independent library golden tests | GitHub Actions `41767618425`, implementation head `c786a713d97c6983e36aeb0692823a61d1978243`: 95 tests passed, structural checks passed | Frozen SciPy/NumPy vectors generated outside Kestrel and committed; no dynamic SciPy CI, host integration or formal instrument compliance |
| Audio timebase rational-clock/epoch reference | GitHub Actions `41792085786`: structural validator passed and 170 tests, including 17 new timebase tests | `1927b4d0d82ec8687c0578eadc77413ebdb71435`; no physical-device or UI clock verification |
| Raw PCM byte conversion / valid-bit alignment and quantization | GitHub Actions run `41794191643`: structural validation passed; 189 total repository tests including 19 new PCM tests | Implementation `f7a95a4cd9342be2bb6fdb5746d2ab71bc67557d`; no full file parser, codec, real-time or instrument testing |
| DSP instrument compliance | Not assessed | No normative conformance claim |

**Persistence:** Twelve developed audio skills, their references, tests, source provenance and this active indexed handoff are committed to open PR #2. The new resampling implementation and frozen-golden commit is `a388abdbb54ec601ed80b943ec33c3be8f5b6511`, with 211 passing tests on GitHub Actions `41800254484`. Nothing is in `main` until PR #2 is merged.

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

### New increment — audio timebase and epoch integrity (verified reference)

**Authorization:** The owner requested that we continue writing audio skills and
check/update Kestrel project memory. Scope is PR #2's existing review branch;
the merged mathematics core is reused conditionally. PR #3 and applications
remain untouched.

**Changed this batch:** `skills/audio-timebase-sync/SKILL.md`,
`references/TIMEBASE_CONTRACT.md`, `agents/openai.yaml`, and
`scripts/reference_timebase.py`, plus
`tests/test_audio_timebase_reference.py`, `skills/INDEX.md`,
and this existing indexed roadmap. The simple reference uses exact integer
sample origins and `fractions.Fraction` frame times, finite-rate rational
conversion, explicit epoch resets and atomic discontinuity rejection.
Timestamp anchors are explicitly **nominal mappings, not hardware timing
calibration, jitter or latency evidence**. It does not alter Kestrel Math
implementations or any audio application.

**Authoritative context:** W3C Web Audio API `getOutputTimestamp()` clock
correlation, PortAudio input ADC/callback/output DAC timing guidance, and
FFmpeg time-base semantics. Implementation commit `0dd28fc` passed 169
repository tests in CI `41791939201`; follow-up `1927b4d` prevents
reusing a non-consecutive historical epoch identifier and adds an adversarial
regression. CI `41792085786` passed the structural validator and **170 tests**.
The new script remains a small pure-stdlib oracle, not a calibrated device
sync/clock-recovery system, streaming resampler, measured jitter model, or
host/UI integration. Initial 9/73 program count advanced to **10/73**;
**63 candidates remain**.

**Curriculum at prior timebase milestone:** 10 developed / 73 candidate audio skills, 63 then pending; the following PCM milestone advances to **11 developed / 62 pending**.

### Latest batch — audio PCM sample format integrity (verified)

The owner requested another audio skill and cautioned against weakening
engineering rigor. Existing PR #2 remained open; the merged mathematics
department stays unchanged. A dedicated `audio-sample-formats` module
now establishes **WAVE-style u8/s16/s24/s32 and IEEE f32/f64 raw sample**
conventions, explicit endian/planar/interleaved channel layout, integer
normalization/valid-bit container distinctions, float samples beyond ±1,
ties-to-even quantization, per-channel code saturation, and strict invalid
buffer rejection. It cross-links generic Math numerical analysis only when
needed, leaving PCM semantics owned by audio.

**New scope:** `skills/audio-sample-formats/SKILL.md`, its
`references/PCM_FORMAT_CONTRACT.md`, optional `agents/openai.yaml`,
`scripts/reference_pcm.py`, `tests/test_audio_sample_formats_reference.py`,
central `skills/INDEX.md`, and this same project handoff.

**Observed evidence:** Initial reference-code/test commit
`f9224b4cf89cbc5d4e840dca5577992b0acf9c6a` did not yet contain
its skill documentation, and that intermediate CI was not a completion
gate. During review a handwritten 20-valid-bit-in-24 PCM hex test
fixture was corrected in `f7a95a4cd9342be2bb6fdb5746d2ab71bc67557d`.
GitHub Actions run `41794191643` at that head **passed structural
validation and all 189 repository tests**, compared with the preceding
170-test baseline. New tests cover known raw byte values, independent
Python `struct`/`wave` checks, exact PCM endpoints and layouts,
strict padding validation, negative failures, and float headroom.

**Limitations:** Reference samples are bounded and processed offline;
the code does *not* parse WAVE/RF64/AIFF container metadata, map channel
masks, apply dithering/noise-shaping, validate resamplers, profile realtime
performance, check physical audio devices, or certify standards-level
measurement. Explicit normalization policy is not interchangeable with
other libraries' default conversions.

**Current curriculum:** **11 developed of 73; 62 pending**.

### Latest milestone — audio resampling (verified bounded reference)

**Authorized scope:** Build the next audio curriculum module, `audio-resampling`,
on the existing open PR #2 branch; reuse relevant Math procedures without changing
the mathematics department, application repositories or Kestrel agent contract.

**Implementation and decisions:** A 256-frame-bounded standard-library
reference uses an exact reduced destination/source rate L/M, centered
Kaiser-windowed sinc FIR (beta 5, half-length 10 max(L,M) in intermediate
samples), explicit finite zero extension, rational integer-clock output
mapping, linear-phase group-delay metadata, per-output boundary flags and
per-epoch output origins. Its `StreamResampler` withholds incomplete
noncausal outputs until future source samples arrive. An explicit finalize
authorizes end-of-record extension; gaps, overlaps, malformed channels,
nonfinite input and overflow reject without changing accepted state.
Stream resets require never-reused epoch IDs. Processing is offline and
**not realtime-optimized**, clock-adaptive or a file decoder.

**Actual verification:**
- Local Python 3.13.5 test run exercised **22** new analytic, metamorphic,
  boundary, noise/anti-alias, timebase, negative and frozen-golden tests.
  An initially incorrect chunk-dependent boundary flag and overstrict
  ideal-unit-impulse expectation were caught and corrected before publication.
- SciPy 1.17.0 / NumPy 2.3.5 separately generated frozen numerical references
  for 2:3, 3:2, 147:160 and 160:147 ratios. The new optional
  `scripts/check_scipy_resampling.py --seed 20261104 --cases 24`
  passed **3,669 sample comparisons** locally. SciPy shares the
  *intended* Kaiser/sinc design family but uses a different convolution
  implementation; this checks numerics and alignment, not optimum
  filter quality or independent theory.
- GitHub Actions [41800254484](https://github.com/Kisuul/KestrelGaming/actions/runs/41800254484)
  passed Kestrel structural validation and the complete **211-test**
  standard-library suite on `a388abdbb54ec601ed80b943ec33c3be8f5b6511`.
  Optional SciPy dependencies were **not added** to ordinary CI.

**Limits:** No measured end-to-end device sync, production streaming
latency/CPU, full stopband sweep, perceptual quality, asynchronous drift
compensation, arbitrary codecs/PCM quantization or normative instrument
conformance. Test bands/thresholds are fixture-specific heuristics;
the filter retains all source frames per bounded epoch.

**Current curriculum:** **12 developed / 73 candidates, 61 pending**.

## Running backlog

**Status key:** `BRANCH` = committed to review branch (not necessarily merged); `PENDING` = not yet implemented; `PLANNED` = scope subject to review.

**Current developed skills (12 of 73 candidates total, including the existing foundation):**

- `audio-dsp-core` — BRANCH; central signal path and measurement contracts; earlier batch, PR #2.
- `audio-window-functions` — BRANCH (this batch); periodic/symmetric windows, calibration and ENBW.
- `audio-fft-spectrum` — BRANCH (this batch); amplitude DFT, one-sided bins, calibration and oracle.
- `audio-power-spectral-density` — BRANCH (this batch); density normalization, integrated power, Welch averaging and reference fixtures; CI tests passed for `a18c90e`.
- `audio-rms-crest-factor` — BRANCH (this batch); sample RMS, mean square, sample crest and silence/channel reference fixtures; CI tests passed for `a18c90e`.
- `audio-spectrogram-waterfall` — BRANCH (this batch); STFT sample-time frames, calibrated PSD/amplitude histories and visualization integrity; GitHub Actions `41759127730` passed on `5db1972`.
- `audio-sample-peak` — BRANCH (this batch); sample maxima, earliest tie, per-channel program/rolling peak, exact hold expiry and threshold semantics; CI `41762257230` passed on `d76a278`.
- `audio-true-peak` — BRANCH (this batch); **experimental** zero-extended Lanczos reference, distinct sample/intersample and interior/edge peaks, analytic timing fixtures. Not BS.1770 conformant; CI `41768969111` passed on `9bf8ac2` (106 repository tests).
- `audio-dsp-test-fixtures` — BRANCH (this batch); deterministic bounded PCM generation with sample/channel metadata, uint32-seeded noise, callback partitions, 12 analytic/metamorphic regression tests, optional SciPy differential CLI. GitHub Actions `41775340813` passed 118 tests at `74b4d8a`.
- `audio-timebase-sync` — BRANCH; exact integer/rational sample time, gap/overlap rejection, immutable clock anchors, no historical epoch ID reuse and sample-rate conversion. **17 new tests**; GitHub Actions `41792085786` passed structural checks and the full **170-test** suite on `1927b4d0`.
- `audio-sample-formats` — BRANCH; u8/s16/s24/s32/f32/f64 raw PCM byte-order/layout/valid-bit rules, quantization and float headroom; **19 new regression tests**, full CI **189 tests** on `f7a95a4`, run `41794191643`.
- `audio-resampling` — BRANCH; bounded Kaiser-windowed FIR resampler, exact Fraction sample clocks, antialias/phase/delay, stable streaming with explicit finalize/epochs, 22 focused tests and independently generated SciPy golden vectors; CI `41800254484` passed **211** tests at `a388abd`, with optional local SciPy differential 3669 samples / 24 cases.
- **Outstanding: 61 candidates**, including at least the following nine-family backlog.

### Foundation and numerical DSP (4 pending)

`audio-channel-mapping`, `audio-filter-design`, `audio-stream-buffering`, `audio-numerical-stability`.

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

Confirm the final memory-only commit's GitHub Actions run and current PR #2
diff. Keep PR #2 open for owner review; do not merge without owner
authorization. The new resampling reference is intentionally bounded
and **not** a production audio backend.

**Recommended next bounded module:** `audio-channel-mapping` for explicit
channel identity, layout masks, downmix/upmix policy, stereo/antiphase
handling and independently checked sample/channel transforms. Alternatively,
`audio-filter-design` can build on the resampling FIR concepts, but must
earn its own frequency-response and numerical acceptance checks.
Preserve the **61 pending** candidate audio skills and reuse mathematics
skills only for genuinely shared quantitative foundations.

## Revisit when

At every new batch, on PR merge/rebase, when any standard or authoritative reference changes, or if fixtures reveal incorrect math. Re-read current instructions and revision rather than assuming this backlog is binding authority.
