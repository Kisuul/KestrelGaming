---
name: audio-ppm-metering
description: Distinguish and audit legacy BBC/EBU/Nordic quasi-peak programme meters, select an explicit PPM profile, calibrate TEST tone and digital sample references, implement/measure burst and return ballistics, and reject false claims of IEC/EBU compliance against independent published fixtures.
---

# Audio peak-programme metering — a fast-looking needle is not evidence

## Activate when

Use for **PPM / Peak Programme Meter / quasi-peak** level indicators, historical BBC/EBU/Nordic studio alignment, burst integration, return-speed measurements, meter scale and test-tone references, or auditing a software meter advertised as "PPM compliant." This skill does **not** implement an IEC-certified instrument. If a user merely says "peak meter," establish whether they need **sample peak**, **true peak**, **quasi peak (PPM)**, **VU/program volume**, or **programme loudness** before choosing the algorithm. If not specified and materially important, ask which measurement controls the decision.

Load only relevant dependencies: [audio-dsp-core](../audio-dsp-core/SKILL.md) for processing tap, units and result evidence; [audio-timebase-sync](../audio-timebase-sync/SKILL.md) for sample epochs; [audio-sample-peak](../audio-sample-peak/SKILL.md) or [audio-true-peak](../audio-true-peak/SKILL.md) for clipping/overshoot decisions; [audio-vu-metering](../audio-vu-metering/SKILL.md) for a *different* 300 ms volume indicator; [audio-numerical-stability](../audio-numerical-stability/SKILL.md) for robust state; [math-verification](../math-verification/SKILL.md) for independent expectations. Do **not** preload every audio skill.

## Engineering procedure

1. **Identify instrument family and edition.** The historically documented EBU Type IIb (Tech 3205-E, November 1979), BBC Type IIa and IEC Type I/Nordic have different scales/ballistics. The first bounded reference here is **EBU Type IIb normal-mode burst FIT, PARTIAL**, with a known failed frequency-response requirement. Neither slow mode nor BBC, Nordic, or IEC TR 60268-18 is implemented. Fail closed on unknown profiles. The EBU marks Tech 3205 as legacy, superseded in operating practice by EBU R128 loudness guidance.
2. **Define calibration before interpreting dB.** Historical **EBU TEST** corresponds to a 1 kHz sine at **0.775 V RMS** (0 dBu) at the specified analogue reference point. This ideal sine's peak is `sqrt(2)*0.775 V`. For normalized PCM the corresponding peak reference must be *provided explicitly* based on a known system alignment; it is not universally -18 dBFS, +4 dBu, or unit peak. Report **dB relative to TEST**, never relabel it as dBFS, dBTP, LUFS, dBu or physical SPL.
3. **Use the actual historical test signals.** The [independently fixed acceptance ledger](references/PPM_CONTRACT.md) and [published fixture table](../../tests/fixtures/AUDIO_PPM_EBU_1979_GOLDENS.md) require calibrated isolated sine bursts: 5 kHz for 100, 10, 5, and 1.5 ms; **at least 10 kHz for 0.5 ms**, so the shortest burst contains five cycles. Measure the **maximum meter indication**, not the callback-end value or sample peak. Burst levels are +8, +6, +4, -1, -9 dB relative to TEST with specified separate tolerances. The historic integration time is the *-2 dB reading from a 10 ms 5 kHz burst*, not a chosen RC `tau`.
4. **Do not infer an algorithm from one test.** A simple first-order envelope fitted to the 10 ms criterion fails the 5, 1.5 and 0.5 ms targets. The [reference](scripts/reference_ppm.py) therefore uses two lowpass time scales on a calibrated absolute-value rectifier and a separate slow return ceiling. The **time constants were fitted to the published bursts**. Passing those same values is calibration, **not independent conformance proof**. Compare also multiple onset phases/rates, polarity, overload, return, frequency response and actual unknown programme waveforms.
5. **Separate source, detector, state and display.** Declare processing tap, channel identity, rational sample rate, sample index and epoch. Run independent per-channel detectors, not an implicit stereo sum (antiphase material must still indicate on each channel). Do not quantize, normalize, clip, or replace the meter with a visual smoothing animation. Display refresh and optional peak hold must not change the measured result. Reject seek/gap and rate/calibration changes without an explicit fresh epoch and reset.
6. **Check the full instrument, including failures.** EBU normal-mode tests include 2.8±0.3 s for a **24 dB** fall, 1 kHz +9 dB rising past +8 within 150 ms, overswing <=0.5 dB and flatness **±0.3 dB from 31.5 Hz to 16 kHz**. A correct *average* decay in dB is not automatically a release time constant. The present reference **FAILS flatness**: a 400 ms, 31.5 Hz sine at 48 kHz indicates roughly **+2.15 dB** relative to its normalized TEST amplitude; 16 kHz indicates approximately **-0.82 dB**. Those are explicit limitations, not tolerated as "close enough". No full IEC physical input impedance/distortion/environmental conformance is claimed.
7. **Distinguish calculation confidence from metrological confidence.** Run the [bounded Python oracle](scripts/reference_ppm.py) and [the regression suite](../../tests/test_audio_ppm_reference.py), optionally [the independent SciPy arithmetic checker](scripts/check_scipy_ppm.py). The SciPy check compares two implementations of the *same model*. It does not independently validate the model's resemblance to real instruments. A physical or certified device comparison remains open. Never infer actual performance of a different programming language or realtime driver from Python unit tests.
8. **Teach correct engineering decisions.** A PPM under-reads short transients by design and cannot certify lack of clipped integer PCM, intersample true peak, or LUFS programme loudness. When choosing an indicator, justify its use against the actual objective (international legacy alignment versus live clipping/loudness management). Report uncertainty and source edition. If a user requires **EBU/IEC conformance**, the current reference is **not an acceptable implementation**; recommend further design and verification before deployment.

## Tests and acceptance

```sh
python3 -m unittest discover -s tests -v
python3 tools/validate_seed.py
python3 -m unittest tests.test_audio_ppm_reference -v  # if importable in the repo
python3 skills/audio-ppm-metering/scripts/check_scipy_ppm.py --seed 20261105 --cases 24  # optional SciPy
# git diff --check
```

Expected educational module: a narrow, testable procedure that makes compliant and noncompliant behaviors distinguishable, independent decision examples, explicit historical provenance, and rejection of false instrument claims. **This is not a certification milestone.** An acceptable implementation for live compliance would also need published/independent frequency, impulse/pulse, dynamic linearity, slow-mode if supported, phase, analogue electrical/overload and varied programme tests; in its current form, some of these fail or remain untested.

## Primary references

- [EBU Tech 3205-E, 2nd ed., November 1979](https://tech.ebu.ch/docs/tech/tech3205.pdf), §§ 2–4 and Tables 2–3 (historical, expressly superseded by EBU R128).
- [ITU-R BS.645-2 (1992), Annex 1/2](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.645-2-199203-I%21%21PDF-E.pdf), historical alignment signals and comparative PPM characteristics.
- [IEC 60268-10:1991, Ed. 2](https://webstore.iec.ch/en/publication/1205), primary standard catalogue only; full IEC text not examined and no IEC conformance claim.
- [EBU R 128 modern loudness guidance](https://tech.ebu.ch/loudness), deliberately different measurement regime.
