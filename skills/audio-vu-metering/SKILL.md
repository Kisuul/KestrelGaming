---
name: audio-vu-metering
description: Engineer and audit VU-style audio level indication with explicit 1 kHz alignment, mean-rectified detection, 300 ms mechanical ballistics, overshoot, source/sample clocks, and independently falsifiable peak/RMS/loudness distinctions.
---

# Audio VU metering — know what the needle is indicating

## Activate when

An agent needs to design, calibrate, implement, compare, or debug a VU or standard-volume-indicator-style meter; define a 0 VU lineup, explain moving-needle ballistics, or assess whether program audio is near its **declared alignment level**. Read the [meter contract](references/VU_METER_CONTRACT.md) before writing DSP code or recommending calibration.

**Do not activate as a substitute for** [sample peaks](../audio-sample-peak/SKILL.md), [true peak](../audio-true-peak/SKILL.md), [RMS](../audio-rms-crest-factor/SKILL.md), peak programme metering (future `audio-ppm-metering`), or BS.1770/LUFS loudness (future `audio-program-loudness`). The [audio DSP core](../audio-dsp-core/SKILL.md) defines input tap and measurement conventions; [timebase](../audio-timebase-sync/SKILL.md) defines sample epochs and gaps; [channel mapping](../audio-channel-mapping/SKILL.md) handles layouts; [math numerical analysis](../math-numerical-analysis/SKILL.md) and [verification](../math-verification/SKILL.md) are conditional support, not required wholesale.

## Decision and implementation procedure

1. **Choose the instrument, not a fashionable label.** Need digital clipping, a transient, or peak headroom? Use sample-peak/true-peak/PPM as appropriate. Need programme loudness? Use a defined loudness meter. Need to align audio programme voltage and display approximate average operation near a specified lineup reference? VU may be appropriate. A rolling 300 ms RMS is *not* a standard VU indicator, and a smoothed dBFS peak is not necessarily one either. Say what the detector actually measures.
2. **Identify the signal and clock.** State whether samples are dimensionless float PCM or calibrated volts, the actual measuring tap (pre/post gain), rate as an exact rational, channel labels and whether inputs are already channel-mixed. Measure channels independently unless a channel-mapping policy is explicitly selected. State epoch, half-open input sample span, signal discontinuities and sample-to-display refresh behavior. One displayed value per callback is fine; one detector update per GUI paint is **not**.
3. **Declare the 1 kHz tone and 0 VU reference.** Analog: `dBu=20 log10(V_RMS/0.775 V)`; a typical studio `+4 dBu` reference has about 1.228 V RMS, but equipment calibration is configurable. Digital: choose a *sine-wave peak relative to a normalized PCM sample peak of 1*, e.g. `-20 dBFS-peak` or `-18 dBFS-peak`, with reference sine peak `10^(dB/20)`. **Do not silently equate RMS-dBFS, peak-dBFS, dBu, dBm, VU, LUFS, or perceived loudness.** Record the actual lineup; the latter digital values are examples, not universal prescriptions.
4. **Choose and disclose the detector topology.** A physical SVI uses a full-wave rectifier and electromechanical pointer with defined dynamic behavior; its instrument transfer is neither the textbook RMS window nor just a one-pole smoothing filter. Our [bounded mathematical reference](scripts/reference_vu_meter.py) uses `mean(full-wave rectification)` in a continuous-time calibration approximation: an ideal sine of peak `A_ref` has mean absolute amplitude `2*A_ref/pi`. Its per-sample mechanical target is `u[n]=(pi/2)*abs(x[n])/A_ref`. This means a DC/square signal of the same RMS as a sine reads about **+0.91 VU**, not the same as a true-RMS meter. Sampled sine tones differ slightly with rate/phase.
5. **Specify ballistics in *time*, not callback size.** The reference uses an idealized second-order underdamped needle, 99% first response at **300 ms** and 1.25% overshoot of steady deflection. These are properties of a chosen model inspired by IEC/ANSI practice, *not a claim that it passes all IEC 60268-17:1990 requirements*. Exact zero-order-hold second-order state integration per sample avoids callback-dependent Euler instability. The response to a 300 ms 1 kHz burst must be checked separately from a constant detector step. Mechanical stop, electrical load, rectifier frequency behavior, and physical pointer scale are not implemented.
6. **Distinguish the quantity from its display.** The pointer deflection is a linear amplitude-ratio quantity; `VU=20 log10(deflection)` relative to the chosen 0 VU tone. Exact initial silence produces no finite logarithm (return `None`, not fictional 0 VU). Display scale often runs roughly −20..+3 VU; a value over +3 VU is flagged, **not clipped or normalized**. Report sample peak separately in input units, explicitly scoped to its input block; that diagnostic does **not** establish true peak or clipping history. A negative transient of the idealized oscillator is clamped only for display, not used to alter audio.
7. **Protect continuity and input validity.** Reject nonfinite inputs, ambiguous channel metadata, unequal/empty input planes, unsupported rates, nonrepresentable normalization/ballistic state, and cursor gaps/overlaps. Compute proposed outputs and state before committing anything. Changing calibration, layout, source epoch, rate, or processing tap requires a new explicitly identified meter epoch. Do not treat synthetic silence, a pause in display updates, or dropped callback frames as uninterrupted original audio.
8. **Falsify with more than one oracle.** Check (a) 1 kHz aligned tone settles near 0 VU, (b) ±6 dB tone amplitude translates to ±6 VU after settling, (c) independent second-order step response reaches 99% in 300 ms with 1–1.5% overshoot, (d) same RMS sine and DC differ in rectified-mean response, (e) impulse is not represented as an instantaneous peak, (f) 1/7/48/variable sample callback chunking yields the same final state, (g) bad/gapped blocks are atomic, and (h) independent channel signals and exact sample clocks survive. Use [the 40+ regression cases](../../tests/test_audio_vu_meter_reference.py), [frozen analytic goldens](../../tests/fixtures/AUDIO_VU_METER_GOLDENS.md), and the optional [SciPy ZOH differential checker](scripts/check_scipy_vu.py), not merely self-referential expected values.
9. **Report maturity honestly.** The bounded Python oracle is **not** a certified IEC 60268-17 SVI, a broadcast compliance instrument, a real-time-safe plug-in, an RMS/PPM/LUFS device, or a measurement of acoustical loudness. Production acceptance requires actual calibrated hardware/host comparison, edition-specific test stimuli, tone burst and frequency-response sweeps, repeatable measurement taps, UI sampling and rendering tests, and output level/latency validation.

## Useful engineering cross-checks

- A 1 kHz sine at **−20 dBFS-peak** on a meter explicitly lined up at that level should settle near **0 VU**, yet its digital *sample peak* is **0.1**, or −20 dBFS-peak. The VU needle alone cannot certify safe instantaneous peaks elsewhere.
- A 10 ms tone burst at the reference amplitude must read **far below** a continuous 1 kHz tone with the same peak; changing refresh frequency cannot change the detector response.
- The same-RMS DC voltage and sine are **not equivalent** for a mean-rectified detector, even though a conventional RMS meter would report equal values.
- A 300 ms rectangular RMS average, a one-pole envelope, a second-order moving-coil model and a hardware SVI are **different constructions**. Document the chosen model before applying standards labels.

## Local commands (in Kestrel repo)

```sh
python3 -m unittest discover -s tests -v
python3 tools/validate_seed.py
python3 skills/audio-vu-metering/scripts/check_scipy_vu.py --seed 20261105 --cases 24  # optional NumPy/SciPy
# git diff --check   # when working in a local Git checkout
```

The standard-library reference processes only 1–8 planar channels and 1–32768 frames per call, at sample rates 8–384 kHz. It is educational, scalar and not callback-real-time safe. High-frequency response is *not* certified across the range of accepted sample rates.

## Sources and applicability

- [IEC 60268-17:1990, corrigendum incorporated](https://webstore.iec.ch/en/publication/1216): the **electromechanical standard volume indicator** specification. This module is inspired by its measurement purpose; the model is **not** full-conformance-certified.
- [ITU-R Report BS.2054-4 (2014), §§4–5](https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BS.2054-4-2014-PDF-E.pdf): lineup examples (−20 dBFS sine), 99% response in 300 ms, limits of VU readings for peaks and loudness.
- [Audio Engineering Society, *Learn More: The venerable VU meter*](https://aes.org/resources/audio-topics/loudness-project/learn-more/): standard-volume-indicator history, rectifier/mechanical detector and distinction from true RMS.
- [IEC 60268-10:1991](https://webstore.iec.ch/en/publication/1205) and [ITU-R BS.1770](https://www.itu.int/rec/R-REC-BS.1770/en): different PPM and loudness/true-peak measurement purposes, **not** implemented here.
