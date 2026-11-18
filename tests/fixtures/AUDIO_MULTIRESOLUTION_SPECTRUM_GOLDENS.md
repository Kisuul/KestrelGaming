# Skill #24 frozen analytical expectations

Frozen before reference implementation or observed-error tolerance tuning for
AUDIO-24-01, baseline `fe65c8c900608873911d7f9b64e8a95881fa80c8`.
These are acceptance expectations, not assertions that tests have already run.
See the [contract](../../skills/audio-multiresolution-spectrum/references/MULTIRESOLUTION_SPECTRUM_CONTRACT.md).

| Fixture | Independent expectation |
| --- | --- |
| Silence | Every original PSD ordinate exactly 0; timestamps still advance; no finite floor |
| Rectangular DC c | Only DC has density c²*M/fs when N=M; integral c²; DC never selected |
| Rectangular Nyquist ±A | Only k=N/2 has density A²*M/fs; integral A²; unique bin not doubled |
| Coherent sine peak A | Integral A²/2; rectangular on-bin density A²*M/(2*fs); exact four-sample cycle [0,A,0,-A] avoids sine-generation roundoff |
| Rectangular impulse A at j | Inclusion iff start <= j < end; interior density 2*A²/(fs*M), DC/Nyquist half that; integral A²/M |
| Periodic Hann impulse | Same with w[j]² and S2=3*M/8; a sample under w[0]=0 contributes no energy |
| Periodic Hann gains | S1=M/2; S2=3*M/8; CG=1/2; ENBW=1.5*fs/M |
| End-aligned transient | At C=64 with M=(64,16,4), impulse at 63 contributes powers (1/64,1/16,1/4); impulse at 47 contributes (1/64,0,0) |
| Default geometry | Endpoints 8192,10240; first starts 0,6144,7680; doubled centers 8191,14335,15871 |
| Large origin o | Add o to every boundary and 2*o to every doubled center, exactly above 2**53 |
| Off-bin sine | Independently sum existing direct DFT; leakage remains positive away from the peak; no exact tallest-bin amplitude assertion |
| Nearby tones | fs=1024, rectangular M=(256,64,16), frequencies 80 and 88 Hz, equal peak 0.5; long-frame densities 1/32 at 80/88 and zero within rounding at 84; short native grid spacing 64 Hz cannot sample both tone centers |
| Padding | Same windowed input, larger N; Parseval and ENBW_Hz unchanged; only df changes |
| Crossovers | For edges (1,8,16,32): nextafter(8,-inf) belongs low, 8 and nextafter(8,+inf) belong mid; corresponding rule at 16; 32 included and nextafter(32,+inf) excluded |
| White noise | Seeded realization: compare actual window-weighted sample energy with each independent profile's PSD integral; finite realization does not equal ensemble variance exactly |
| Pink noise | Seeded random-phase cosine synthesis with amplitudes proportional to 1/sqrt(k); ensemble octave powers equal in expectation; report finite-record dispersion, no exact random-bin golden |
| Multichannel | Independent labeled planes, anti-phase equal PSD, amplitude-halved power quartered; permutation changes labels/order only |
| Partitions/reset/errors | Exact output equality for valid partitions; reset removes all old history; late bad input/metadata, processing or arithmetic failure leaves all state unchanged |
| Extreme input | Exact four-sample cycle at A=2**±128 has integrated power 2**(±256-1); adjacent out-of-domain amplitudes and nonfinite input reject before mutation |
| Limits | Invalid alignment, shape, type, work, output, epoch or configuration limits reject atomically |

Ordinary nonzero PSD and Parseval comparisons start at relative tolerance 1e-10.
For small direct-DFT vectors, use per-bin absolute tolerance `1e-12 * frame_power/df`
near cancellations, plus relative 1e-10. Absolute tolerance is magnitude-scaled,
not a claim that any expected zero has a relative error. Closed-form exact zeros
use equality when the arithmetic path permits it; sine-generated theoretical
nulls use the stated absolute bound. Geometry, ordering, labels and ownership
always use exact equality. No tolerance may be loosened solely for a green run.

## Executed evidence

On Python 3.12.14, the 35 focused tests and 627-test full repository suite passed.
`python3 tools/validate_seed.py` and `git diff --check` passed. No failed checks
or tolerance adjustments were observed in the implementation verification run.
The exact implementation revision is recorded in the dated project handoff.

The reproducible optional command is:

```sh
python3 tests/test_audio_multiresolution_spectrum_reference.py --independent-studies
```

SciPy 1.17.0 `signal.periodogram` independently checked **1,536 profile/channel
spectra**: fs=48000/96000, rectangular/periodic Hann, N=M/2M, two independent
channels, seeded off-bin-tone-plus-noise input, manually sliced complete frames,
`detrend=False`, `return_onesided=True`, `scaling="density"`. SciPy constructs
its own `windows.hann(M,sym=False)` coefficients. All frequency coordinates
matched exactly. Maximum absolute density error divided by `frame_power/df`
was **4.79012e-17**; maximum relative error on bins above 1e-8 of the frame's
peak reference density was **9.46059e-13**; maximum Parseval relative error
was **3.88738e-16**. This supplements closed-form and existing direct-DFT tests;
SciPy is optional and is not imported by the reference or ordinary tests.
A replay of the optional command produced identical reported results.

The same command performs 32 independent random-phase pink approximations
(seed 24012473): M=N=1024, fs=1024, periodic Hann, cosine amplitudes 1/sqrt(k),
k=1..255. Expected band power is calculated independently by distributing each
coherent cosine's 1/(2*k) power with Hann weights 1/6,2/3,1/6 at k-1,k,k+1.
This explicitly includes leakage at the reporting edges.

| Octave bins | Expected power | Mean measured/expected | Sample SD of ratio | Approximate 95% half-width for mean |
| --- | ---: | ---: | ---: | ---: |
| [8,16) | 0.363827 | 0.928791 | 0.386137 | 0.139250 |
| [16,32) | 0.354771 | 0.954620 | 0.244601 | 0.088209 |
| [32,64) | 0.350574 | 0.976141 | 0.170472 | 0.061476 |
| [64,128) | 0.348550 | 1.019643 | 0.116881 | 0.042150 |

The half-width uses 2.04*sample_SD/sqrt(32), an approximate t-based summary of
independent random-phase trials, not exact coverage for an arbitrary noise
process. The finite harmonic sums only approach equal octave power. This is a
descriptive study with reported uncertainty, not a hard exact pink-noise fixture
or a cross-profile energy result.

An independent hostile-review agent additionally exercised 101 accepted
randomized configurations and **6,940 frames**, including mixed windows,
non-power-of-two M, nontrivial hops/LCMs, supported amplitudes and exact origins
above 2**200. Its separate sin-squared Hann/time-energy and direct complex-sum
oracles measured maximum Parseval relative error **4.56989e-15** and DFT error
normalized by `frame_power/df` **4.64508e-16**. It tested partition equality,
shifted crossover edges one ULP each way, and failures after a successful frame
in every profile plus reset-plan failure. No required-invariant violation was
observed. These probes are independent review evidence, not exhaustive proof or
owner/Gauge acceptance; the checked-in tests and optional command supply the
maintained reproducible verification entrypoints.
