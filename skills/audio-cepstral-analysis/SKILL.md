---
name: audio-cepstral-analysis
description: Compute or audit the real cepstrum and a liftered spectral envelope from raw FFT magnitudes. Use to inspect repetition candidates, diagnose spectral nulls and parity errors, or explain how a lifter changes the envelope.
---

# Audio cepstral analysis

Use this skill to inspect periodic structure in log magnitude or to smooth
a magnitude envelope. For phase recovery, pitch tracking, or MFCCs, use the
measurement method for that task.

1. **Trace the frame.** Select one original frame and channel. Record the tap,
   window, detrending, sample rate, observation length, FFT length, hop, and
   exact sample interval. Use the unnormalized DFT magnitudes on a common
   linear scale. Check any one-sided amplitude conversion at its endpoints.
   [FFT calibration](../audio-fft-spectrum/SKILL.md)
2. **Declare the logarithm policy.** State the positive magnitude reference.
   Use natural logs. With a strict policy, mark a spectrum with an exact null
   unavailable. With a relative floor, record the factor and affected bins.
   Report a valid zero frame as silent. Check whether a near-null comes from
   the signal, the window, or finite arithmetic.
   [Floor and null contract](references/CEPSTRAL_ANALYSIS_CONTRACT.md#nulls-and-flooring)
3. **Keep the original FFT length.** Include DC once. Include even-length
   Nyquist once. At odd length, mirror the final packed bin. Divide the
   inverse by the original FFT length. Preserve the sign of each coefficient.
   [Parity and transform](references/CEPSTRAL_ANALYSIS_CONTRACT.md#real-cepstrum)
4. **Interpret the quefrency.** Use $q/f_s$ for a delay and $f_s/q$ for a
   repetition candidate at $q>0$. Choose a search range supported by the
   observed frame. Verify an echo or periodic source with other evidence.
   Padding extends the circular transform. Use the observed sample interval
   to assess support. [Sample-clock rules](../audio-timebase-sync/SKILL.md)
5. **Smooth the envelope.** Keep both sides of the chosen low-quefrency
   range. Count a retained even midpoint once. Recover the log envelope
   with the forward transform. Keep the log result when a linear
   reconstruction exceeds the numeric range.
   [Envelope contract](references/CEPSTRAL_ANALYSIS_CONTRACT.md#spectral-envelope)
6. **Verify the convention.** Check an impulse, a signed echo, and a
   gain change on a prepared frame. Compare odd and even transforms
   with identical packed bin counts. Use a known log spectrum to test a lifter.
   [Analytic fixtures](../../tests/fixtures/AUDIO_CEPSTRAL_ANALYSIS_GOLDENS.md)

Use the [offline reference](scripts/reference_cepstral_analysis.py) for small
frame calculations. Report the window, transform length, floor, quefrency
range, and lifter cutoff with the result.
