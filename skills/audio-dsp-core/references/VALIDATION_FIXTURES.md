# Baseline audio DSP fixtures and acceptance evidence

Reference for [audio-dsp-core](../SKILL.md). Fixtures are **specifications for tests to write/run**, not evidence that any implementation already passed.

## Deterministic numerical fixtures

| Signal | Essential checks |
| --- | --- |
| All-zero digital silence | Peak = RMS = mean square = 0; mathematical log-level negative infinity or explicit invalid/log policy; no NaN |
| Constant +0.25 | Peak = RMS = 0.25; mean square = 0.0625; DC spectral handling |
| Alternating +0.25/-0.25 | Same mean square and RMS as constant; distinct spectral content |
| Single +1 impulse in N samples | Peak = 1; RMS = 1/sqrt(N); mean square = 1/N; FFT window placement matters |
| On-bin 1.0 peak sine | Peak near 1 where sampled extrema permit; RMS near sqrt(1/2) for integral periods; interior FFT bin scaling |
| Off-bin sine | Leakage and scalloping loss visible; no unqualified exact-peak-bin claim |
| Two known sinusoids | Frequency placement and amplitude separation; characterize leakage |
| Seeded broadband noise | Reproducible PSD statistics and averaging; tolerance accounts for randomness |
| Anti-phase stereo (+s,-s) | Each channel has nonzero RMS; aggregate energy is not zero |
| Same-phase stereo (+s,+s) | Channel policy documented; no silent double counting |
| Non-finite sample | Documented reject/flag/contain policy; no poisoning of later frames |

Use independent expectation calculations or a separate established implementation, not duplicated production formulas masquerading as an oracle.

## Stream and temporal fixtures

- Split the same contiguous signal into different callback block sizes and verify identical numerical frames and sample timestamps.
- Pause/resume, seek, stream restart, sample-rate change, channel-layout change, and FFT-size/hop change: assert expected reset behavior.
- Force a bounded buffer overrun; assert a discontinuity marker, no false silence, and recovery after restart.
- Exercise threshold crossing, hysteresis, attack/release/hold, near-threshold noise, and repeated rapid crossings for energy detectors.
- Test all supported sample rates, window sizes, and channel modes; use boundary sizes including empty input when applicable.
- Confirm render cadence does not influence computed results.

## Evidence to retain

For each fixture report: input generation parameters, sample rate, channel layout, algorithm version/configuration, expected value, tolerance, observed result, environment, and pass/fail. For realtime tests report worst-case callback duration, target budget, and overflow behavior; avoid publishing an unmeasured performance claim.

A synthetic fixture is not evidence of physical-device calibration, standardized loudness compliance, instrument-class accuracy, or suitability for safety-critical measurements.
