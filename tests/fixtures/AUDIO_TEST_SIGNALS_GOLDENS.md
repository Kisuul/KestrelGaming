# Audio test signal fixtures

[Reference](../../skills/audio-test-signals/scripts/reference_test_signals.py) ·
[Contract](../../skills/audio-test-signals/references/TEST_SIGNALS_CONTRACT.md) ·
[Executable checks](../test_audio_test_signals_reference.py)

Use 48 kHz and origin $O=2^{60}+37$ unless stated. Use
phase in turns in the renderer. Set the active start to
$O$ unless a leading guard is specified. Compare integer
coordinates and same-runtime partitions exactly.

## Tone and level checks

| Probe | Expected evidence |
| --- | --- |
| Use 4,800 frames, bin 100, amplitude 0.5, phase zero, and a rectangular window. Render blocks of 97, 233, 1,024, 611, and 2,835. | The blocks exactly equal the full render. RMS is $1/(2\sqrt{2})$, and bin 100 gives peak amplitude 0.5. Converting absolute indices to binary64 first yields up to 0.9330 FS error in the sample sequence. |
| Set the frequency to $100.25 f_s/4800$ and phase to $1/14$ turn. | Bin 100 has amplitude about 0.450549219. Record RMS is about 0.353748532. About 18.89% of the one-sided power is outside bin 100. |
| At DC and Nyquist, set amplitude 0.5 and phase 0, $1/12$, or $1/4$ turn. Use 128 frames. | DC is constant at 0, 0.25, or 0.5, respectively. The Nyquist samples alternate in sign. At zero phase, all samples are zero. |
| Render bin 127 of an odd 255-sample frame with amplitude 0.5. | The last positive bin has peak amplitude 0.5 and the record has RMS $0.5/\sqrt{2}$. |
| Sum bins 100 and 137 at cosine phase with amplitudes 0.25 and 0.125. Repeat with bins 100 and 200 at cosine and sine phase. Use 4,800 frames. | Both cosine cases reach 0.375 at the first sample. The sine case reaches $3\sqrt{3}/16$. All three have RMS $\sqrt{5/128}$. |
| Request peak limit 1 with amplitudes 1 and $2^{-54}$. | The exact coefficient sum exceeds the limit. Binary64 addition alone rounds the sum to 1. Reject before rendering. |
| Use anti-phase stereo noise from the shared bank, 128 frames, seed 1,729, amplitude 0.5. | Channel RMS is about 0.285759892 on both lanes and the sum is identically zero. Preserve the seed and bank version. |

## Impulse response

Put a 0.5 impulse at offset 7 in a 128-frame active span.
Apply FIR coefficients `[0,0,0,1/2,-1/4,1/8]`.
The nonzero response samples at offsets 10, 11, and 12
are 0.25, −0.125, and 0.0625. The impulse RMS on its
active span is $0.5/\sqrt{128}$.

Move the impulse to offset 127. The output now has its
three nonzero samples at offsets 130–132. Retain five
additional response frames. In the generator the tail
guard is zero. At the response tap it contains the FIR
tail.

## Sweeps and tail checks

Use amplitude one, zero phase, and an unfaded 12,000-frame
active span from 100 to 8,000 Hz. Add a 7,200-frame block
to the tone's block sequence. The renders agree exactly.
The instantaneous frequency at sample 11,999 is
approximately 7,997.079182 Hz. The final active sample
value is approximately −0.2368885480470, from the
integrated phase. Reverse the endpoints and repeat
with phase $1/8$ turn. The final value is
approximately −0.8834233495378.

With endpoints 1,000 Hz and its next binary64 neighbor,
render 9,600 frames. The small phase increment survives
when `exp(z)-1` would round to zero. At offset 4,801, the
value is within $3\times10^{-13}$ of the coherent 1,000 Hz
tone and exceeds 0.1.

Convolve the up-sweep with the same six-tap FIR and use
16,384-point transforms. Compare $Y/X$ with the analytic
filter at 250–5,000 Hz where $|X|>1$ with the unnormalized
DFT. The full 12,005-sample response recovers the filter
to numerical precision. Dropping the five tail samples
produces about 0.00469 maximum complex error on these
bins.
