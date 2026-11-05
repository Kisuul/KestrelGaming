# Audio VU metering — precise bounded reference contract

Companion to [the skill](../SKILL.md). This is a **VU-inspired analytical simulator**, not a specification-complete IEC 60268-17 SVI, test lab or production audio meter.

## Design identity and definitions

**Signal provenance:** 1–8 independently labelled planar channels, contiguous exact **integer sample** coordinates in a named epoch, rational nominal sample rate `Fraction` (8–384 kHz). Input `unit-normalized float PCM` is not volts until an explicit gain or A/D calibration provides that mapping. PCM may exceed `±1` in float intermediate processing without implying integer PCM clipping; the model never clamps audio. `volts` are accepted only when caller confirms that the upstream samples represent the physical voltage at the actual measurement tap. No implicit downmix/channel reordering, resampling, frequency weighting or peak detection.

**Tone calibration:** for an ideal 1 kHz steady sinusoid, the user selects **a sine peak** `A_ref > 0` in declared input units. Digital example: `A_ref=10^(L/20)` for explicit `L=-20 dBFS-peak` relative to normalized peak amplitude 1; another installation may choose `L=-18`. For analog line-level, `V_RMS=0.775 V * 10^(dBu/20)` and `A_ref=sqrt(2)*V_RMS`. At +4 dBu, about 1.228 V RMS and 1.737 V peak. dBu is a **voltage ratio** here, not a statement that some measured power is delivered into 600 Ω. Recording a dBm specification would require load and impedance information and a separate calibration.

**Detector:** for a continuous ideal sine `x(t)=A_ref*sin(2*pi*1000*t)`, `mean(abs(x)) = 2*A_ref/pi`. This *model* drives the needle with `u[n]=(pi/(2*A_ref))*abs(x[n])`, an instantaneous rectified sample normalized to give unit time-averaged target under an ideal sine. This **does not calculate 300 ms RMS**, and it is not the full physical copper-oxide rectifier transfer of a certified instrument. At finite audio sampling rates, discrete mean-absolute sine differs from the integral; tested 48 kHz 1 kHz sine steadies to about zero VU with a small predictable discrepancy. Other frequencies, sample rates, phase offsets and anti-aliasing are **not** fully certified.

**Needle continuous model** (idealized 2nd-order LTI, not an electromechanical apparatus):

```
  y''(t) + 2*zeta*omega_n*y'(t) + omega_n^2*y(t) = omega_n^2*u(t)
  zeta = -ln(Mp)/sqrt(pi^2 + (ln(Mp))^2), Mp=0.0125
  zeta ~= 0.8127169864286775
  omega_n ~= 13.511912562532723 radians/second
```

The step response from zero for constant held `u=1` is:

```
  wd = omega_n*sqrt(1-zeta^2)
  y_step(t) = 1 - exp(-zeta*omega_n*t) *
      (cos(wd*t) + (zeta/sqrt(1-zeta^2))*sin(wd*t))
```

The earliest time at which `y_step(t)` reaches **0.99** is 300 ms by the chosen tuning; peak around **399.042 ms** is **1.0125**, i.e. **1.25% overswing**. `300 ms` is not an integration window and is not a per-sample IIR coefficient. This idealized second-order system has a symmetric fall response only under linear assumptions; physical meter stops/springs/rectifiers can differ.

**Exact ZOH per audio sample:** constant `u[n]` for the next exact sample interval `dt = 1 / sample_rate`. Evolve displacement `y` and velocity `v` from previous state by solving the ODE over that interval, *not* by Euler iteration. With `alpha=zeta*omega_n`, `beta=omega_n*sqrt(1-zeta^2)`, `E=exp(-alpha*dt)`, `C=cos(beta*dt)`, `S=sin(beta*dt)` and `z=y-u`:

```
  y_new = u + E*(C+alpha*S/beta)*z + E*(S/beta)*v
  v_new = -E*(omega_n^2*S/beta)*z + E*(C-alpha*S/beta)*v
```

The reference precomputes these transition coefficients per meter rate. This is a 2-state **linear spring model driven by a rectified input**, not a true RMS detector. At every audio sample, the model evolves regardless of whether a GUI redraw occurs. The new output represents the state at the *exclusive end* of the returned sample range. Nonempty blocks of 1–32768 frames and 1–8 channels are supported. Nonfinite inputs and nonrepresentable arithmetic reject **atomically**: no channels, states, block counter or sample cursor advance.

**VU number:** `VU=20*log10(max(0,y))`. `y=1` means alignment (`0 VU`); `y=0` has no finite VU number so the returned `vu` is **None** (the mathematical log is `−∞`, not a finite scale marking). A physical negative pointer deflection cannot occur; the display-only nonnegative clamp flags `display_clamped_to_zero` when the idealized differential state is negative, without changing the inner state or any audio signal. The display's nominal `+3 VU` edge is an **indicator**, never an audio limiter or conformity threshold. `sample_peak_in_input_units` is scoped to the *current returned block*, not whole-program peak hold or intersample true-peak.

## Independent checks and expected quantities

| Independent stimulus | Expected interpretation |
| --- | --- |
| Ideal detector target `u=1` held for 0.1 s | Needle ~0.4350868491 (not 0.1 s worth of RMS) |
| Ideal detector target for 0.16 s | Needle ~0.7180364715 |
| Ideal detector target for 0.2 s | Needle ~0.8452902481 |
| Ideal target 0.300 s | Needle 0.99, **first** crossing of 99% |
| Ideal target to 0.39904222 s | Peak 1.0125 = **1.25% overswing** |
| Reference steady 1 kHz sine, −20 dBFS-peak, 48 kHz | About 0 VU **after settling**; sample peak remains 0.1; not 0 dBFS |
| Same sine −6 dB amplitude | About −6 VU after settling; this is an amplitude ratio |
| Identical RMS DC voltage versus sine | DC ~+0.912 VU relative to sine on the mean-rectified model (`20 log10(pi/(2*sqrt(2)))`) |
| One-sample input impulse | Very small needle response versus steady program level even when sample peak is large |
| Stereo anti-phase | Both channel indicators move; never sum raw channels and cancel them automatically |
| Rechunk the same contiguous frames | Identical final needle and sample index, independent of update/paint rate |
| Gap, calibration change, new rate or source seek | Reject without state movement, or create explicit new unique epoch |

Golden scenarios are in [AUDIO_VU_METER_GOLDENS.md](../../../tests/fixtures/AUDIO_VU_METER_GOLDENS.md), with [stdlib tests](../../../tests/test_audio_vu_meter_reference.py) derived from analytic formulas. Optional [SciPy state-space differential](../scripts/check_scipy_vu.py) constructs the continuous ODE independently, solves pole/damping parameters with SciPy's root finder and discretizes with `scipy.signal.cont2discrete` to compare callbacks. Agreement checks **this idealized model**, not standards conformance, device implementation or perceptual loudness.

## Acceptance beyond this oracle

A production VU meter needs measured 1 kHz calibration with actual electrical units, the full IEC 60268-17:1990+COR1:1991 electromechanical frequency/tone-burst/reversibility/rectifier/electrical/scale requirements if claiming conformity, instrument-to-host comparison over source and levels, actual update-rate/clock drift handling, and UI scale/refresh validation. Digital example calibration cannot be lifted into all analog installations. Compare separate peak and loudness instruments before using the VU indicator to manage clipping headroom.

**Primary sources:** [IEC 60268-17:1990](https://webstore.iec.ch/en/publication/1216), [ITU-R BS.2054-4 (2014)](https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BS.2054-4-2014-PDF-E.pdf), [AES VU meter overview](https://aes.org/resources/audio-topics/loudness-project/learn-more/). These establish context and history; this reference does **not** claim normative implementation or an exhaustive standards clause audit.
