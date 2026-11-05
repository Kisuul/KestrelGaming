# Audio numerical stability — independent analytic fixtures

All cases use explicit **sample-unit** amplitudes, not automatically dBFS or SPL. Exact rational formulas are the source of expected values; [the bounded Python tests](../test_audio_numerical_stability_reference.py) are consumers of these cases. Decimal numbers in this document are illustrative; when testable, prefer exact powers of two and rationals.

| Case | Mathematical expected result | Naive finite-arithmetic failure | Required interpretation |
| --- | --- | --- | --- |
| Silence `[0,0,0,0]` | `RMS = 0` | Division by zero from scaling with `max=0` | True zero is valid, not missing data |
| DC `[1/4]*16` | `RMS=1/4` | None expected | Dimension: input sample units |
| Unit impulse `[1,0,0,0]` | `RMS=1/2` | `Σx²` should be normalized by N | Do not report a peak as RMS |
| Four-phase coherent sine `[0,1,0,-1]` | `RMS=1/sqrt(2)` | DFT convention confusion | No sample-timing extrapolation |
| `[2^1023]*4` | `RMS=2^1023` finite binary64 | Each squared term overflows | Scale *before* forming squares |
| `[1e-200]*4` | `RMS=1e-200` | Squared terms underflow to 0 | Nonzero measurement cannot silently become silence |
| Uniform 4-tap `w_i=1e-200` | `ENBW_bins=4*4u²/(4u)²=1` | `Σw_i²` underflows, apparent `0/0` | Scale cancels before any squaring |
| Rectangular 2-point real waveform `[2^512,2^512]`, `fs=48000 Hz` | `X[0]=2^513`, DC PSD `2^1026/96000` sample²/Hz `≈7.4903880619e303` | `|X|²` overflows, though final PSD fits | Do not clip, zero, or declare input invalid merely for huge synthetic amplitude |
| Rectangular N=4, window `[1]*4`, complex DFT bin X=4 | DC PSD = `1` and bin 1 PSD = `2` at `fs=4 Hz`; even Nyquist bin 2 PSD=`1` | Double-counting DC/Nyquist | Exact real one-sided factor and units |
| N=3 real spectrum X=3 and fs=3 Hz with w=`[1]*3` | k=1 PSD=2 (no Nyquist for odd N) | Treating floor(N/2) as an even-N Nyquist | Respect parity |
| N=4 rectangular, `X[1]=2^1023` | one-sided amplitude `2*2^1023/4=2^1022`, finite | Multiply by 2 before divide -> infinity | Scale before applying gain |
| PSD ordinates `[1e308,1e308]` | arithmetic mean = `1e308` | raw sum overflows | Only scale *comparable nonnegative PSD* |
| Signed sum `[2^54,1,-2^54]` | exact real sum 1 | left-to-right floating addition produces 0 | Distinguish cancellation from silence |
| Signed 8-bit quantize of `3/2` counts | nearest ties-even => 2 | Rounding policy ambiguity | Integer counts of one LSB, not physical amplitude |
| Signed 8-bit quantize of `-3/2` counts | nearest ties-even => -2 | truncation toward zero => -1 | State ties, sign, saturation policy |
| Signed 8-bit input 200 counts | saturate => 127; error => reject | wraparound yields -56 | Saturation never implicit |
| Unsigned 8-bit -1 counts | saturate => 0; error => reject | negative arithmetic treated modulo 256 | Declare unsigned range |
| binary64 value `2^24+1` to binary32 | rounds to `2^24` | precision loss not detected | Distinguish dtype with actual backend test |
| binary64 `2^-150` to binary32 | nearest ties-even rounds zero | silent nonzero-to-silence | Record loss/underflow status |
| Stable biquad denominator `1 -1.8 z^-1+0.9998 z^-2` | pole radius `sqrt(0.9998)<1` | coefficient quantize `a2` at 1/1024 to 1 makes poles marginal, radius=1 | Inspect *implemented* coefficients |
| Accumulator sample origin `2^54+7` | each accepted block advances exact integer coordinate | binary64 timestamps lose unit increments beyond 2^53 | Use integer sample indices/explicit epoch |

**Independent verification discipline:** Freeze the above before changing the reference. For each negative case, assert a meaningful failure (wrong final value, explicit exception or named underflow report), not merely that *some unrelated* validator rejects the whole test graph. Synthetic examples intentionally outside calibrated PCM range demonstrate arithmetic pathologies; they do not measure actual acoustic sound pressure or production sample levels.

**Limits:** The 1–256 sample oracle is not a replacement for target CPU/SIMD/fixed-point measurements, thread synchronization, DFT implementation validation or controlled agent-use A/B trials. The PCM `s16` to normalized sample conversion and reference window conventions are documented in their own Kestrel audio skills.
