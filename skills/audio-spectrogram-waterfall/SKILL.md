---
name: audio-spectrogram-waterfall
description: Design, implement, and audit calibrated time-frequency spectrograms and waterfalls with sample-accurate STFT frame timing, window and hop semantics, traceable magnitude/PSD scaling, honest color axes, and bounded history.
---

# Audio spectrogram and waterfall — an honest signal history

## Activate when

Load for STFT time-frequency displays, scrolling waterfalls, spectrogram axes and color mapping, time-frequency ridge/transient interpretation, or diagnosing audio-history drift. Do **not** load for a single-frame spectrum or generic audio playback UI. Consult [audio-dsp-core](../audio-dsp-core/SKILL.md) if ingestion/discontinuity policy is changing; [audio-window-functions](../audio-window-functions/SKILL.md) for window choice; [audio-fft-spectrum](../audio-fft-spectrum/SKILL.md) for peak-amplitude bins; and [audio-power-spectral-density](../audio-power-spectral-density/SKILL.md) for density units and one-sided power scaling.

Read [the time-frequency and rendering contract](references/STFT_WATERFALL_CONTRACT.md) before choosing timestamp and color semantics.

Consult [math-dimensional-analysis](../math-dimensional-analysis/SKILL.md) when checking sample-clock, seconds and frequency-axis conversions, and [math-verification](../math-verification/SKILL.md) when defining independent STFT timing and calibration comparisons. Load only the relevant procedure; a rectangular output array alone does not require matrix-algebra guidance. Frame placement, transform normalization, density units and rendering/gap semantics remain defined by the audio contracts.

## Procedure

1. **Trace the analysis tap and owner of time.** Identify audio origin, sample rate, channel scope, source/gain position, resampling, transport seek and stream resets. Use absolute sample positions (or a documented monotonic sample clock) for frames; rendering refresh timestamps are never a substitute for audio sample time.
2. **Define each analysis frame explicitly.** Record sample-window length M, FFT length Nfft >= M, hop H in samples, window variant and coefficients, pre-window detrending, frame start, end-exclusive, and nominal center; specify boundary padding/partial-frame handling. In the no-padding convention of the [reference fixtures](references/STFT_WATERFALL_CONTRACT.md), frames start at 0, H, 2H ... and only complete windows are emitted, with center at start + (M-1)/2. Libraries may use centered frames and boundary padding instead; align conventions rather than assuming equal indexing.
3. **Name the measured ordinate.** An unnormalized complex STFT, one-sided calibrated *peak-amplitude* bins, a power spectrum, and a one-sided PSD are different quantities. Amplitude uses a coherent-gain correction proportional to 1/sum(w); PSD uses 1/(fs*sum(w²)), with paired positive-frequency **power** bins doubled. State normalization and reference; no generic “dB” label without units and reference.
4. **Build a sample-time matrix.** The frequency coordinate for a one-sided real transform is k*fs/Nfft. The time coordinate should be in sample numbers and seconds derived from fs; frame centers may be half-integers for even M. The reference's integer `center_sample_twice` preserves exact centers at large origins; its floating center/seconds fields may round. Overlap changes frame cadence but does not create new independent data or improve the intrinsic frequency resolution. Zero padding increases displayed frequency-grid density, not the true resolving power.
5. **Make resets and gaps visible.** On underrun, discontinuous capture, seek, source change, sample-rate change or analysis-configuration change, create a discontinuity marker or an explicitly new epoch. Never silently join unrelated frames, synthesize valid-looking zero/silence columns for missing input, or reuse old columns under new calibration. Paused streams stop advancing sample-based history.
6. **Keep raw observations separate from rendering.** Store calibrated linear amplitude/power/density and configuration metadata for as long as required; apply dB conversion, clipping, color mapping, interpolation and display floors only in the UI layer. For amplitude ratios use 20 log10; for PSD or power ratios use 10 log10. Zero may render at a declared floor; it is not a finite measured negative dB value.
7. **Budget the waterfall deliberately.** Bound history by duration, sample-time domain and memory; specify row/column aggregation if pixels are fewer than bins or frames. Do not average logarithmic dB values and claim an average physical power. Label frozen views and dropped-history regions; enforce monotonic time axis even when rendering frames are skipped. Handle logarithmic frequency displays specially at DC (f=0 cannot be placed on a log axis).
8. **Test synthetic time-frequency behavior.** Compare silence, coherent tone ridges, frequency steps, an impulse at a known sample, off-bin leakage, odd/even FFT lengths, zero padding, overlap, incomplete tails, and configuration resets. Partition identical samples into different source callback chunks and assert identical frame values and timestamps. Use the deliberately slow [reference STFT](scripts/reference_stft.py) and [regression tests](../../tests/test_audio_stft_reference.py); these validate mathematics, not real-time GUI performance.
9. **Audit the visual truth contract.** Verify time/frequency axis tick positioning, source-channel labels, colorbar units/reference/floor/range, zoom and auto-range behavior, log frequency DC handling, and the history update cadence. Compare a rendered row/column to the numerical data at a known timestamp rather than accepting a convincing-looking heatmap.
10. **Report what is verified.** Retain fixtures, measured results/tolerances, transform configuration, display choices and performance budget. Separately identify unverified device calibration, production workloads, GPU/CPU costs, reconstruction/invertibility, and instrument/standard compliance. Follow [Kestrel verification](../../kestrel/VERIFICATION.md).

## Acceptance gate

A spectrogram/waterfall is reviewable when sample-window placement, complete/tail/boundary handling, FFT and density normalization, time/frequency axes, color reference, reset/gap behavior and history bounds are documented, and deterministic fixtures have been run against an independent expectation. Rendering fidelity must be inspected in the actual target app before any complete-product claim.

## Authoritative reading

- [SciPy ShortTimeFFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.html) — time/frequency grids, hop, centering, padding, and transform modes.
- [SciPy ShortTimeFFT.spectrogram](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.spectrogram.html) — a spectrogram is the squared magnitude of an STFT; cross-spectrograms differ.
- [SciPy legacy spectrogram API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.spectrogram.html) — exposes boundary, segment and density choices; *legacy* rather than a default for new implementations.
- [Julius O. Smith, Spectral Audio Signal Processing](https://www.dsprelated.com/freebooks/sasp/) — STFT windows, leakage, hop and time/frequency tradeoffs.
