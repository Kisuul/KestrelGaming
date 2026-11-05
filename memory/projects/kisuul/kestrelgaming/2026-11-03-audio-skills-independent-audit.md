---
schema: 1
id: 2026-11-03-audio-skills-independent-audit-r01
kind: lesson
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: ChatGPT
created: 2026-11-03
updated: 2026-11-03
sources: "PR #2 hostile audit at a0901b1cd9a01e118c5f9270e82424bdd155a214; audit record 51a27e3d94202b01bf58e52b1541b9849bc81bcc; remediation commits 6d635acf6e81c32015a837768cb5f65e0f7b504e, 32f7b05ea4bbd2392ea5dad381d778ff40d6ee44, 15d3eec49dd367cd634eec387bd9ede1fb5ff7b1, c786a713d97c6983e36aeb0692823a61d1978243; CI 41767618425 passed 95 tests, structural checks."
---

# Independent audit of the seven audio-analysis skills (review r01)

## Summary

**Later evidence:** The [completed Math core integration](handoffs/2026-11-03-audio-math-integration-workorder-r01.md)
records an actual live SciPy comparison against the repository implementations:
84 comparisons passed with seed 20261103, 12 cases, NumPy 2.3.5/SciPy 1.17.0.
Earlier *not run* statements below describe earlier revisions. This closes that
bounded execution gap, not production, host, realtime or normative conformance.

**Review status:** FOCUSED REMEDIATION VERIFIED on the PR branch as of `c786a71`. The initial findings remain below as historical evidence; remaining gaps are full dynamic differential testing, application/host integration, realtime behavior and normative instrument validation. The original inspection found no high-severity error in ordinary-range FFT/PSD/level formulas.

Reviewed PR #2 at `a0901b1cd9a01e118c5f9270e82424bdd155a214`, with 7 implemented audio skills of a 73-candidate taxonomy (66 candidates remain). This is a read/review of current feature branch source, not a claim of instrument certification, host integration, or review of uncommitted local changes. No application or DSP implementation has been changed by this review.

This record stores findings independently of the [running curriculum handoff](handoffs/2026-11-03-audio-skills-roadmap.md). Read them together on resume.

## Evidence

### Confirmed strengths

- Kestrel skills have focused activation conditions and explicit distinction between sample-peak, true-peak, RMS, amplitude FFT, PSD and UI presentation; mathematical/reference claims are appropriately qualified in core guides.
- CI [workflow 41762386365](https://github.com/Kisuul/KestrelGaming/actions/runs/41762386365) passed structural checks and 84 unit tests on branch head `a0901b1`. The five audio test files have 48 test methods; the 84 also include unrelated Kestrel tests. Passing proves only the covered cases.
- Independently reconstructed one-sided PSD normalization from `skills/audio-power-spectral-density/scripts/reference_psd.py` and compared against `scipy.signal.periodogram` for both rectangular and periodic Hann windows, frame lengths 63/64/127, Nfft 63/64/256, seeded random data, no detrending. Eight comparisons matched to around 1.1e-19 absolute PSD ordinate difference or less; integrated spectral energy matched windowed mean-square to ~3.4e-16. This comparison checked the **formula**, not an imported/clone-executed copy of the private repository script.
- Relevant SciPy references: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.periodogram.html and https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.fft_mode.html.

### Findings to address

| Severity | Finding and source | Why it matters / follow-up |
| --- | --- | --- |
| Moderate verification gap | `tests/test_audio_*.py` primarily test each reference oracle against analytic fixtures. No cross-library SciPy comparison, property-based random/stress cases, or browser/host integration gate is in `.github/workflows/validate.yml`. | Extend tests with independently computed fixtures, optional SciPy differential comparisons in a dedicated environment, and application-level integration trials before relying on measurement claims. Do not imply the existing green suite proves conformity. |
| Low numeric correctness bug (extreme finite inputs) | `skills/audio-rms-crest-factor/scripts/reference_levels.py` and `skills/audio-sample-peak/scripts/reference_peak.py` compute dB as `20*log10(amplitude/reference)`. For amplitude `1e-300` and reference `1e300`, finite positive inputs yield an underflowed zero ratio and `ValueError`; reversing inputs yields infinity instead of the finite expected +12000 dB. | Use `20*(log10(amplitude)-log10(reference))` after handling exact zero and checking finite positive references. Add finite-stress regression tests and inspect the DSP normalization path for analogous errors. This is far outside ordinary PCM ranges, but contracts should not silently mis-handle accepted finite values. |
| Low numeric correctness bug (extreme tiny samples) | `reference_levels.py` squares input values before summing; for four samples of `1e-200`, `x*x` underflows to zero and the reference reports RMS=0 although all samples are nonzero. | Use a scaled sum-of-squares method when wide dynamic range is required, or explicitly document a bounded supported range. Distinguish numerical zero from measured digital silence. |
| Low stale skill guidance | `skills/audio-fft-spectrum/SKILL.md`, under When to load, says `audio-power-spectral-density` is still planned, though that skill now exists and is indexed. | Replace the outdated sentence with a direct skill link and correct trigger. This is the clearest cross-module knowledge drift discovered. |
| Low Markdown discoverability defect | `memory/projects/kisuul/kestrelgaming/INDEX.md` had a blank line between the project-profile pipe-table row and the handoff row, breaking the table in Markdown renderers. | Fix index formatting as a narrow memory edit. A validator checks linked paths, not rendered Markdown layout. |
| Low source precision / reproducibility | `skills/audio-rms-crest-factor/SKILL.md` uses an AES standards-store overview URL instead of a document-specific AES17-2020 preview. `audio-sample-peak` references ITU-R BS.1770-5 (a good primary source); external URLs are not checked by Kestrel structural CI. | Replace broad AES link with the document-specific official preview URL, record standards edition and normative/access limits, and check reference links periodically. |
| Moderate integration risk, not demonstrated bug | `reference_peak.py` outputs final rolling peak at block end, while `block.peak` separately preserves brief impulses from anywhere inside a long block. A UI consuming **only rolling_peak** could miss impulses older than the trailing hold window when a callback exceeds hold size. | Add an explicit guidance/test case for long blocks and small H, and require a declared UI consumption policy. This does not invalidate the documented trailing-window calculation. |

### Verification process observations

- `.github/workflows/validate.yml` runs `python3 tools/validate_seed.py` and `python3 -m unittest discover -s tests -v`. It does not currently run `git diff --check`, although CONTRIBUTING asks contributors to run that check; the CI pass should not be represented as an executed whitespace-diff gate.
- No actual application, real audio input hardware, calibrated meters, memory retrieval exercise from a separate agent host, or FFT CPU/GPU performance benchmark was tested.
- The SciPy mathematical cross-check above is an independent one-off **audit calculation**, not a committed regression test.
- Formal ITU-R BS.1770-5 true-peak compliance was **not** examined because `audio-true-peak` is still pending.

## Remediation r02 — implemented and independently checked

**Branch:** `skills/audio-dsp-core-foundation-2026-11-03` (PR #2, still a
review branch, not `main`). **Final implementation head:**
`c786a713d97c6983e36aeb0692823a61d1978243`. GitHub Actions
[41767618425](https://github.com/Kisuul/KestrelGaming/actions/runs/41767618425)
reported **95 tests passed** plus successful structural validation. The
original audit head had 84 tests; existing tests were retained.

| Prior finding | Remediation and evidence | Status |
| --- | --- | --- |
| dB ratio underflow/overflow | `reference_levels.py` and `reference_peak.py` now compute nonzero ratios as `20*(log10(value)-log10(reference))`; tests include ±12000 dB finite extremes | Fixed and tested in CI |
| Tiny nonzero signal misreported as RMS silence | RMS uses scaled sum-of-squares. Output flags `mean_square_underflowed` when Q cannot be represented, and `rms_underflowed` when isolated subnormal samples still round to zero RMS; explicitly distinct from zero input | Fixed and tested; binary64 representation limits remain |
| Outdated PSD specialist trigger | `audio-fft-spectrum/SKILL.md` now links to the existing PSD skill | Fixed |
| AES17 link precision | RMS skill now links to [the official AES17-2020 preview](https://www.aes.org/publications/standards/preview.cfm?ID=21) | Fixed; preview does not grant full normative text |
| Short hold vs long callback | Sample-peak skill/reference now warns that final rolling peak may omit an early transient; fixture tests preserved block/program peak visibility | Addressed and tested |
| Project memory index broken table | Original audit commit fixed the blank line in the table | Fixed |
| Independent validation gap | Five pinned spectral fixture tests were generated with external **SciPy 1.17.0 / NumPy 2.3.5** and run with stdlib-only GitHub CI; inputs, source calls and golden outputs in [fixture instructions](../../../../tests/fixtures/AUDIO_EXTERNAL_GOLDENS.md) | Partially addressed |

**Unresolved verification:** CI exercises frozen *external-library goldens*, not
a live SciPy installation or randomized differential test on every push.
Standalone mathematical references are not target-app DSP integrations,
instrument calibration, true-peak conformance or realtime performance tests.
No production web visualizer has been verified by this hardening batch.

**Remediation scope:** Seven developed audio skills remain seven, with 66
candidate skills outstanding. No audio application source or governing Kestrel
contract was changed by this work.

## Recommended next action

1. Next curriculum skill: `audio-true-peak`, with explicitly specified oversampling, filter calibration, reconstruction/boundary choices and analytic vectors. Mark it **experimental** until independently evaluated for the intended BS.1770 revision; sample peak is not true peak.
2. Expand frozen external goldens into a *live* cross-library differential harness, with random/stress scenarios and version-pinned dependencies in an optional verification environment. The five pinned fixtures are a baseline, not complete statistical coverage.
3. Before claiming host/device conformance, test real-time callbacks, visual consumers, gaps, resets and channel correctness in the target audio application, plus calibrated reference measurements.
4. Recheck live PR head, code review and fresh CI before merging; keep the hardening evidence and original audit history in Kestrel memory.

## Revisit when

Any remediation PR lands, audio reference scripts or tests change, the curriculum expands into normative loudness/true peak, or a connected app uses these mathematical conventions. Recheck live branch and test results: this report describes an inspection at a specific revision.
