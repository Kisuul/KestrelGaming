# THD and THD+N fixture values

## Coherent power

Use 480 samples at 48 kHz with a rectangular window and
no padding. Start at sample $2^{60}+37$. The width is
100 Hz. For local sample $0\le n<480$ set

$$
x[n]=0.05
+0.5\cos(2\pi\,10n/480)
+0.005\cos(2\pi\,30n/480)
+0.002\cos(2\pi\,17n/480).
$$

The analytic component powers in squared PCM units are
$0.0025$ at DC, $0.125$ at bin 10, $0.0000125$ at
bin 30, and $0.000002$ at bin 17. Use fundamental bin
10, orders 2 through 24, and band endpoints that
include all positive bins. Exclude DC.

| Expected output | Value |
| --- | --- |
| $P_1$ | $0.125$ |
| $P_D$ | $0.0000125$ |
| $P_R$ | $0.0000145$ |
| $P_B$ | $0.1250145$ |
| THD | $-40$ dB |
| Fundamental-relative THD+N | $-39.355420108$ dB |
| Total-relative THD+N | $-39.355923860$ dB |

The 1,700 Hz spur contributes to the residual. Use the
longer 4,800-sample fixture and 1,370 Hz spur in the
research handoff for a separate spectral implementation.
Both spans give the powers above.
[Research fixture](../../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-26-audio-thd-thdn-research-r01.md#executed-checks-and-portable-fixtures)

| Change | Expected result |
| --- | --- |
| Enable DC with zero in the band. | Add $0.0025$ to $P_R$ and $P_B$. Keep $P_D$ and $P_1$. |
| Set the band to [1,000, 1,700] Hz. | Both edge bins enter. The third order is out of band. $P_D=0$ and $P_R=0.000002$. |
| Add a 12,500 Hz cosine with peak 0.2. | The line contributes 0.02 to the full positive-band residual. A [400, 5,000] Hz band gives the original residual. |
| Use only a fundamental and a coherent nonharmonic line at equal peak levels. | $P_R=P_1$. The fundamental-relative result is 0 dB and the total-relative result is $-3.010299957$ dB. |
| Use peak 0.5 at bin 10 and peak $2^{-32}$ at bin 30. | $P_1=0.125$. $P_D$ and $P_R$ are approximately $2^{-65}$. Binary64 rounding gives equal totals for $P_B$ and $P_1$. |
| Use only the fundamental bin as the band. | The three ratios have zero numerator and give $-\infty$ dB. |
| Use silence, a DC-only capture, a band excluding the fundamental, or a floor above $P_1$. | Ratios are unavailable. Preserve the measured powers and qualification status. |
| Set the positive floor to the measured $P_1$. | The fundamental qualifies. |

## Endpoint and alias checks

At 48 kHz with 480 frames, use interior tones at 8 and
16 kHz with peaks 0.5 and 0.005, and an alternating
Nyquist sequence with peak 0.003. Orders 2 and 3
contribute $0.0000125$ and $0.000009$ respectively.
The fourth order is 32 kHz and has possible fold bin
160, which is also the second-order bin. The admitted
distortion is $0.0000215$, with THD about $-37.6447$ dB.

At $F_s=48{,}000{,}000/1{,}001$ Hz and $N=253$,
use fundamental bin 42 and a cosine in bin 126 with
peak 0.006. The highest bin is paired and contributes
$0.000018$ at order 3. Its frequency is exactly
$126F_s/253$, below $F_s/2$. A band consisting only
of that exact frequency admits it.

## Off-bin rejection probes

Use 4,800 frames at 48 kHz. Generate a 1,002.5 Hz
sine with peak 0.5 and phase 0.37 rad. Divide the
residual RMS by the input RMS for each projection.

| Projection removed | Residual RMS ratio |
| --- | --- |
| The sine and cosine of bin 100 (1,000 Hz). | Approximately 0.43474928946 |
| The sine and cosine at 1,002.5 Hz. | Below $3\times10^{-15}$ |
| The sine and cosine at 1,003 Hz. | Approximately 0.0903791 |

Add a 1,015 Hz sine with peak 0.002 and phase $-0.8$
rad. Removing the fitted 1,002.5 Hz line leaves over
95% of the spur's power. Compare to the residual of
applying the same projection to the spur alone.

Use a 57-frame span with
$u[n]=0.5\sin(2\pi\,1002.5n/48000)$ and
$v[n]=0.12\cos(2\pi\,2005n/48000-0.8)$.
Removing $u$ from their sum leaves $v$. The combined
mean square exceeds the sum of the individual powers
by $2\operatorname{mean}(uv)\simeq0.0061461272$.

Use a coherent 1,000 Hz sine at peak 0.5 and 4,800
frames. With a rectangular PSD, the calibrated center
bin holds 0.125 at DFT length 4,800 and 0.0625 at
length 9,600. Both grids integrate to 0.125 across
the full one-sided spectrum of the same record.
[Executable checks](../test_audio_thd_thdn_reference.py)
