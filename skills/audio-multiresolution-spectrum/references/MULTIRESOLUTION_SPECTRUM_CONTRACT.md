# Multiresolution spectrum contract

Companion to the [skill](../SKILL.md),
[reference](../scripts/reference_multiresolution_spectrum.py), and
[frozen fixtures](../../../tests/fixtures/AUDIO_MULTIRESOLUTION_SPECTRUM_GOLDENS.md).

## Independent measurements and mathematics

Three parallel profiles read identical ordered PCM planes. Each owns its complete
left-aligned window/hop schedule, window properties and original PSD grid. No
resampling, detrending, interpolation, averaging or smoothing occurs. FFT padding
from M to N is explicit configuration; incomplete input frames are never padded.

For sample rate fs, window length M, hop H and FFT length N >= M:

```
df = fs/N                 observation_duration = M/fs
hop_duration = H/fs       S1 = sum(w[n])       S2 = sum(w[n]**2)
X[k] = sum(x[n]*w[n]*exp(-j*2*pi*k*n/N), n=0..M-1)
PSD[k] = d[k]*abs(X[k])**2/(fs*S2), k=0..N/2
sum(PSD)*df = sum((x[n]*w[n])**2)/S2
```

The radix-2 reference supports even N only. d=1 at DC and the unique Nyquist bin;
d=2 at paired interior bins. Units are squared normalized amplitude per hertz.
Multiplying density by df yields bin power. Parseval applies to each complete
profile independently, including explicit zero padding. For a nonstationary Hann
frame, this integral need not equal the unweighted sample mean square.

Coherent gain is S1/M, mean-square gain is S2/M, ENBW in native M-point bins is
M*S2/S1² and ENBW in Hz is fs*S2/S1². Rectangular w=1 has gains 1,1 and ENBW fs/M.
Periodic Hann `w[n]=0.5-0.5*cos(2*pi*n/M)` has gains 1/2,3/8 and ENBW 1.5*fs/M.
Approximate null-to-null main-lobe widths are 2*fs/M and 4*fs/M respectively.
These widths describe the window, not a guarantee of separating arbitrary tones.
Coherent tone amplitude requires its own S1 correction and appropriate isolation;
neither a highest PSD bin nor an off-bin peak is an exact amplitude estimator.
Zero padding reduces df while leaving duration, ENBW in Hz and main-lobe width
unchanged. Hop controls reporting cadence; overlapping frames are correlated.

## Reference profiles

| fs | Profile | M | H | N | Selected bin centers (Hz) | df (Hz) | M/fs (ms) | H/fs (ms) |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| 48000 | low | 8192 | 2048 | 8192 | [20,200) | 5.859375 | 170.666667 | 42.666667 |
| 48000 | mid | 2048 | 512 | 2048 | [200,2000) | 23.4375 | 42.666667 | 10.666667 |
| 48000 | high | 512 | 128 | 512 | [2000,20000] | 93.75 | 10.666667 | 2.666667 |
| 96000 | low | 16384 | 4096 | 16384 | [20,200) | 5.859375 | 170.666667 | 42.666667 |
| 96000 | mid | 4096 | 1024 | 4096 | [200,2000) | 23.4375 | 42.666667 | 10.666667 |
| 96000 | high | 1024 | 256 | 1024 | [2000,20000] | 93.75 | 10.666667 | 2.666667 |

All defaults use periodic Hann. Rectangular is supported for analytical checks.
The 96 kHz configuration doubles sample counts to preserve physical durations.

## Common-end schedule and exact provenance

For epoch origin o, profile i emits `[o+j*H_i, o+j*H_i+M_i)` for j >= 0.
Choose C=max(M_i) and L=lcm(H_0,H_1,H_2). Require

```
(C-M_i) % H_i == 0    for every i
composite endpoints = o+C+q*L, q=0,1,...
```

Because L is divisible by every H_i, every selected endpoint belongs to every
profile's actual schedule, and every contributor is complete. Reject configurations
that fail the congruences; this reference does not search for a delayed first
intersection. Profile lengths must be ordered low >= mid >= high. L is bounded.
At 48 kHz and o=0 the first intervals are `[0,8192)`, `[6144,8192)` and
`[7680,8192)`; the next endpoint is 10240. Centers differ: preserve
`center_sample_twice = 2*start_sample+M-1`, never a float-derived clock.
Origins above 2**53 remain exact. Each observation retains its epoch, sample rate,
source tap, profile configuration, exact window coefficients/properties, frequency
grid and ordered labeled channel PSDs. Consumers can derive exact elapsed seconds
with `fractions.Fraction(sample-origin, fs)`; no hardware-time claim follows.

## Ownership and unavailable output

Configuration defines four strictly increasing positive frequency edges. The
default ranges are those above. Bin centers use binary64 `k*fs/N`; compare them
directly with the declared edges, without epsilons or approximate equality. Internal
edges belong to the higher profile, and only the final upper edge is inclusive.
Ownership is a display/selected-estimate rule, not a perfect crossover filter.
Leakage can cross edges. Different grids leave unevenly spaced selected bins.

`owner_index(config,f)` identifies the profile range. Each composite selection
retains source bin indices, with status `ok` or `unavailable` if none exist. Full
original PSDs remain available, including DC and bins outside selected ranges.
`composite.at_frequency(f,label)` returns a measured ordinate only if f exactly
equals a selected bin center on the owning grid; otherwise it returns an explicit
`unavailable` reading with no density. It never snaps to an adjacent profile or
interpolates. Unknown channel labels are errors. Bounds beyond Nyquist may be
configured but have no bins there. DC is always excluded from selections.

There is no `composite_total_power`. Selected densities have different bin widths,
windows and histories. Summing them, even after local bin-width weighting, does
not establish energy conservation across a composite. Use an individual complete
PSD's Parseval integral for that profile's window-weighted power.

Log density is `10*log10(PSD/reference_density)` with an explicit positive density
reference in matching units. Zero remains measured zero (log value −infinity); a
finite visual floor belongs to rendering. Digital PCM has no SPL calibration.

## Streaming API, atomicity and resource domain

`SpectrumConfig` and `ProfileConfig` are immutable. `reference_config(fs, labels,
source_tap)` supplies the two tabulated defaults. Other sample rates require an
explicit configuration. `MultiresolutionSpectrum(config, epoch_id=..., start_sample=...)`
is single-caller, synchronous and sample-clocked. `push(start_sample, planes,
epoch_id=...)` returns an immutable `PushResult(profile_observations, composites)`.
Original observations are ordered by end-exclusive sample, then profile order;
channels retain configuration order. Composites are ordered by endpoint and refer
to the same original observation objects. No output is retained internally.

Inputs are tuples/lists of equal-length real numeric planes (bool is rejected),
one per distinct nonblank channel label. Indices are nonnegative Python integers
(bool rejected). Require exact expected start and matching epoch even for empty
pushes. A valid zero-length push is a no-op. Reject gaps, overlaps, epoch mismatches,
bad metadata or late invalid input before changing any state. Compute new windows,
spectra, selections and outputs in temporary state; only then commit the timeline
and all pending histories. Numerical/processing failures return no partial output
and preserve histories, cursor and schedules. No implicit tail flush exists.

`reset_epoch(epoch_id,start_sample,config=None)` requires a previously unused ID,
clears every history and restarts all schedules relative to the new origin. Rate,
layout or tap changes require a fresh epoch/configuration. Use the public existing
`SampleTimeline`, `SampleRate` and `DiscontinuityError` timebase types; no private
classes from other skills are imported. The FFT is local to this reference and is
never used as its own independent oracle. No shared DSP refactor is needed.

Explicit reference limits (rejected before processing):

- Exactly three named profiles; 1..8 ordered unique channels; fs integer 2..384000.
- 4 <= M <= N <= 32768; N is a power of two; 1 <= H <= M; L <= 65536.
- At most 65536 samples per plane per push, 256 completed profile frames total,
  2**24 channel-weighted `sum(frame_count*N*log2(N))` work units, and 2**20
  returned PSD ordinates per push. Divide larger callbacks explicitly.
- Normalized PCM permits headroom: samples are zero or have absolute binary64
  magnitude in [2**-128,2**128]. Values outside this domain are rejected, including
  finite extremes; this is not a claim to support all finite binary64 inputs.
- Epoch IDs, labels and source tap are at most 128 characters; sample indices
  at most 256 bits; at most 1024 epochs per analyzer, bounding epoch bookkeeping.

Retained raw samples are fewer than `channels*sum(M_i)`, plus cached windows/grids
O(sum(N_i)) and bounded epoch metadata. Callback staging is
O(channels*(3*block_samples+sum(M_i))+returned_ordinates); FFT scratch O(max(N_i)).
Transform work is O(channels*sum(frame_count*N_i*log2(N_i))), with additional
bounded sample copying, validation, selection and sorting. Python object overhead
is not eight bytes per sample. These are size bounds, not callback deadlines.

The amplitude domain keeps direct FFT squaring and normalization within normal
binary64 range for ordinary results. Check positive squared magnitudes and PSDs
that round to zero, nonfinite intermediates/results, and nonzero windowed frames
that collapse entirely to zero; raise `ArithmeticError` atomically. Finite precision
can still hide a quiet component under a loud one, and cancellation near true
spectral zeros has no useful relative error guarantee. Tiny numerical leakage is
not clamped away. Bounds do not guarantee exact recovery of arbitrary dynamic range.

## Example and verification

From the scripts directory:

```python
from reference_multiresolution_spectrum import MultiresolutionSpectrum, reference_config

config = reference_config(48000, ("L", "R"), "decoded PCM")
analyzer = MultiresolutionSpectrum(config, epoch_id="capture-1", start_sample=0)
result = analyzer.push(0, ([0.0]*8192, [0.0]*8192), epoch_id="capture-1")
assert result.composites[0].end_sample_exclusive == 8192
assert [f.start_sample for f in result.composites[0].contributors] == [0, 6144, 7680]
analyzer.reset_epoch("capture-2", 2**53+7)
```

Run `python3 -m unittest discover -s tests -p 'test_audio_multiresolution_spectrum_reference.py' -v`,
the complete repository suite, `python3 tools/validate_seed.py` and `git diff --check`.
Fixtures freeze closed-form expectations, independent direct-DFT checks and
adversarial stream cases before tolerance changes. Optional SciPy comparisons must
use explicit identical coefficients, no detrending, complete manual slices,
one-sided density scaling and matching N, not library-default centered padding.
No realtime, perfect separation or standards certification is claimed.

## Research reconciliation and sources

The user-uploaded Deep Research report proposes 16384/4096/1024 at 48 kHz and
375/3000 Hz crossovers, with additional 96 kHz alternatives. Those are proposals;
the AUDIO-24-01 handoff specifies the authoritative table used here. The report's
display interpolation and amplitude modes are excluded from this PSD reference.
Its formula `d*|X|²/(N*S2)` describes bin power; density requires `fs*S2` instead.
Its suggestion that a cross-profile partition alone supplies calibrated total
power is insufficient with unequal windows and histories; this API exposes none.
Opaque research citation tokens are not independently retrievable source evidence.

Established contracts: [FFT](../../audio-fft-spectrum/references/FFT_CALIBRATION.md),
[window](../../audio-window-functions/references/WINDOW_CALIBRATION.md),
[PSD](../../audio-power-spectral-density/references/PSD_CALIBRATION.md),
[STFT](../../audio-spectrogram-waterfall/references/STFT_WATERFALL_CONTRACT.md),
[timebase](../../audio-timebase-sync/references/TIMEBASE_CONTRACT.md).
Public mathematical references: [SciPy periodogram](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.periodogram.html),
[SciPy Hann](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.windows.hann.html),
[Smith, Spectral Audio Signal Processing](https://www.dsprelated.com/freebooks/sasp/).
External source links provide background; executed evidence belongs in the fixture
ledger and dated implementation handoff.
