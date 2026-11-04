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
sources: "PR #2 review at a0901b1cd9a01e118c5f9270e82424bdd155a214; GitHub Actions 41762386365 passed 84 tests; reviewed skills, scripts, tests, indexes and handoff; independently cross-checked one-sided PSD formulas against local SciPy 1.17.0 periodogram (8 configurations on 2026-11-03); reproduced finite-ratio log-underflow and RMS-square-underflow behavior from exact source expressions."
---

# Independent audit of the seven audio-analysis skills (review r01)

## Summary

**Review status:** FOLLOW-UP REQUIRED; no high-severity error found in the conventional FFT/PSD/level formulas during this inspection, but the branch has correctness/verification limitations and documentation drift worth fixing **before** advanced normative true-peak work.

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

## Recommended next action

1. Correct the stale spectrum skill description, tighten AES source, and add the two numerical stress tests/implementation fixes (plus long-block/short-hold meter guidance). Keep this a focused remediation batch with existing test coverage protected.
2. Add an independent differential-test layer for FFT/PSD/STFT (not merely cross-calling the reference implementation). Enforce practical output-range expectations and measurable tolerances.
3. Reverify current branch/CI and record the exact fix revision in this audit and curriculum handoff.
4. Only then continue to `audio-true-peak`, distinguishing an experimental oversampled estimator from a validated standards-conforming instrument.

## Revisit when

Any remediation PR lands, audio reference scripts or tests change, the curriculum expands into normative loudness/true peak, or a connected app uses these mathematical conventions. Recheck live branch and test results: this report describes an inspection at a specific revision.
