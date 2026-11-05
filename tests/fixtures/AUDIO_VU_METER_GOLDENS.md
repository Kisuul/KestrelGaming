# Independent audio VU-inspired mathematical fixture and decisions

The fixture is an explicitly specified **mathematical reference**, not data captured from an IEC 60268-17 certified meter. Expected values below come from the closed-form second-order differential equation, decibel/rectification definitions and independent signal reasoning; they are **not** copied from the Python output. See [VU contract](../../skills/audio-vu-metering/references/VU_METER_CONTRACT.md).

## Independent derived constants

Select `M_p=0.0125` amplitude overshoot. For a standard underdamped unit-gain second-order system, `M_p=exp(-pi*zeta/sqrt(1-zeta^2))`; hence `zeta= -ln(.0125)/sqrt(pi² + ln(.0125)²) ~= 0.8127169864286775`. Choose `omega_n` to make the *first 99% crossing* at 0.3 seconds. The continuous analytical step response (see contract) then yields:

| Seconds after unit detector step | Deflection, analytic |
| ---: | ---: |
| 0 | 0 |
| 0.100 | 0.43508684911749607 |
| 0.160 | 0.7180364715485825 |
| 0.200 | 0.8452902480743435 |
| 0.299 | 0.9893895005441624 |
| 0.300 | 0.9900000000000001 |
| 0.301 | 0.990599043182191 |
| 0.39904222172960185 | 1.0125 |
| 0.550 | 1.0039715706790773 |

Only precisely evaluated constants are asserted in unit tests; a string with an ellipsis is illustrative, not a machine oracle.

## Calibration and error traps

- **Analog voltage**: for `+4 dBu`, `V_rms=0.775*10^(4/20) V ~= 1.228 V RMS`; `A_peak=sqrt(2)*V_rms ~= 1.737 V` for a pure sine. This says nothing about load impedance or output power.
- **Digital sine peak**: `-20 dBFS-peak` means `A_peak=10^(-20/20)=0.1` for unit-normalized peak float samples. Its sine RMS amplitude is `0.1/sqrt(2)`, *not* a `0 dBFS` signal. `-18 dBFS-peak` reference is different by 2 dB; both are selectable lineup conventions.
- **Mean-rectified versus RMS**: ideal sine with RMS `r` has mean absolute amplitude `2 sqrt(2)*r/pi`. A constant DC input of magnitude `r` instead has mean absolute amplitude `r`; DC / sine indication for equal RMS tends to `pi/(2sqrt(2))` or about +0.912 dB. A true RMS meter would not show that contrast.
- **Ideal input step vs tone burst**: `u=1` is a constant **detector target**. It is not a 1 kHz sine and cannot certify frequency-dependent physical rectification or complete IEC tone-burst behavior. Sampled 1 kHz tone at 48 kHz has a small discrete rectification bias; regression tolerances make that explicit.
- **Transients**: input impulse sample peak of `0.1` can occur while indicated VU remains much lower. A meter showing `0 VU` during programme alignment does **not** imply no digital or reconstructed-sample overload.
- **Independent channels**: L and -L of the same sine each produce the same VU; summing to zero before metering would be a different, explicitly chosen *mono downmix* operation.
- **Invalid continuity**: a gap, overlapping sample range or an invalid second channel rejects the entire block **without moving state or cursor**, even if a first channel could have been calculated.

## Independent instrument-review exercises (for future agent-use tests, NOT executed)

1. **Question:** A designer proposes a rolling 300 ms RMS average as an IEC VU meter. **Acceptance:** Agent distinguishes RMS-window and standard volume indicator detector/ballistics; requires a standards clause and hardware/tone-burst tests before certification.
2. **Question:** A plugin shows 0 VU for a −20 dBFS-peak 1 kHz tone. Does this guarantee no clipping? **Acceptance:** No; 0 VU is lineup-related and intentionally misses fast peaks; independently meter sample/true-peak and specify the signal tap.
3. **Question:** Why does equal-RMS square/sine programme indicate differently? **Acceptance:** A rectified-mean model responds to average absolute amplitude, not only mean square; quantifies about +0.91 dB DC/square offset and identifies model-specific nature.
4. **Question:** Is +4 dBu identical to −18 dBFS? **Acceptance:** No; physical voltage vs digital normalized reference require A/D gain and declared alignment; both can be separately selected in a device.
5. **Question:** The meter flickers when the GUI redraw rate changes. **Acceptance:** Update meter at the audio sample clock, not one envelope sample per paint; preserve exact epoch/cursor and block partition invariance.
6. **Question:** A VU meter should replace a LUFS meter in broadcast deliverables. **Acceptance:** Reject that substitution and name the applicable loudness/true-peak method and standards requirements.

The above exercises are *design acceptance questions*. They are not measured evidence of host-level skill activation, better agent judgment, or downstream production conformance.
