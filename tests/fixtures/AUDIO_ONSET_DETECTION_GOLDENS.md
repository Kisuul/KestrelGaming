# Audio onset detection fixtures

Use 48 kHz unless another rate is given. Record the onset definition,
channel, grid, score source, and input availability with the result.
[Contract](../../skills/audio-onset-detection/references/ONSET_DETECTION_CONTRACT.md) ·
[Regression checks](../test_audio_onset_detection_reference.py)

## Signal and feature fixtures

For the tone rows, use two contiguous rectangular frames with
$M=N=H=480$. Tone $k,a$ means $a\cos(2\pi kj/480)$ on one
frame. Use lag one, unit weights, and radius one for filtered flux.
Compare the direct STFT path within $3\times10^{-13}$ amplitude flux
and $2\times10^{-15}$ RMS for these levels.

| Earlier frame | Current frame | Plain flux | Filtered flux | Positive RMS change |
| --- | --- | ---: | ---: | ---: |
| Tone $8,0.5$ | Tone $9,0.5$ | 0.5 | 0 | 0 |
| Tone $8,0.5$ | Tone $12,0.5$ | 0.5 | 0.5 | 0 |
| Tone $8,0.6$ | Tone $8,0.6$ plus $9,0.2$ | 0.2 | 0 | 0.0229495268 |
| Tone $8,0.5$ | Tone $8,0.25$ | 0 | 0 | 0 |
| Tone $8,0.5$ | Tone $8,0.75$ | 0.25 | 0.25 | 0.1767766953 |

With rectangular odd and even transforms $N=M=7,8$, add DC 0.125
to a cosine of amplitude 0.25 at the highest positive bin. Recover
0.125 at DC and 0.25 at the highest bin in both cases. The highest
odd bin is paired. The even Nyquist bin is unpaired.

With $w=[0,1/4,3/4]$ and $x=[100,1,3]$, the weighted RMS is
$\sqrt{8.2}$. In an inverted stereo pair, check positive novelty
in each source channel and measured zero in the equal-weight mix.
Check a silent pair of complete frames for unavailable then zero.
Check incomplete tails, wrong grid or clock, gaps, and nonfinite
inputs. With two maximum-finite PCM values on a two-point rectangular
FFT, the shared STFT overflows. With one minimum-subnormal PCM
value on that grid, both calibrated bins round to zero. Both cases
give a range failure. Two minimum-subnormal values retain a
nonzero DC bin and weighted RMS.

## Peak, readiness, and replay

| Fixture | Expected result |
| --- | --- |
| Scores $[\mathrm{NA},0,0,4,4,1,0,5,0,0,0]$, $H=240$, $a=1$, $b=2$, $B=2$, $\delta=0.5$. | Frames 3 and 7 qualify at $R=960$. At $R=961$ only frame 3 qualifies. If the last two scores are absent, frame 7 is pending. |
| Unit impulse at 4440 in 7200 samples. Periodic Hann, $M=N=960$, $H=240$, $L=1$, $a=1$, $b=2$, $B=4$, $\delta=0.01$. | Peak frame 16 starts at 3840. Its center is 4319.5, or 2.510417 ms early. Earliest readiness is 5280, or 17.5 ms after the impulse. No confirmed peak at boundary 5279. |
| Replay the impulse at origin $2^{60}+37$ with different callback partitions. | All 27 frame centers, scores, and the earliest ready sample agree. The observed release varies with the first callback end at or beyond 5280 relative to the origin. |
| Reset to a new epoch after a valid detection. | Warm-up is unavailable again. The old background and minimum-separation state are clear. |

The impulse oracle supplies $A_{t,k}=d_k w[4440-s_t]/\sum w$
and $E_t=w[4440-s_t]/\sqrt{\sum w^2}$ for frames that contain the
impulse, with zero elsewhere. Use the periodic Hann
$w[j]=(1-\cos(2\pi j/M))/2$. The fixture exercises the larger
calibrated-feature entry point. The bounded PCM tests exercise
actual STFT replay with different block divisions.

For an independent slow-attack check, use 12,000 samples of
$0.5\sin^2(\pi u/2)\cos(2\pi 1000j/48000)$, where
$u=\min(1,\max(0,(j-4440+1)/3840))$. With the impulse grid,
the largest RMS rise is centered at 6479.5, 42.489583 ms
after sample 4440.

For an independent vibrato check, let $t=j/48000$ and synthesize
$0.5\cos(2\pi 1000t+(28/5)(1-\cos(2\pi 5t)))$ for two seconds.
Use periodic Hann $M=N=2048$, $H=240$, and $L=1$. Across 391
supported comparisons, the 95th percentile goes from 0.097353
to 0.031076 with radius one. Test the weak neighbor separately
before using the radius for detection.
[Research construction and independent FFT results](../../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-21-audio-onset-detection-research-r01.md#executed-checks-and-portable-fixtures)

## Matching

For reference times $[100,140]$ ms and detections $[125,160]$ ms,
use 25 ms tolerance. Both pairs match. Their signed errors are
25 and 20 ms. For label 1000 ms and detections 990 and 1010 ms
at 20 ms tolerance, the earlier occurrence matches. The signed
error is $-10$ ms, $TP=1$, $FP=1$, $FN=0$, and $F_1=2/3$.
Keep duplicate observations distinct, and compare exact doubled
sample positions at the interval and tolerance boundaries.
