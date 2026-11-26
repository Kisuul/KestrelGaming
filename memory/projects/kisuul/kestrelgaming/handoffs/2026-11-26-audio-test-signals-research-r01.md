---
schema: 1
id: 2026-11-26-audio-test-signals-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch 3d65d0ddb88fead8d8a067e6abb8877ae5609d7b; Farina (2000), Muller and Massarani (2001), SciPy 1.17.0 chirp comparator; executed phase, multitone and logarithmic sweep checks below."
---

# Skill 44 research for audio test signals

## Summary

**Task outcome:** COMPLETE

Select a stimulus that makes the suspected behavior observable.
Describe its sample support, phase, level and channel routing so
another implementation can reproduce it. Start with coherent tones,
impulses and controlled multitone mixtures. Add a sweep where the
measurement needs broadband excitation and a corresponding inverse.
[Kestrel fixture contract](../../../../../skills/audio-dsp-test-fixtures/references/FIXTURE_CONTRACT.md)

## Evidence

### Describe the signal before rendering it

Record the epoch, integer sample origin $o$, rate $f_s$, frame
count $N$, channel IDs, digital or physical amplitude reference,
and phase. Record any seed, generator definition, fade, conversion
or resampling. Preserve the realized PCM as the input to a
measurement. A generator description states what was intended.
The actual stimulus can acquire noise, extra tones or an altered
sample clock before it reaches the device under test.
[Sample clock](../../../../../skills/audio-timebase-sync/SKILL.md) ·
[Signal provenance](../../../../../skills/audio-analysis-provenance/SKILL.md)

For a coherent interior-bin tone, use $f=k f_s/N$ and
$x[n]=A\sin(2\pi k(n-o)/N+\phi)$ over $[o,o+N)$. Reduce the
integer phase numerator modulo $N$ before floating-point
conversion. A whole number of cycles in that rectangular frame
has RMS $A/\sqrt{2}$ for $0<k<N/2$. The observed sample peak
also depends on phase. At DC a sinusoid is a constant, and at
even-length Nyquist its two possible samples are $\pm A\sin\phi$.
Test those endpoints independently. A callback boundary must
preserve phase in the epoch. An intentional restart, gap or
fade changes the contract.
[FFT calibration](../../../../../skills/audio-fft-spectrum/SKILL.md) ·
[Window selection](../../../../../skills/audio-window-functions/SKILL.md)

| Question | Useful stimulus and failure to check |
| --- | --- |
| Are scale and leakage handled? | Use a coherent tone and a deliberate off-bin tone at stated phases. A short burst or taper changes the expected spectrum and the measurement support. |
| Where is the response in time? | Use a known impulse with head and tail guard samples. At reduced level, repeat to see whether the inferred response scales. A single impulse may have too little energy for a quiet path. |
| Which products appeared? | Use two or more known tones. Choose their frequencies to separate the expected products on the chosen grid. Report gain and phase per tone. The sum of peak amplitudes bounds the absolute mixture before downstream processing. |
| Does response vary with frequency? | Use a sweep with the rate law, duration, start phase and valid frequency range declared. Keep the exact inverse or excitation model and a guard for the response tail. |
| Can an estimator distinguish noise from missing input? | Use known silence, seeded noise, and a separate discontinuity case. Report noise distribution, level, bandwidth and reproducibility. |

### Specify the sweep and its verification domain

For an exponential up-sweep from $f_0$ to $f_1$, over
$0\le t<T$, set $g=\log(f_1/f_0)$ and
$\phi(t)=2\pi f_0T[\exp(gt/T)-1]/g$. The derivative divided by
$2\pi$ is $f_0\exp(gt/T)$. Use a stable evaluation of
$\exp(z)-1$ near zero. The last PCM sample is earlier than $T$.
Choose the sweep limits below Nyquist with guard for the
intended measurement. A fade is part of the signal model.
Check common duration and phase conventions when comparing tools.

Sweep-based estimation needs the matching inverse and enough
observed tail. Under the model described by Farina, an
exponential sweep permits separation of responses associated
with harmonic distortion orders. Validate that separation with a
known linear filter and a known nonlinearity before interpreting a
new capture. The sweep's valid excitation band and the inverse's
noise gain limit where a result is useful.
[Farina (2000), §§2–3](https://angelofarina.it/Public/Papers/134-AES00.PDF) ·
[Muller and Massarani (2001)](https://publications.rwth-aachen.de/record/192865)

### Executed checks and portable fixtures

| Probe | Verified result |
| --- | --- |
| Use 48 kHz, 4,800 samples, $k=100$, $A=0.5$ and zero phase. Start at $2^{60}+37$. Render once, then in blocks of 97, 233, 1,024, 611 and 2,835 samples. | Both renders are identical. RMS is 0.3535533905932738 and the one-sided peak amplitude at bin 100 is 0.5. |
| Use $k=2400$ and $A=0.5$ with phase 0 and then $\pi/2$. | The first frame is zero to within `1e-15`. The second alternates +0.5 and −0.5. |
| Sum two cosine-phase components at bins 100 and 137 with peak amplitudes 0.25 and 0.125. | The sum reaches its 0.375 bound at sample zero. |
| Render a 100 to 8,000 Hz logarithmic sweep, 0.25 s at 48 kHz, with no fade. | The integrated-phase sine and SciPy 1.17.0 logarithmic chirp with a −90° cosine phase agree within `2.47e-12` in sample amplitude. The final nominal instantaneous frequency is about 7,997.079 Hz. |

These checks verify digital stimulus construction and comparator
agreement. Actual playback level, device response, and the
deconvolution of a captured sweep have separate acceptance checks.
[SciPy 1.17.0 chirp](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.signal.chirp.html)

## Next action

Build the stimulus-description and bounded render procedure
around the existing fixture bank. Include an impulse, coherent
and off-bin tone, headroom-constrained tone mixture, and a sweep
with stated support. Keep deterministic expectations separate
from real loopback and device checks.

## Revisit when

The epoch, rate, amplitude reference, waveform profile, generator
algorithm, or measurement objective changes.
