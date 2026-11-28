# Noise, SNR, and SINAD fixture values

## Coherent driven powers

At 48 kHz use 480 frames with local offset zero at
sample $2^{60}+37$. Use a rectangular record and no
padding. Add DC 0.05 to a 1,000 Hz sine at peak 0.5,
a 3,000 Hz sine at peak 0.005, and a 1,700 Hz cosine
at peak 0.002. Exclude DC and assign the third
harmonic to distortion.

| Quantity | Value |
| --- | ---: |
| $P_S$ | 0.125 |
| $P_D$ | 0.0000125 |
| $P_N$ | 0.000002 |
| $P_X$ | 0 |
| $P_R$ | 0.0000145 |
| $P_B$ | 0.1250145 |
| SNR | 47.9588001734 dB |
| SINAD | 39.3554201077 dB |

The longer research record uses 4,800 frames and a
1,370 Hz spur. The line peak and admitted powers
match the short record.
[Research fixtures](../../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-26-audio-noise-snr-sinad-research-r01.md#executed-checks-and-portable-fixtures)

| Change | Expected output |
| --- | --- |
| Add a 2,100 Hz sine at peak 0.001. Then exclude the 1,700 Hz line from SNR. | $P_N$ goes from 0.0000025 to 0.0000005. The mask puts 0.000002 in $P_X$. SNR goes from 46.9897000434 to 53.9794000867 dB. Both cases have $P_R=0.000015$ and SINAD 39.2081875395 dB. |
| Add a 12,500 Hz cosine at peak 0.2. | The full positive band gives $P_N=0.020002$. With [400, 5,000] Hz the noise power is 0.000002. Both reports retain the added line's raw power. |
| Use peak 0.5 at 1,000 Hz and peak $2^{-32}$ at 1,700 Hz. | Direct noise power is about $2^{-65}$. The individually rounded $P_B$ and $P_S$ subtract to zero. |
| Use equal fundamental and residual powers. | SINAD is 0 dB and total-relative THD+N is −3.0102999566 dB. |
| Admit only the qualified fundamental bin. | Both denominators are zero, with SNR and SINAD $+\infty$ dB. |
| Supply a qualified fundamental and a harmonic with no admitted noise bins. | SNR is $+\infty$ dB and SINAD is finite. |
| Exclude the fundamental via band or floor. | The measured powers remain available and both ratios are unavailable. |

## Noise power and support

Use a 480-frame impulse at 48 kHz with peak
$\sqrt{10^{-7}480^2/2}$. The interior bin density is
$10^{-9}$ squared PCM units per Hz. Bands
[50, 1,050] Hz and [50, 2,050] Hz admit 10 and 20
centers. Their powers are $10^{-6}$ and
$2\times10^{-6}$, a 3.0102999566 dB difference.

For equal-duration powers $10^{-6}$ and $10^{-4}$,
use their mean $5.05\times10^{-5}$. Relative to unit
power this gives −42.9670862188 dB. Averaging the
two displayed levels gives −50 dB.

Use the fixture bank's \`seeded_noise\` at 48 kHz,
256 samples, seed 470047, and amplitude 0.05.
The full mean square is 0.0008130940426452365.
Excluding DC gives 0.0008062456564285143.
The quiet report has no signal numerator.

Use three complete 128-sample periodic Hann windows
on the quiet record with hop 64 and detrending disabled.
The average of the three window-energy-normalized time
powers is 0.000796486372634173. Welch integration gives
that same power at 128 and 256 DFT points, within the
precision of the reference.

## Quantizer counterexample

Render a coherent 1 kHz sine at 48 kHz and peak 0.2
quantizer steps. Round each sample to the nearest step.
All output samples are zero, and error equals the negative
input. The error power is 0.02 steps squared. A driven
measurement of the output has an unavailable signal
reference. The uniform model's mean square is $1/12$
steps squared.
[Executable checks](../test_audio_noise_snr_sinad_reference.py)
