# Spectral descriptor measurement contract

## Input and frequency support

Use one complete frame of a real signal from one channel and one analysis
profile. Supply the calibrated one-sided PSD in squared amplitude units per
hertz. Record the source clock, epoch, tap, channel, amplitude unit, calibration,
profile, window, detrending, sample rate $f_s$, observation length $M$, transform
length $N$, and hop $H$. Identify the actual window coefficients with a stable
window identifier. The support is $[s,s+M)$ on an integer sample clock. The
doubled center is $2s+M-1$.

The PSD producer owns window-energy normalization and folding. It doubles paired
positive-frequency power bins. DC and the unique even-length Nyquist bin each
have one contribution. An odd transform's final positive bin is paired.
For bin $k$, use the center $f_k=k f_s/N$ and full bin power
$q_k=S_{xx}[k]\Delta f$, with $\Delta f=f_s/N$. Over the full grid, the sum
equals the window-energy-normalized mean square of the prepared frame.
[PSD calibration and Parseval](../../audio-power-spectral-density/references/PSD_CALIBRATION.md)

The reference uses one contiguous band, `[low_hz, high_hz)`, measured in hertz.
The default lower edge is 0. The default upper edge is $f_s/2$. Compare edges to
the binary64 centers calculated as `k*fs/N`, as in the multiresolution
reference. DC requires `include_dc=True`. If the upper edge equals $f_s/2$,
`include_nyquist=True` includes the unique even-length endpoint. This option
defaults to true and has no effect on an odd transform. The band must have
positive width and stay inside the input's frequency range. A valid band can
contain no bin centers.

Selecting a bin assigns its full power to its center. For a continuous-band
application, use the [RTA overlap contract](../../audio-fractional-octave-rta/references/FRACTIONAL_OCTAVE_RTA_CONTRACT.md#psd-integration-and-coverage)
and declare the density model. For example, a point at 150 Hz has zero spread.
A uniform cell from 100 to 200 Hz has spread $100/\sqrt{12}$ Hz. Calculate an
aggregate from one original profile. A selection assembled across unequal
observation windows has different time and frequency support.
[Original multiresolution profiles](../../audio-multiresolution-spectrum/SKILL.md)

## Frame descriptors

Let $B$ contain the selected bin indices, including their zero ordinates. Use
$K=|B|$, $Q=\sum_{k \in B}q_k$, and $p_k=q_k/Q$ when $Q>0$.

| Output | Definition | Unit |
| --- | --- | --- |
| Selected power | $Q$ | Squared input amplitude |
| Centroid | $\mu=\sum_k p_k f_k$ | Hz |
| RMS spread | $\sigma=\sqrt{\sum_k p_k(f_k-\mu)^2}$ | Hz |
| Rolloff | First selected bin center with cumulative power $\ge rQ$ | Hz, with DFT bin index |
| Flatness | Geometric mean of the PSD ordinates divided by their arithmetic mean | Ratio |
| Crest | Maximum PSD ordinate divided by the arithmetic mean | Ratio |
| Entropy | $-\sum_{p_k>0} p_k \ln p_k$ | Nats |
| Normalized entropy | Entropy divided by $\ln K$ for $K>1$ | Ratio |

Count equality at a rolloff boundary. For `[9, 25, 6]` at $r=17/20$, cumulative
power reaches 34 at the second selected bin. For `[47, 48, 5]` at $r=19/20$,
it reaches 95 at the second selected bin. The reference takes a rational
`rolloff_fraction` in $(0,1)$. Its default is $17/20$. For a decimal threshold
such as 0.95, construct the fraction from the decimal string or use $19/20$.

| State | Result |
| --- | --- |
| Band contains no center | `empty_selection`. Power and descriptors are unavailable. |
| Band contains only exact zeros | `silent`. Power is zero and shape descriptors are unavailable. |
| Positive power with an exact zero ordinate | Flatness is zero. Compute other descriptors normally. |
| One positive bin in a wider selection | Centroid and rolloff give that center. Spread and entropy are zero. Crest is $K$. |
| One selected bin with positive power | Raw entropy is zero. Normalized entropy is unavailable. |
| Positive scalar rounds to binary64 zero | Return the field as unavailable and name it in `underflowed`. Other available fields remain measurable. |

Flatness ranges from zero to one. Crest ranges from one to $K$. Entropy ranges
from zero to $\ln K$. A display may apply its own decibel reference and floor.
Keep these settings with the display. Use physical calibration before applying
physical unit labels.

## Frame-to-frame flux

For current frame $t$ and previous frame $t-1$, in the same bin order:

$$
F_\mathrm{power} = \sqrt{\sum_k(q_{t,k}-q_{t-1,k})^2},\qquad
F_\mathrm{shape} = \sqrt{\sum_k(p_{t,k}-p_{t-1,k})^2}.
$$

Power flux has squared amplitude units and shape flux is dimensionless. Both
describe a change over the declared hop. A common positive gain between
otherwise identical spectra changes power flux. It preserves shape when the
represented power ratios remain equal.

Use fixed band settings for a stream. Require identical context, including the
clock, epoch, channel, tap, calibration, window, FFT length, and hop. Require
`next_start_sample == previous_start_sample + hop_samples`. A hop may exceed
the window length if the schedule calls for that spacing. Reject a duplicate,
gap, or context change and preserve the last accepted frame. Call `reset()`
at a deliberate discontinuity. Then supply the new epoch as applicable.

The first frame gives `first_frame` and both flux values are unavailable. An
empty selection gives `empty_selection`. Either allowed silent operand gives
`silence`, with power flux available. For two positive-power observations,
`ok` supplies both values. If a positive shape change rounds to zero,
`shape_underflow` supplies power flux and leaves shape flux unavailable. The
result records the previous start index when a comparison was made.

## Reference limits and verification

[The reference script](../scripts/reference_spectral_descriptors.py) supplies
`measure(frame, options)` for a stateless calculation. Use
`DescriptorStream(options).push(frame)` for adjacent-frame flux. The
`PSDFrame` takes one `PSDContext`, an exact start index, and an immutable
tuple of $N // 2+1$ ordinates. It checks each ordinate before use, even outside
the selected band. A frame or option outside the declared domain raises
`ValueError`. The reference trusts the caller's measurement provenance.

- Sample rate is an integer from 2 through 384,000 Hz. Use $2\le M\le N\le32768$
  and an integer hop from 1 through 32,768. Declare `none` or `mean` detrending.
  Keep the start and end-exclusive indices in $[0,2^{256}-1]$.
- An ordinate is a built-in float or integer. The supported values are exact zero
  and nonnegative, finite values from $2^{-800}$ through $2^{800}$. The reference
  converts each ordinate to binary64 before measuring it.
- For an upstream `ProfileObservation`, select one channel's PSD. Copy its
  sample interval, profile, and transform settings. Supply the tap's unit,
  calibration, and clock identity from acquisition. Check the supplied
  end-exclusive index against $s+M$. Keep the clock identity unique to the
  originating timeline.

The reference converts the binary64 ordinates to integer weights with a
common power-of-two denominator. This preserves boundary equality when the
common $\Delta f$ cancels. The reference uses exact bin moments before taking
the square root. A binary64 implementation should accumulate around the mean,
since subtracting nearly equal rounded raw moments can lose the variance.
For flatness, take logs of the original positive ordinates before forming
ratios. For entropy, sum contributions in the log domain to preserve a
representable aggregate of very small terms.

Review the [frozen fixtures and agent tasks](../../../tests/fixtures/AUDIO_SPECTRAL_DESCRIPTORS_GOLDENS.md).
The reference is deterministic, offline, and uses standard-library Python.
Its valid input is a calibrated single-resolution PSD. Fractional cell moments,
FFT generation, loudness, onset decisions, device calibration, and real-time
performance have their own acceptance checks.

The Timbre Toolbox uses several spectral representations. Librosa 0.11.0 uses
magnitude in its centroid convention and applies a floor in its flatness
routine. Essentia's flux describes a magnitude-spectrum difference with
options for norm and half-wave rectification. Match the weights, grid,
floor, fraction, and flux settings before using a library as an oracle.
[Peeters et al. (2011), §III](https://www.mcgill.ca/mpcl/files/mpcl/peeters_2011_jasa.pdf) ·
[librosa 0.11.0 source](https://librosa.org/doc/0.11.0/_modules/librosa/feature/spectral.html) ·
[Essentia Flux](https://essentia.upf.edu/reference/streaming_Flux.html)
