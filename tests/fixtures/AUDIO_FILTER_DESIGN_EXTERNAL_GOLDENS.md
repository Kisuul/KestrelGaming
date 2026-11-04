# Filter-design independent SciPy golden vectors

**External provenance:** Independently computed via NumPy **2.3.5** / SciPy **1.17.0**, separate from Kestrel's pure-stdlib filter implementation, on 2026-11-04. The [standard-library tests](../test_audio_filter_design_reference.py) hold **frozen literals**; they do not call SciPy during GitHub CI. These values compare finite numerical implementations of the *same intended window-method FIR and Butterworth 2-pole design*; they are not independent evidence that the shared design choice is acoustically optimal or satisfies a continuous-band performance requirement.

To independently reproduce the FIR values and biquad, with specified SciPy/NumPy versions:

```python
from scipy import signal
import numpy as np
import scipy
print(np.__version__, scipy.__version__)
fs = 48000
for taps, kind, edge in [
    (31, "lowpass", 3000),
    (31, "highpass", 3000),
    (65, "bandpass", (2000, 6000)),
    (65, "bandstop", (2000, 6000)),
]:
    coeffs = signal.firwin(taps, edge, window="hamming",
                           pass_zero=kind, fs=fs, scale=True)
    print(kind, [repr(float(x)) for x in coeffs[:5]],
          repr(float(coeffs[taps//2])))
print("butter", signal.butter(2, 3000, btype="lowpass",
                              output="sos", fs=48000))
```

The frozen values (in the corresponding test file) are the **first five FIR coefficients and center coefficient** of each filter. The 2nd-order Butterworth 3 kHz, 48 kHz sample-rate, low-pass section has approximately `(b0,b1,b2,a1,a2) = (0.02995458,0.05990916,0.02995458,-1.45424359,0.57406192)`, with its omitted denominator `a0` normalized to 1. The external Butterworth values are rounded in the frozen fixture and compared with 1e-8 absolute amplitude tolerance; the FIR coefficients use 3e-13 absolute tolerance. These are small empirical margins, **not** worst-case proof for all coefficients or inputs.

Separately, [the optional live SciPy checker](../../skills/audio-filter-design/scripts/check_scipy_filter_design.py) reconstructs multiple seeded designs and compares full FIR and SOS coefficients, 6-point complex responses for each design, streamed synthetic signals, and local phase-delay values. This live checker is *not required in standard CI* and must be reported as unrun in environments that lack SciPy/NumPy. It does not test actual DAW, browser, hardware or realtime performance.

See the [filter design contract](../../skills/audio-filter-design/references/FILTER_DESIGN_CONTRACT.md) and [math verification procedure](../../skills/math-verification/SKILL.md) for independence and interpretation caveats.
