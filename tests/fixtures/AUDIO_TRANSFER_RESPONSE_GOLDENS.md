# Transfer response fixture values

## Noise at the input or output measurement

Use 48 kHz, nonoverlapping rectangular windows, no
padding, and no detrending. Place the capture at sample
$2^{60}+37$ and use local offsets for the stimuli.

| Probe | Expected result |
| --- | --- |
| Use two 32-frame reference windows with impulses of 0.25 at offset 2. Use output impulses of 0.75 and 0.25 at the same offsets. | H1 is 2, H2 is 2.5, and coherence is 0.8. Both output errors sum to zero in the cross measure. |
| Use two 16-frame windows with cosine input peaks 0.375 and 0.125 at bin 4. Use a sine of peak 0.5 at bin 4 in each response. | At bin 4, H1 is $-1.6j$, H2 is $-2j$, coherence is 0.8, and phase is $-\pi/2$. |
| Reverse the taps in the input-error fixture. | H1 is $0.5j$, H2 is $0.625j$, phase is $\pi/2$, and coherence is 0.8. |
| Set a cross-density floor equal to the magnitude at bin 4 in the input-error fixture, then double the floor. | At equality H2 qualifies. Doubling the floor leaves H1 qualified and gives H2 status \`weak_cross\`. Both retain their raw values. |

On common nonzero support, compare H1 with H2
multiplied by coherence. This checks the exact ratio
in these fixtures. Check the signed phase separately.

## Delay and support

In each of two 256-frame segments put a unit reference
impulse at offset 32 and a response impulse of peak 0.25
at offset 39. Add 17 trailing samples after the second
segment. The used interval ends at offset 512 and the
full capture ends at 529. Expect
$0.25\exp(-j2\pi 7k/256)$ at all 129 nonnegative bins,
and a delay of seven samples or $7/48{,}000$ seconds.
The same data with one complete segment gives warm-up.

Advance the response by three samples to offset 36.
Retain the original tap support and specify the positive
advance to the group-delay procedure. The measured slope
gives four samples. The restored delay is seven samples.

## Bin states and numerical range

| Probe | Expected result |
| --- | --- |
| Use the pulse at offset 32 as reference and response taps of 0.5 at offsets 32 and 33. | DC gain is one. At even Nyquist H1 is exactly zero and H2 is unavailable. Phase and coherence are unavailable. |
| Repeat the reference in two segments and invert only the second response. | Both auto densities are positive and the cross density is zero. H1 is zero, H2 is unavailable, and coherence is zero. |
| Use a zero reference and an energetic response. | Retain the output density. Both estimates have status \`unexcited\` and are unavailable. |
| Use two complete windows with energy in only the first pair and both planes zero in the second. | The bin has coherence one and one energized pair. The default two-pair gate rejects qualification and keeps the estimate. |
| Use two repeated 8-frame impulse pairs with one plane at the smallest positive binary64 value and the other at the largest finite value. Swap the two levels in a second capture. | Both directions retain the exact gain and coherence one. The linear binary64 magnitude is unavailable and the dB levels are about $\pm12{,}631.218618$. |

[Executable checks](../test_audio_transfer_response_reference.py) ·
[Research fixtures](../../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-26-audio-transfer-response-research-r01.md#executed-checks-and-portable-fixtures)
