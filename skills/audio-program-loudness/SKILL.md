---
name: audio-program-loudness
description: Measure or audit BS.1770 programme loudness in LUFS or LKFS for an explicitly mapped channel bed. Use for integrated gating, momentary or short-term loudness, or EBU R 128 delivery analysis. For clipping, true peak, VU, PPM, SPL or Loudness Range alone, use the corresponding measurement instead.
---

# Audio programme loudness

## Choose the measurement

| Decision | Quantity |
| --- | --- |
| Compare entire programmes, or check the loudness of a delivery segment | Integrated (I), with the two-stage gate |
| Inspect a syllable, impact or other short event | Momentary (M), a 400 ms ungated rectangular window |
| Follow the level of a phrase or scene | Short-term (S), a 3 s ungated rectangular window |
| Check whether samples or the reconstructed waveform can clip | Sample peak or true peak, even when I meets target |
| Measure the spread of levels over a programme | Loudness Range (LRA), a separate Tech 3342 analysis |

LUFS and LKFS report the same absolute value. Use LU for a difference from a
stated reference or between readings. Apply the −23 LUFS target only when the
delivery policy calls for EBU R 128. Check the actual delivery policy before
suggesting gain. `target - I` estimates the change in gain in dB. Remeasure
after gain or limiting because the gate can select a different set of blocks.

## Procedure

1. Identify the input tap, exact sample rate, PCM format and full-scale
   reference, ordered speaker labels, sample epoch and half-open sample range.
   For delivery, measure the audio at the declared delivery tap, after any
   gain, downmix or processing that changes that signal. Use normalized PCM
   with nominal full-scale amplitude 1. Do not infer a layout from plane count.
2. Select the standards scope. The bundled reference covers **ITU-R BS.1770-5
   Annex 1 at 48 kHz** for explicitly labeled mono, stereo, 5.0 and 5.1.
   Resolve other rates with a verified filter design or a separately declared
   resampling step. Route advanced channel or object layouts to their own
   profile. See the [measurement contract](references/PROGRAM_LOUDNESS_CONTRACT.md)
   for coefficients, speaker labels, and the exact input contract.
3. K-weight each included channel with the shelf and RLB high-pass cascade.
   Preserve its filter state across contiguous callbacks. Exclude labeled LFE.
   Weight and sum channel **powers**. Changing R's polarity leaves stereo
   loudness unchanged. A mono sum can cancel that signal.
4. Use full, ungated windows for M and S. For I, use complete 400 ms blocks at
   100 ms intervals. Keep blocks strictly above −70 LUFS for the first energy
   mean. Set the relative gate 10 LU below that mean's loudness. Keep blocks
   strictly above both gates for the final energy mean. Convert the means to
   LUFS after averaging power. Recompute both passes from block history when
   the programme grows. Leave an incomplete last block out of I.
5. Report an incomplete measurement separately from an empty absolute gate.
   Preserve the distinction between a zero-energy window and a finite value
   below the gate. Treat a display floor as a presentation choice. For a seek,
   gap, overlap, or change of tap, rate, format or layout, start a fresh epoch.
   Preserve missing-input provenance and keep any intentional silence explicit.
6. Verify the measurement against [published fixtures](../../tests/fixtures/AUDIO_PROGRAM_LOUDNESS_OFFICIAL_GOLDENS.md)
   and an independent implementation. Check anti-phase stereo, LFE-only input,
   exact gate boundaries, callback segmentation and a changing relative gate.
   Report the standard edition, tap, sample span, layout, result state, and
   which tests support the claim. Keep workflow tolerances separate from meter
   test tolerances.

## Resources

- Use the [standard-library reference](scripts/reference_program_loudness.py)
  as a deterministic oracle for normalized planar PCM. The contract includes
  an invocation example. The reference implements M/S/I. Full EBU Mode also
  requires other measurements and meter behavior, including LRA and true peak.
- Run the [fixture checker](scripts/check_ebu_loudness.py) with the original
  EBU Loudness Test Set v5.0 ZIP for an offline check of cases 1–14.
- Use [channel mapping](../audio-channel-mapping/SKILL.md) to resolve speaker
  identities, [sample formats](../audio-sample-formats/SKILL.md) for PCM
  scaling, [timebase sync](../audio-timebase-sync/SKILL.md) for discontinuities,
  and [analysis provenance](../audio-analysis-provenance/SKILL.md) for reporting.
- Use [sample peak](../audio-sample-peak/SKILL.md) or
  [true peak](../audio-true-peak/SKILL.md) when peak headroom matters. The
  bundled true-peak reference is experimental.
