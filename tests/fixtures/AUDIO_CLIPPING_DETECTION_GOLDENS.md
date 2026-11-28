# Audio clipping detection goldens

[Executable checks](../test_audio_clipping_detection_reference.py) ·
[Contract](../../skills/audio-clipping-detection/references/CLIPPING_DETECTION_CONTRACT.md)

## Sample evidence

Use signed 16-bit codes
`[0,32767,32767,32767,0,-32768,-32768,0,32766,32767,32766,0]`
at origin $O=2^{60}+37$. Compare one block with blocks of
2, 3, 1, and 6 frames. Expect four positive contacts, two
negative contacts, and zero exceedances. For the two-sample
plateau rule, add $O$ to each reported index below.

| Polarity | Observed span | Plateau-ready frontier | End-confirming frontier |
| --- | --- | ---: | ---: |
| Positive | $[1,4)$ | 3 | 5 |
| Negative | $[5,7)$ | 7 | 8 |
| Positive | $[9,10)$ | Absent | 11 |

| Probe | Expected evidence |
| --- | --- |
| End an accepted block at sample 11 after a positive contact at 10. Try a block at 12. | Reject the gap with frontier 11. Start a new epoch at 12. A new positive contact at 12 gives separate runs $[10,11)$ and $[12,13)$. Both have absent end confirmation and plateau readiness. |
| Follow two positive rails immediately with two negative rails. | The first negative rail gives both the exclusive end of the positive run and the start of the negative run. |
| Set a 300-sample plateau rule and accept 256 then 100 positive contacts. | The run qualifies at frontier $O+300$. Its observed end after the second block is $O+356$. |
| Decode `00 00 80 F0 FF 7F` as signed 24-bit little-endian PCM with 20 valid bits. | Expect centered codes $-524288$ and $524287$. Their normalized values are $-1$ and $0.9999980926513672$. |
| Feed floats `[0.8,1,1.125,1.25,1,-1.25,-1,0]` with references $\pm1$. | Three contacts and three strict exceedances. The positive excess run is $[2,4)$ with extreme $1.25$. The negative excess run is $[5,6)$ with extreme $-1.25$. |
| Use references $-0.5$ and $0.75$. Let $l$ and $h$ be the adjacent representable values outside them. Feed $(-0.5,l,-0.875,l,0.75,h,0.75)$ as one block and in blocks of 2, 1, and 4. | The negative run is $[1,4)$ with extreme $-0.875$. The positive run is $[5,6)$ with extreme $h$. The counts are three negative and one positive excess, with one negative and two positive contacts. |

## Conversion evidence

Encode `[0,32767/32768,32767/32768,0]` and
`[0,1.125,1.125,0]` with the reference signed 16-bit
encoder. The first reports zero saturations and the second
reports two. Both produce bytes `00 00 FF 7F FF 7F 00 00`
and the same observed rail run $[1,3)$.

| Input | Output code | Encoder saturations | Strict reference exceedances |
| --- | ---: | ---: | ---: |
| $32767/32768$ | 32767 | 0 | 0 |
| $1-2^{-17}$ | 32767 | 1 | 0 |
| $1$ | 32767 | 1 | 0 |
| $-1$ | -32768 | 0 | 0 |
| $-(1-2^{-17})$ | -32768 | 0 | 0 |
| $-(1+2^{-17})$ | -32768 | 1 | 1 |

At $1-2^{-17}$ the reference encoder rounds to 32768 before
saturation. It treats every input below $-1$ as overflow. Pure
nearest-code rounding in the last row gives the valid code
$-32768$. The saturation count describes the stated encoder policy.

## Waveform evidence

**Soft saturation.** At 48 kHz, generate
$y[n]=0.8\tanh(2\sin(2\pi\,1000n/48000))$ for 480 frames.
The maximum sample magnitude is $0.7712220640606535$.
The 3 kHz component has peak amplitude $0.1509938598164597$.
The float detector at $\pm1$ observes zero contacts and no
excess runs. Compute the harmonic amplitude from the coherent
single-sided bin power as $\sqrt{2P_3}$.

**Intersample exceedance.** The ideal periodic waveform
$1.1\sin(\pi F_s t/2+\pi/4)$ has continuous peak magnitude
$1.1$. Its samples repeat $(a,a,-a,-a)$ with
$a=1.1/\sqrt{2}\approx0.7778174593$. Use 256 samples at
48 kHz. The $\pm1$ float detector observes no sample
exceedance. The experimental 8× Lanczos estimate with
radius 32 is $1.100022630568014$ on the supported interior.
The full finite-record estimate is $1.111405025195615$ at a
boundary. Preserve the support label with either estimate.
