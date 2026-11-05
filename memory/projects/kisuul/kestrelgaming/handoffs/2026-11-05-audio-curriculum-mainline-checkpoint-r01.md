---
schema: 1
id: 2026-11-05-audio-curriculum-mainline-checkpoint-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: ChatGPT
created: 2026-11-05
updated: 2026-11-05
sources: "PR #2 head 435a3b10c6e23cca2aba4712fb03fd148d65a13a; GitHub Actions 42004818873 (451 tests); source review and independent CPython 3.13.5 arithmetic probes 2026-11-05; owner full-curriculum merge restriction."
---

# Audio engineering curriculum — mainline memory checkpoint, 2026-11-05

## Summary

**Task outcome:** PARTIAL

This handoff is informational; the audio curriculum remains incomplete and no audio implementation was changed by this memory update.

As independently inspected on **2026-11-05**, [Kestrel PR #2](https://github.com/Kisuul/KestrelGaming/pull/2) is open and unmerged. The audio development branch `skills/audio-dsp-core-foundation-2026-11-03`, head `435a3b10c6e23cca2aba4712fb03fd148d65a13a`, has **19 developed audio skills out of 73 planned**, with **54 outstanding**. The already merged **six shared mathematics skills are not counted** in the 73. The audio curriculum remains a set of selectively loadable engineering procedures, contracts, bounded educational reference implementations and fixtures—not a production DSP runtime or certified instrument suite.

**Owner's explicit gate:** **DO NOT merge umbrella PR #2 into `main`** before all 73 audio modules have been completed and independently reviewed, followed by explicit owner approval. A green CI suite, individual child-PR integration into the audio development branch, or this progress notice does not waive that gate. See the [recorded owner decision on the audio branch](https://github.com/Kisuul/KestrelGaming/blob/435a3b10c6e23cca2aba4712fb03fd148d65a13a/memory/projects/kisuul/kestrelgaming/2026-11-04-audio-curriculum-full-completion-gate-r01.md).

**Source of truth for live work:** [PR #2](https://github.com/Kisuul/KestrelGaming/pull/2), the [audio branch skill catalog](https://github.com/Kisuul/KestrelGaming/blob/435a3b10c6e23cca2aba4712fb03fd148d65a13a/skills/INDEX.md), and the [numbered running roadmap](https://github.com/Kisuul/KestrelGaming/blob/435a3b10c6e23cca2aba4712fb03fd148d65a13a/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-03-audio-skills-roadmap.md). This concise mainline checkpoint must **not replace or overwrite** those detailed records. Recheck the branch before any agent resumes.

## Evidence

### Implemented/verified versus unverified

- **Observed:** Nineteen indexed audio procedures include DSP core, FFT/windows, PSD, RMS/crest, STFT/waterfall, sample and experimental true peak, fixtures, sample-timebase, PCM, resampling, channel mapping, filter design, streaming buffering, provenance, numerical stability, VU-style and historically fitted PPM metering. Each has associated scoped source/reference material; do not interpret the count as 19 standards-conformant instruments.
- **Observed remote CI:** [GitHub Actions run 42004818873](https://github.com/Kisuul/KestrelGaming/actions/runs/42004818873) completed successfully for exactly `435a3b10c6e23cca2aba4712fb03fd148d65a13a`. Job logs report **451 unittest cases passed** and structural validation succeeded. This is **remote CI evidence**, not an independently executed local full checkout.
- **Unverified:** Blind agent with/without-skill effectiveness, production application integration, realtime/device performance, physical calibration and full IEC/EBU/ITU conformance. Existing tests establish bounded reference behavior only.
- **Observed scope:** The audio PR has 132 changed paths at this revision and diverges from `main`; integration/reconciliation must preserve concurrent baseline changes. No changes to PR #2 are authorized or performed by this checkpoint.

### Independent initial adversarial review — evidence and limits

The **2026-11-05 partial audit** examined PR #2's source and CI; it is **not** a completed audit of all 19 modules.

1. **AUD-001 (numerical correctness; action needed):** `skills/audio-power-spectral-density/scripts/reference_psd.py` and `skills/audio-spectrogram-waterfall/scripts/reference_stft.py` compute terms equivalent to `abs(X)**2 / (fs*sum(w*w))`. For accepted finite inputs such as `samples=[1e100, 0.0]`, `window=[1e100, 1e100]`, `fs=48000`, a source-derived DC-bin numerator squares `1e200` and overflows, although the exact normalized result is approximately `1.0416666666666666e195` (finite binary64). This was **independently reproduced using source-expression arithmetic and rational comparison on CPython 3.13.5**, not by importing/running the original modules. Add exact-head regression tests and range-aware normalization; verify the chosen supported domain and final-output nonrepresentability policy.
2. **AUD-002 (numerical correctness; action needed):** `skills/audio-fft-spectrum/scripts/reference_dft.py` calculates the one-sided amplitude as `abs(X)*factor/sum(window)`. For `samples=[1e308,0,-1e308,0]`, `window=[0.5]*4`, the k=1 bin magnitude is `1e308`; multiplying by 2 first yields `inf`, while the normalized mathematical amplitude is the finite `1e308`. Independently reproduced using source-derived binary64 arithmetic; the original module was **not directly executed** for this audit counterexample. Demand a discriminating test and a numerically safe computation, not a broad acceptance-tolerance increase.
3. **AUD-003 (standards conformance; known and transparently recorded):** The [audio-ppm-metering skill](https://github.com/Kisuul/KestrelGaming/blob/435a3b10c6e23cca2aba4712fb03fd148d65a13a/skills/audio-ppm-metering/SKILL.md) fits EBU Tech 3205-E isolated bursts but **fails** the historical ±0.3 dB frequency-flatness requirement (branch tests document roughly +2.15 dB at 31.5 Hz and -0.82 dB at 16 kHz). The authors **explicitly disclose this** and set `standards_conformance=False`; do not present it as concealed failure or IEC/EBU compliance. Published burst values were also training targets, so matching them is fit verification, not independent certification. This audit inspected the relevant tests and contract, **not** a locally executed PPM run.

The extreme-value counterexamples concern finite arithmetic in bounded educational references, not evidence of a deployed application's audible malfunction. The [audio-numerical-stability skill](https://github.com/Kisuul/KestrelGaming/blob/435a3b10c6e23cca2aba4712fb03fd148d65a13a/skills/audio-numerical-stability/SKILL.md) already teaches these failure classes; cross-skill implementation consistency needs checking.

## Next action

1. **For audit/remediation agents:** Confirm current PR #2 head, reproduce AUD-001/002 *against original reference modules* with independent expected values, add negative tests and fix without widening tolerances or changing quantities/units. Report real red/green results and preserve branch safety.
2. **For integrators:** Test cross-module contracts (units, channel identity, sample clocks/epochs, discontinuities, calibration, rejected-input atomicity), including true consumer paths that individually green unit suites may miss. Audit the remaining modules using independent oracles and explicit limits.
3. **For curriculum authors:** Continue the remaining 54 obligations using the audio branch's live roadmap and handoff ownership. Its next **proposed**, not yet completed, module is `audio-program-loudness` (ITU-R BS.1770/EBU R128 research before implementation). Other remaining levels-family items include loudness range and envelope dynamics.
4. **For behavioral evaluators:** Run fixed, blinded with/without-skill tasks; separate procedural activation, engineering correctness, false positives and context/tool cost. Until executed, outcome is **NOT RUN**.
5. **For all Kestrel agents:** Work in the actual authorized task branch. Do not overwrite another agent's audio handoffs, change `main` from the audio workstream, or infer that this informational checkpoint grants permission to merge PR #2.

**Changed by this memory task:** Only a mainline project-scoped checkpoint and its project-index link. No audio skill, source, fixture, test, permission, contract, CI configuration, or agent identity is changed. This record is a dated snapshot, not a continuously refreshed status feed.

## Revisit when

PR #2 head, module count, CI evidence, standards edition, numeric regression tests, correction commits or owner merge criteria change; an agent begins new audio work; or an independent full audit/behavioral evaluation supersedes this partial review. Review PR #2 and its branch roadmap before accepting any number here as current.
