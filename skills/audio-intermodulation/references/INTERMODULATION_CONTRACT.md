# Coherent two-tone intermodulation

[Stimulus](#capture-and-stimulus) · [Product assignment](#product-assignment) ·
[Bin power](#bin-power) · [Carrier references](#carrier-references) ·
[Verification](#verification)

## Capture and stimulus

Record both stimulus frequencies, peak levels, phases,
source tap, output tap, channel, and sample-clock support.
Keep the drive and gain settings. Check for clipping and
capture gaps. Measure the source or a linear loopback
through the same measurement path at a comparable level.
Source products limit what the output measurement can
attribute to the device.

Use a complete capture with a rectangular window and
DFT length equal to its frame count $N$. Supply two known
carrier bins with $0<k_1<k_2<N/2$. Select a declared channel
with \`measure_intermodulation\`. The offline reference uses
5 to 1,024 frames, keeps the half-open interval, and uses
the exact sample rate $F_s$ from the capture epoch.
[Capture contract](../../audio-oscilloscope/SKILL.md) ·
[Test signals](../../audio-test-signals/references/TEST_SIGNALS_CONTRACT.md#support-and-phase)

Choose the test for the behavior of interest. The Audio
Precision SMPTE-style example uses 60 Hz and 7 kHz with
a 4:1 low-to-high amplitude ratio and measures sidebands
referenced to the high tone. Its DFD example uses two
equal high-frequency tones and sums amplitudes. When
comparing to an instrument or standard, match the
selected products, weighting, aggregation, and reference.
[Audio Precision example methods](https://www.cieri.net/Documenti/Misure%20audio/Audio%20Precision%20-%20Automotive%20Audio%20Amplifiers%20Testing%20%282019%29.pdf) ·
[Analog Devices MT-012](https://www.analog.com/media/en/training-seminars/tutorials/mt-012.pdf)

## Product assignment

A mixed pair $(m,n)$ has both coefficients nonzero. Its
order is $|m|+|n|$. Its signed nominal bin is $s=mk_1+nk_2$.
Keep the signed bin and frequency $sF_s/N$ in the report.
Conjugate pairs $(m,n)$ and $(-m,-n)$ describe the same
real line. Declare each product once. For bin membership the
reference uses the representative with first nonzero
coefficient positive. The requested formula keeps its sign.

Set \`max_order\` to 2 or 3. Group all candidate pairs through
that order, including DC, both carriers, both sets of
individual harmonics, and the mixed pairs. Terms with the
same coefficient pair share one candidate. For example,
cubic terms can change the carrier level. Use the quadratic
family for a controlled square response and the cubic family
when cubic lines can reach the capture. The declared family
sets the scope of the isolation check.

| Sampling policy | Mapping when $2\lvert s\rvert>N$ |
| --- | --- |
| \`digital_fold\` | Map to $k=\min(r,N-r)$ with $r=s\bmod N$. Keep the possible fold bin and its observed power. |
| \`band_limited\` | Record the possible fold bin and omit this candidate from observed membership. Use this mode when filtering rejects the high product before sampling. |

When $2|s|\le N$, assign bin $|s|$ in both modes. A
negative frequency in this range is the conjugate partner
of a real line. It has no above-Nyquist fold.

Combine candidates by observed bin before checking
the measurement band. More than one distinct candidate
makes that bin ambiguous under the model. Keep its measured
power and membership. Relative phase changes the complex sum
in a collided bin. A change in carrier pair or rate can
separate the candidates. Use a longer capture when the
physical frequencies differ and the earlier window lacked
resolution. Use a different pair or sampling geometry for
an exact collision on the observed grid.

The line status is \`above_nyquist\` for a rejected candidate,
then \`collision\` for a shared bin, \`out_of_band\` outside
the declared band, and \`excluded_endpoint\` for a disabled
endpoint. A remaining line is \`resolved\`. The bin's
\`admitted\` flag records the band and endpoint decisions
even when the line has a collision. The ledger keeps every
bin, including bins with no model candidates.

## Bin power

Use one-sided power $p[k]=S_{xx}[k]F_s/N$ and bin
frequency $kF_s/N$. Use the peak conversion
$\sqrt{2p[k]}$ for a paired bin and $\sqrt{p[k]}$ for DC
and the even-length Nyquist bin. The highest odd-length
bin is paired. Nyquist's peak is the amplitude of the
sampled alternating sequence.

Give inclusive integer or rational band endpoints in Hz
between zero and $F_s/2$. The default is the complete band
with DC excluded and even Nyquist included. DC remains a
candidate when excluded. A mixed product that maps to DC
shares its bin with that candidate.

The PSD call uses a computational bin width of one. Scale
PCM by a common power of two before the DFT and restore
squared PCM units after it. Subtract the mean for AC bins and
retain the squared PCM mean at DC. In the rectangular
unextended transform, this separation is exact before
rounding. The ledger retains the represented powers as
fractions. AC precision depends on the binary64 DFT.
A peak beyond the binary64 range is unavailable while its
power stays in the ledger.
[PSD normalization](../../audio-power-spectral-density/references/PSD_CALIBRATION.md#normalization) ·
[THD bin-power example](../../audio-thd-thdn/references/THD_THDN_CONTRACT.md#capture-and-bin-power)

## Carrier references

Give \`ImdProfile\` the carrier bins, requested mixed pairs,
sampling policy, and ratio reference. Both measured output
carriers must be resolved, positive, and at or above the
declared power floor for this two-tone measurement. An
admitted carrier with zero power has status \`zero_power\`.
A positive carrier below the floor has status \`below_floor\`.
Choose a floor that reflects the source and measurement
limits. A low noise or leakage value in a carrier bin can
otherwise pass a zero floor.

| Ratio reference | Reference power $P_C$ | Level units |
| --- | --- | --- |
| \`low_carrier\` | Measured low carrier power | dBc |
| \`high_carrier\` | Measured high carrier power | dBc |
| \`both_carriers\` | Sum of measured carrier powers | dB |

Use the resolved bin power for a line numerator and the sum
of unique resolved requested bins for a group numerator $P_I$.
Return $\sqrt{P_I/P_C}$, $100\sqrt{P_I/P_C}$ percent, and
$10\log_{10}(P_I/P_C)$. Keep the numerator, reference power,
and requested membership. A qualified zero numerator gives
zero ratio and $-\infty$ dB. An unavailable carrier reference
withholds ratios and retains the available powers. A group
with any unresolved request has unavailable aggregate power
and ratio. Individual resolved lines keep their ratios when
the carrier reference is qualified. Select the desired
subset explicitly to measure a smaller group.

## Verification

Measure a linear control and separate quadratic and cubic
responses. Compare absolute product levels at two drive
settings. Recompute ratios from the measured carrier levels
at each setting. Test an exact band edge, an odd highest
bin and even Nyquist, a possible fold with and without
collision, and a carrier below the floor. Use a second rate
or a verified filter to test an attribution to aliasing in a
device measurement.
[Fixture values](../../../tests/fixtures/AUDIO_INTERMODULATION_GOLDENS.md)
