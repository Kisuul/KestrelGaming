---
schema: 1
id: 2026-11-05-audio-ppm-metering-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: ChatGPT
created: 2026-11-05
updated: 2026-11-05
sources: "Research 2026-11-05: official IEC 60268-10:1991 and IEC TR 60268-18:1995 catalogues; EBU Tech 3205-E second edition 1979 (legacy) sections 2-3; ITU-R BS.645-2 (1992) annexes; EBU R128 v5.0 (2023); Orban Loudness Meter 2.9.6 manual (2017). Numerical one-pole rejection calculated against legacy EBU burst table. Live PR #2 ba23b76f041b730ff2d2c63976114fc8fa606c39: 18/73 skills, 55 pending."
---

# Skill 19 research — audio PPM metering (before implementation)

## Summary

**Task outcome:** COMPLETE

**This means research and the proposed engineering acceptance plan are complete; the skill itself is NOT implemented, indexed or counted.** At observed [audio PR #2](https://github.com/Kisuul/KestrelGaming/pull/2) head \`ba23b76f041b730ff2d2c63976114fc8fa606c39\`, Kestrel has **18/73 audio modules developed, 55 remaining**. The owner [requires all 73 completed before any umbrella PR #2 merge into main](../2026-11-04-audio-curriculum-full-completion-gate-r01.md).

**Research decision (proposed, not yet implementation acceptance):** Use the publicly available, historically defined **EBU Type IIb, normal-mode quasi-peak PPM** as the first tightly scoped instrument model. Its detailed, publicly inspectable burst/return tests make meaningful independent acceptance possible. Explicitly label this profile **EBU Tech 3205-E (1979), legacy reference**, not modern EBU R128, not generic "digital peak", not IEC-certified. Other PPM families become distinct future profiles only if source-verified and separately tested; avoid silent "PPM" defaults.

The [canonical roadmap](2026-11-03-audio-skills-roadmap.md) still owns the count and identifies \`audio-ppm-metering\` as the next pending skill. Research alone must not alter that file or \`skills/INDEX.md\`.

## Evidence

### Source hierarchy, edition and interpretation

1. **IEC primary catalogue:** [IEC 60268-10:1991, Ed. 2](https://webstore.iec.ch/en/publication/1205) is listed **valid** and applies to peak-programme meters, distinguished from IEC 60268-17 volume indicators. The complete IEC document is paywalled; **its entire normative requirements have not been audited**. Do not assert IEC 60268-10 conformance based only on freely visible descriptions.
2. **Detailed, freely accessible historical specification:** [EBU Tech 3205-E, 2nd ed., November 1979](https://tech.ebu.ch/docs/tech/tech3205.pdf), especially §§ 1–3 and Tables 1–3. It identifies IEC Type IIb and says Type IIa differs in scale/marking. The document itself states it is **superseded by EBU R128 and retained as historical reference**. It remains a legitimate traceable test *fixture source* for the historical instrument, not a current broadcast-loudness policy.
3. **Independent primary corroboration:** [ITU-R BS.645-2 (March 1992)](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.645-2-199203-I%21%21PDF-E.pdf), especially Annex 1 and Annex 2 Table 1, distinguishes BBC IEC IIa, EBU IEC IIb and IEC Type I: **BBC 10 ms integration, 26 dB fall in 3 s; EBU 10 ms, 24 dB fall in 2.8 s; Type I 5 ms, 20 dB fall in 1.7 s**. Note that return intervals reference DIFFERENT dB excursions, so comparing the raw seconds without their dB range is wrong. "Integration time" is a specified -2 dB burst-response criterion, not an arbitrary attack exponential's parameter.
4. **Digital indicator is a different specification:** [IEC TR 60268-18:1995](https://webstore.iec.ch/en/publication/1217) is a **Technical Report** for sampled/quantized digital-audio peak indication. It is not interchangeable with IEC 60268-10's Type IIb electromechanical context. Do not imply the IEC technical report is a fully inspected normative algorithm; its full text has not been obtained.
5. **Modern operational boundary:** [EBU R128 v5.0, November 2023](https://tech.ebu.ch/publications/r128?categoryFilter=presentations) uses LUFS/loudness range and maximum true-peak descriptors; [ITU-R BS.1770-5 (November 2023)](https://www.itu.int/rec/R-REC-BS.1770) governs loudness and true-peak algorithms. Neither VU, quasi-peak PPM, sample-peak nor loudness is substitutable for another. [EBU loudness guidance](https://tech.ebu.ch/loudness) explicitly describes the move away from PPM-only operational practice.
6. **Independent industry experience:** The [Orban Loudness Meter 2.9.6 operating manual](https://usermanual.wiki/Collections/Radio-Manuals/Orban_Loudness_Meter/Documentation/FreeOrbanLoudnessMeter_2.9.6_Readme.pdf), 2017, reports that its oversampled single-time-constant PPM misses some Tech 3205 burst specifications. This is published implementer testimony, **not an independent compliance certification or a full reproduction of Orban's unpublished implementation**.

### EBU Tech 3205-E normal-mode expected-value matrix (legacy)

Input amplitude is chosen to yield **+8 dB** on a continuously applied pure 5 kHz sine. Apply isolated sine bursts and measure the maximum indicated level. These are independent *published acceptance values*, not predictions derived from our future detector:

| Burst duration | Tone | Expected reading | Published tolerance |
| --- | --- | --- | --- |
| 100 ms | 5 kHz | +8 dB | ±0.5 dB |
| 10 ms | 5 kHz | +6 dB | ±0.5 dB |
| 5 ms | 5 kHz | +4 dB | ±0.75 dB |
| 1.5 ms | 5 kHz | -1 dB | ±1.0 dB |
| 0.5 ms | **at least 10 kHz** to contain five cycles | -9 dB | ±2.0 dB |

Additional **separately defined** acceptance measurements from Tech 3205: 10±2 ms to register 2 dB below the continuous +9 dB indication (5 kHz); +12 to -12 dB return in **2.8±0.3 s** normal mode; 1 kHz continuous +9 onset should pass +8 in **at most 150 ms**; transient overswing no greater than **0.5 dB**; flatness within **±0.3 dB from 31.5 Hz to 16 kHz** over the stated indication range; polarity reversal test difference ≤0.5 dB on the defined asymmetrically clipped waveform; the stated pulse duration/overload tests. Tech 3205 also describes **slow mode**, a separate feature with its own burst and **3.8±0.5 s** return performance. Do not silently implement it with normal-mode settings or claim its compliance without testing.

The **static** 1 kHz sine test input is **0.775 V RMS (0 dBu) at the specified analogue reference point**, indicating "TEST" / 0 dB relative. ITU-R BS.645-2 specifies that alignment tone corresponds to BBC **mark 4** and EBU **TEST**. A normalized PCM-to-analogue alignment (e.g. a chosen dBFS sine reference) must be **explicit configurable provenance**, not invented as universally -18 dBFS or +4 dBu. Distinguish relative dB of an indicator, dBu voltage, dBFS digital sample reference, dBTP true peak and LUFS loudness. A Type IIa BBC display scale is not permission to claim full BBC physical-instrument conformance.

### Falsification before implementation: the naive one-pole detector is insufficient

For an *ideal envelope* first-order attack, y(t)/A = 1 - exp(-t/tau). Choosing the 10 ms target, 20log10(y/A) = -2 dB, gives tau ≈ **6.3232 ms**. That model predicts, relative to the steady +8 dB level:

| Duration | One-pole predicted reading | Tech 3205 target |
| --- | --- | --- |
| 10 ms | +6.00 dB | +6 ±0.5 |
| 5 ms | **+2.75 dB** | +4 ±0.75 |
| 1.5 ms | **-5.51 dB** | -1 ±1 |
| 0.5 ms | **-14.38 dB** | -9 ±2 |

**Result:** The mathematically correct one-pole step envelope fails multiple prescribed targets, even *before* considering the actual sine carrier, sample phase, anti-aliasing, display overshoot, full frequency response and 0.5 ms ≥10 kHz five-cycle condition. These figures are a **model rejection calculation**, not measured results from a digital PPM. A multi-timescale attack/rectification plus display system may be explored but must be judged by the *complete* independent burst and ancillary tests, not by fitting only one point.

The 24 dB/2.8 s normal return is **8.571 dB/s on average**, not a generic "2.8 s release time constant"; if expressed as an exponential decay in *linear amplitude*, its equivalent tau is ~**1.013 s**, but a specification for falling by 24 dB is NOT itself a specification of one-pole topology.

### Engineering and verification decisions for the future skill

- Declare instrument **family/profile and edition first**: legacy EBU Type IIb normal-mode by default for this specific skill's reference. Fail closed on unknown PPM profiles; mark Type I, BBC Type IIa, digital IEC TR 60268-18, slow mode and modern loudness as separate profiles or explicit unsupported capabilities. No generic, unlabeled "PPM" claim.
- Separate (1) source metadata/calibration in V or normalized PCM, (2) rectifier/carrier response, (3) quasi-peak ballistic/integration state, (4) scale/units/overload behavior, (5) *display refresh or peak hold*. Do not use RMS level or 300 ms VU needle code to emulate PPM. Use independent per-channel states, true sample clocks, meaningful epoch/gap rules and explicit reset policy.
- Test **raw carrier** waves, not only idealized attack steps. For 0.5 ms use ≥10 kHz (five cycles), run representative 44.1/48/96/192 kHz input rates and multiple burst onset phases, declare any oversampling/interpolation policy and prove its bandwidth/accuracy limits. Test the **maximum displayed response** across a burst plus trailing response period, not merely an arbitrary callback-end sample.
- Pre-register the complete historic normal-mode acceptance matrix above **before** fitting parameters. Add off-target tests: 1 kHz sine/known voltage calibration, exact silence, polar inversion, independent L/R including antiphase, slowly modulated programme, rare impulses and clipping/over-reference, difference versus VU/RMS/sample peak/true peak/LUFS, all callback chunk schedules, large sample origins, repeated short bursts, malformed/nonfinite inputs and atomic rejection. No tests may derive expected values by calling the implementation being assessed.
- State a numerical error budget separately from published instrument tolerances. Report actual failures without widening tolerances to get green. A standard-library numerical reference and an optional independently derived SciPy implementation can corroborate *algorithm arithmetic* but cannot substitute for the published burst conformance tests, physical equipment or acoustic relevance.
- Design held-out **agent usefulness** tasks: choose correct type given ambiguous "peak meter" requirements; map BBC mark 4 against EBU TEST without assuming physical voltage gain; reject -18 dBFS universal calibration; diagnose 1.5 ms tone under-reading; distinguish PPM from oversampled true peak; preserve sample epochs/phase across callback sizes. Pre-register decisions and score with/without skill later, not as part of this research handoff.
- The actual IEC 60268-10 full text, IEC 60268-18 full text, physical frequency tests, analogue electrical requirements and whole-agent A/B performance have **NOT** been independently verified. Keep compliance language limited to the independently tested *selected historic profile* and its checks.

## Next action

**Do not credit skill #19 yet.** Author \`skills/audio-ppm-metering/SKILL.md\`, \`references/PPM_CONTRACT.md\`, a bounded reference, independent published-burst fixtures, negative and metamorphic tests, and an optional independent numerical checker on a reviewable isolated branch based on the latest audio PR head. Use the [Kestrel audio test-fixture](../../../../../skills/audio-dsp-test-fixtures/SKILL.md), [sample clocks](../../../../../skills/audio-timebase-sync/SKILL.md), [numerical-stability](../../../../../skills/audio-numerical-stability/SKILL.md), and [VU metering](../../../../../skills/audio-vu-metering/SKILL.md) selectively, without rewriting their contracts. Verify target tests, Kestrel structural checks, full tests and diff; integrate after hostile review and synchronize the canonical roadmap. Preserve PR #2 as **open/unmerged** until **all 73** modules and explicit owner signoff.

## Revisit when

The owner chooses a different meter family; full IEC standard text becomes available; an implementation passes/fails actual 3205 tone bursts; sample-rate/phase and analogue calibration experiments change the model; a held-out agent-use experiment is performed; or related audio skills are integrated.
