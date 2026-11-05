# Explicit contract — calibrated legacy quasi-peak PPM study, *not* compliance

[Skill](../SKILL.md) · [Reference source](../scripts/reference_ppm.py) · [Independent EBU values and failure ledger](../../../tests/fixtures/AUDIO_PPM_EBU_1979_GOLDENS.md) · [Research handoff](../../../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-05-audio-ppm-metering-research-r01.md).

## 1. Instrument identity and units

Selected educational profile `ebu-tech3205-1979-iib-normal-burst-fit-PARTIAL`. This does **not** instantiate a certified IEC 60268-10:1991 Type IIb, a BBC mark-4 PPM, Nordic Type I, EBU slow mode, or sampled-audio peak indication per IEC TR 60268-18. Type IIa/IIb have related physical time families but **different scales**; never silently alias them. EBU Tech 3205 is an archival spec; EBU R128 is the modern loudness recommendation.

Input `PpmConfiguration(sample_rate_hz: Fraction, channels: int, test_tone_peak_amplitude: float, input_unit: str)` requires **explicit** TEST peak amplitude and physical or PCM source units; no default -18 dBFS alignment. The historic analogue TEST tone is a 1 kHz, **0.775 V RMS** sine at 0 dBu; ideal sine peak = `sqrt(2)*0.775 V`. EBU TEST is **0 dB on the EBU scale**, not automatically 0 dBFS. `amplitude_db` handles zero as -infinity and avoids overflowing the amplitude/reference ratio.

Inputs are planar real finite samples with 1–8 channels, rational sample rate 44.1–192 kHz and 1–256 frames per call. These are *reference limits*, not universal PPM requirements. A sample index is a Python integer, never a rounded floating timestamp. For each block, the reporter supplies `epoch_id`, `start_sample`, exclusive end sample, source units, reference amplitude, per-sample and block-max indicated dB. No implicit audio resampling or remapping occurs.

## 2. Model exactly as implemented

At each channel and sample with `dt=1/sample_rate`, define full-wave input `d[n]=(π/2)*abs(x[n])`, converting **the average of a well-sampled sine's absolute value** to its ideal peak amplitude. Two first-order lowpass states evolve:

```
f[n] = f[n-1] + (1-exp(-dt/τ_f))*(d[n]-f[n-1])
s[n] = s[n-1] + (1-exp(-dt/τ_s))*(d[n]-s[n-1])
c[n] = w*f[n] + (1-w)*s[n]
i[n] = max(c[n], i[n-1]*exp(-dt/τ_return))
reading_dB[n] = 20*(log10(i[n])-log10(TEST_peak))
```

with constants `τ_f=1.39366241 ms`, `τ_s=9.23475167 ms`, `w=0.389565905`, and `τ_return=2.8 s/(24*ln(10)/20) ≈ 1.0133 s`. The two attack constants were **optimized against EBU Tech 3205 Table 2** using an ideal envelope and are therefore *trained on the normative burst table*. They are **not** historical analogue circuit values, general passband compensation, or an independent proof of conformance. The return uses the formula for an **exponential fall in linear amplitude** whose log indication falls 24 dB in 2.8 s; this is a design choice, not a normative topology.

Release is a slow falling ceiling; ripple/phase dependence at extremely low and high tones remains. It does not provide arbitrary-precision DSP, true peaks, LUFS, signal energy, future-packet interpolation, literal hardware ballistic mechanics or analogue-voltage interfacing. It does not clamp floating values at ±1. The example code checks nonfinite/overflow and rejects unrepresentable state changes atomically. Nonzero subnormal signals that cannot be represented after smoothing are rejected rather than claimed silent.

## 3. Pre-registered independent historical acceptance values

All isolated sine bursts calibrated to a continuously applied +8 dB EBU indication:

| Duration | Carrier | Published expected maximum dB re TEST | Tolerance |
|---:|---:|---:|---:|
| 100 ms | 5 kHz | +8 | ±0.5 dB |
| 10 ms | 5 kHz | +6 | ±0.5 dB |
| 5 ms | 5 kHz | +4 | ±0.75 dB |
| 1.5 ms | 5 kHz | -1 | ±1.0 dB |
| 0.5 ms | at least 10 kHz (five cycles) | -9 | ±2.0 dB |

EBU Tech 3205-E sections 2–3 also prescribe 10±2 ms integration defined by a 2 dB-short reading, +12 to -12 in 2.8±0.3 s, 1 kHz +9 crossing +8 in ≤150 ms, transient overswing ≤0.5 dB, **±0.3 dB flatness between 31.5 Hz and 16 kHz**, polarity reversal ≤0.5 dB under specified asymmetric waveform, pulse response, dynamic linearity and further slow-mode and hardware conditions.

**Observed model performance:** Fitted burst targets pass multiple 44.1/48/96/192 kHz sine phases. The reference **FAILS** the wide frequency-flatness requirement (at 48 kHz, 31.5 Hz reads roughly +2.15 dB vs the nominal full-amplitude reference; 16 kHz reads about -0.82 dB); this is a documented *negative result*. Matching fit targets plus an arithmetic differential alone is **insufficient** to claim Type IIb compliance. To legitimately claim compliance, first design a new model passing the *entire applicable test suite*, independently compare representative hardware or certified emulator as appropriate, and audit edition applicability.

## 4. Error, state and downstream interpretation

- Reject missing/unknown physical or digital input units, ambiguous or invalid TEST peak, unsupported PPM profile, bool/floating sample counters, malformed channel buffers, NaNs/Infs, overflowing and unrepresentable detector arithmetic.
- Reject gaps, overlaps, seeks, rate/calibration changes and reused epoch identifiers; use an explicit new epoch with a fresh config. Do not conceal missing audio with unmarked silence.
- Maintain state independently per channel and commit it only after every channel/frame validates. Partial invalid blocks must never advance the cursor or modify the meter.
- Report each sample's dB indication (including -infinity for exact silence) for independent timing tests. Display floors/peak-hold and graphics refresh are downstream, unimplemented policies.
- A PPM is a deliberately **quasi-peak** instrument; do not use it to guarantee PCM clip prevention, BS.1770 true-peak compliance, ITU/EBU loudness, or calibrated acoustic SPL. Full modern R128 metering is covered by other pending modules.

## 5. Verification and honest boundaries

The `tests/test_audio_ppm_reference.py` suite protects historical burst fixtures, different sample rates/phases, TEST calibration, steady/short signal differences, return, overswing, polarity symmetry, rate and channel guards, negative reset and atomic state, callback partition invariance. The *test that passes because flatness fails* is a deliberate **negative conformance finding**, not an assertion of instrument success.

The optional `scripts/check_scipy_ppm.py` computes each lowpass response with SciPy `lfilter` and the release peak using an independent vectorized maximum identity. It establishes **arithmetic agreement on seeded finite inputs only**. Its expected values use the model's published constants but do not claim blind, externally verified meter quality. No physical instrument, licensed complete IEC document, realtime callback, antialiasing/oversampling compensation or agent with/without-skill improvement was tested.

## 6. Primary source editions

[EBU Tech 3205-E, 1979](https://tech.ebu.ch/docs/tech/tech3205.pdf) · [ITU-R BS.645-2, 1992](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.645-2-199203-I%21%21PDF-E.pdf) · [IEC 60268-10 catalogue](https://webstore.iec.ch/en/publication/1205) · [EBU modern loudness programme](https://tech.ebu.ch/loudness).
