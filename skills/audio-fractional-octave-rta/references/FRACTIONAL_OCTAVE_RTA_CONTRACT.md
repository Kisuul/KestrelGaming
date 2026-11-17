# Fractional-octave RTA contract

The [reference](../scripts/reference_fractional_octave_rta.py) estimates per-channel
band power from normalized real PCM. It uses IEC 61260-1 base-10 frequency
geometry and a rolling arithmetic mean of complete modified periodograms.
RMS and dBFS are derived from band power. This is an offline educational model.

- [Frequency geometry](#frequency-geometry)
- [PSD integration and coverage](#psd-integration-and-coverage)
- [Streaming and arithmetic](#streaming-and-arithmetic)
- [Filter-bank measurements and IEC scope](#filter-bank-measurements-and-iec-scope)
- [Run the reference](#run-the-reference)

## Frequency geometry

Let $G=10^{3/10}$, $f_r=1000\ \mathrm{Hz}$, and $1/b$ be the bandwidth
designator. For integer band index $x$, the center $f_m$ is

$$
f_m = f_r G^{x/b}\quad(b\ \text{odd}), \qquad
f_m = f_r G^{(2x+1)/(2b)}\quad(b\ \text{even}).
$$

The lower and upper edges are $f_l=f_m G^{-1/(2b)}$ and
$f_u=f_m G^{1/(2b)}$. The center is their geometric mean. Equal fractions
have the same ratio $f_u/f_l=G^{1/b}$, so bandwidth in hertz grows in
proportion to the center. The reference implements $b\in\{1,3,6,12,24\}$.
IEC geometry applies to any positive integer denominator.

At 1 kHz the octave and third-octave families have a center. For the even
families, bands −1 and 0 share a 1 kHz edge. Use the exact
frequency formula for all calculations. For example, the nominal third-octave
label 1250 Hz corresponds to an exact center near 1258.925 Hz.
Consult Annex E for nominal labels. The API returns binary64 approximations
of the exact frequencies and uses a common exponent on either side of every
shared edge. It selects bands whose computed centers lie in the inclusive
configured range. The default center range is 20 Hz to 20 kHz.

## PSD integration and coverage

Let $f_s$ be the sample rate, $M$ the segment length, $N$ the FFT length
and $\Delta f=f_s/N$. Use the [PSD calibration contract](../../audio-power-spectral-density/references/PSD_CALIBRATION.md).
With unnormalized DFT $X[k]$ of the windowed segment and $S_2=\sum_n w[n]^2$,
one-sided **bin power** is

$$
P_k = S_{xx}[k]\,\Delta f
    = d_k\frac{|X[k]|^2}{N S_2}, \qquad
d_0=d_{N/2}=1,\quad d_k=2 \text{ for } 0<k<N/2.
$$

This reference uses even, radix-2 transforms. The full sum
$\sum_{k=0}^{N/2}P_k$ equals the window-energy-normalized mean square of the
prepared segment by Parseval. When enabled, mean removal occurs per segment
before windowing. Rectangular and periodic Hann windows are available.
Padding the transform beyond $M$ leaves the observation duration unchanged.

Treat an interior bin's power as uniform over its cell
$C_k=[(k-1/2)\Delta f,(k+1/2)\Delta f]$. The Nyquist cell ends at $f_s/2$
and has width $\Delta f/2$. Allocate the unique Nyquist bin's full power across
that half cell. Given a supported band $B=[f_l,f_u]$, compute

$$
Q_b = \sum_{k=1}^{N/2} P_k \frac{|B\cap C_k|}{|C_k|}.
$$

A shared point contributes zero overlap. This rule spreads finite-bin power
deterministically, including tones near an edge. Leakage depends on the window
and actual signal. A rectangular, unpadded DC-only segment has its entire power
in bin zero. Windowing or padding a finite DC segment can produce energy in
positive bins even though the integrator always excludes the DC bin itself.
Whole-spectrum power includes both endpoints. The displayed bands sum to
the power assigned to their covered interval, which can omit regions included
in whole-spectrum power.

| Reading status | Condition | Power, RMS and level |
| --- | --- | --- |
| `unavailable` | Lower edge is at or above Nyquist | All `None` |
| `truncated_nyquist` | Nyquist is strictly between the edges | All `None` |
| `unresolved_dc` | Nyquist support is complete and the lower edge is below $\Delta f/2$, the start of the first positive-bin cell | All `None` |
| `zero_power` | Full coverage and calculated band power is zero | $0,\ 0,\ -\infty$ |
| `ok` | Full coverage and positive band power | $Q_b,\ \sqrt{Q_b},\ 10\log_{10}(Q_b)$ dBFS |

An upper edge equal to Nyquist can have full coverage. Full grid coverage
describes bin support only. Check the band width against $f_s/M$ and the
window's main lobe to assess tone resolution. The rectangular and periodic
Hann main lobes have first-null widths of about $2f_s/M$ and $4f_s/M$,
respectively. For example, the 25 Hz third-octave band is about 5.8 Hz wide.
At 48 kHz an 8192-sample Hann segment has a main lobe about 23.4 Hz wide.
The reference exposes both `segment_spacing_hz` and `bin_spacing_hz` so a
consumer can report the frequency resolution and the integration grid.

Band power is in squared normalized amplitude. RMS is in normalized amplitude.
The full-scale reference is amplitude 1. A peak-1 sine wholly captured by
a band has mean-square $1/2$ and about −3.01 dBFS on this convention.
Sample values may have digital headroom above 1. For calibrated samples in pascals
measured in air, the pressure level would be $10\log_{10}(Q_b/(20\,\mu\mathrm{Pa})^2)$.
This API takes normalized PCM and reports only dBFS.

## Streaming and arithmetic

Supply ordered channel labels, a source tap, an epoch ID and an exact integer
start sample. `push(start_sample, planes, epoch_id=...)` takes one list or
tuple per channel and returns zero or more `RTAFrame` observations. Each
frame includes the epoch, configuration and contributing half-open sample
interval. Channels retain their input order and have separate spectra and
band readings.

For epoch origin $s_0$, hop $H$ and $K$ Welch segments, segment $j$
covers $[s_0+jH,\ s_0+jH+M)$. Its first reported frame occurs when
$j=K-1$. Each frame uses segments $j-K+1$ through $j$, with the
oldest segment start and the newest exclusive end. The observation spans
$M+(K-1)H$ samples, and its reporting interval is $H$ samples.
An incomplete segment remains pending and emits no synthesized data.
$K=1$ gives a modified periodogram.

Integrating each periodogram before averaging is equivalent to band integration
of the averaged PSD in exact arithmetic because the projection is linear.
This implementation stores only the most recent $K$ per-band and whole-spectrum
powers. It sums the current powers with `math.fsum` and divides once.
Recomputing the mean preserves quiet segments after a much louder segment
leaves the history. Overlap makes adjacent periodograms correlated.

The [sample timeline](../../audio-timebase-sync/scripts/reference_timebase.py)
tracks the active epoch and exact sample position. Within the reference bounds,
callback partitions produce the same segment sequence. A correctly positioned
empty block has no effect. Malformed planes, cursor gaps or overlaps, epoch
mismatch, out-of-domain PCM and detected arithmetic failures reject the entire
block before committing its cursor or analysis state. `reset_epoch` takes a
fresh ID and clears both overlap and Welch history. It can also install a new
configuration. The timeline retains used epoch IDs and rejects their reuse.
Use a single caller to serialize pushes and resets.

The bounds below limit the resources this Python reference uses.

| Parameter | Reference bounds |
| --- | --- |
| Rate and channel count | Integer 2–384,000 Hz, 1–8 distinct labels |
| Transform and hop | Power-of-two $N$ from 4 to 262,144, $4\le M\le N$, $1\le H\le M$ |
| Average and input block | $1\le K\le64$, at most 262,144 samples per plane and 128 completed segments per push |
| Band requests | Center limits within 1–384,000 Hz, selecting at least one band. Standalone geometry accepts indices −256 through 256 |
| PCM | Finite binary64, zero or magnitude from $2^{-128}$ through $2^{128}$ |

The PCM bounds allow digital headroom and keep normalization, FFT squares and
Welch sums away from overflow. Input outside the stated range raises
`ValueError`. A computed positive quantity that would become zero during
bin-power conversion, band projection or averaging raises `ArithmeticError`.
Cancellation, leakage and rounding still limit very small bins and precision
across large differences in signal level. For representative calculations the
[fixture ledger](../../../tests/fixtures/AUDIO_FRACTIONAL_OCTAVE_RTA_GOLDENS.md)
states dimensioned tolerances and the independent oracle for each check.

The current Python transform and callback path allocate work buffers. Processing
cost grows with the number of completed segments and channels, with
$O(N\log N)$ FFT work per segment and channel. The plan caches the window,
FFT tables and band weights. Persistent signal state is limited to the pending
overlap and $K$ segments of band powers per channel.

## Filter-bank measurements and IEC scope

An IIR or FIR band-pass filter bank derives band power from filtered,
time-averaged outputs. For a steady sine, each band's mean-square value follows
the squared magnitude of that filter's response at the tone frequency. Check
that response from the filter's SOS coefficients or impulse response, then
verify it with sufficiently long settled tones. Sweep on both sides of the
band, including the transition and stop bands, and account for digital frequency
warping and settling. Use the [filter design skill](../../audio-filter-design/SKILL.md)
for coefficient design and response validation. Welch estimates depend on the
window and cell integration. Compare the methods on settled, well-centered
signals with the measurement span and expected response declared.

IEC 61260-1:2014 specifies band-pass filter performance for class 1 and class 2,
including relative attenuation limits. Part 2 specifies pattern-evaluation
tests and Part 3 specifies periodic tests. The reference implements frequency
geometry only from that series. It has no IEC filter-class rating or calibrated
instrument evidence. IEC 61672 sound-level-meter compliance concerns the
whole instrument including the acoustic measurement path.

- [IEC 61260-1:2014](https://webstore.iec.ch/en/publication/5063) and [Part 1 preview, §§5.2–5.5](https://preview.sist.si/sist-preview/13383/3c4ae3e762b540cc8111744cb8f0ae8e/IEC-61260-1-2014.pdf)
- [IEC 61260-2:2016+A1:2017](https://webstore.iec.ch/en/publication/60437) and [IEC 61260-3:2016](https://webstore.iec.ch/en/publication/24399)
- [ANSI/ASA S1.11 national adoptions](https://asastandards.org/catalog/) and [ISO 266:1997 preferred frequencies](https://www.iso.org/standard/1350.html)
- [IEC 61672-1:2013 preview](https://webstore.iec.ch/en/iec_catalog/product/preview/?id=L3B1Yi9wZGYvcHJldmlldy9pbmZvX2llYzYxNjcyLTF7ZWQyLjB9Yi5wZGY%3D)
- [SciPy Welch density and averaging](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html)

## Run the reference

From the repository root, measure a 1 kHz tone at peak 0.5 with two overlapping
rectangular segments. The 1 kHz band reads approximately 0.125 power and
−9.03 dBFS over sample range $[0,96)$.

```sh
PYTHONPATH=skills/audio-fractional-octave-rta/scripts python3 - <<'PY'
import math
from reference_fractional_octave_rta import FractionalOctaveRTA, RTAConfig

config = RTAConfig(
    sample_rate_hz=8000, channel_labels=("L",), source_tap="decoded PCM",
    fraction=3, segment_samples=64, hop_samples=32, nfft=64,
    welch_segments=2, window="rectangular",
)
rta = FractionalOctaveRTA(config, epoch_id="example", start_sample=0)
pcm = [0.5 * math.cos(math.tau * n / 8) for n in range(96)]
(frame,) = rta.push(0, (pcm,), epoch_id="example")
band = next(reading for reading in frame.channels[0].bands if reading.band.index == 0)
print(frame.start_sample, frame.end_sample_exclusive, band.power, band.level_dbfs)
PY
```

```sh
python3 -m unittest discover -s tests -p 'test_audio_fractional_octave_rta_reference.py' -v
python3 tools/validate_seed.py
python3 -m unittest discover -s tests -v
git diff --check
```
