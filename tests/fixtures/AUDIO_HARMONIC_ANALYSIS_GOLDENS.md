# Harmonic analysis fixtures

These cases use one calibrated, one-sided FFT peak-amplitude frame. The
reference keeps the measured bin amplitude when it refines a frequency.
Compare the measured frequencies to the known stimulus. Status, order, and
bin assertions are exact. Each frequency tolerance applies to its fixture.

## Peak arithmetic and endpoints

| Case | Independent expected result |
| --- | --- |
| Three magnitudes from $\exp[-1.75(k-\delta)^2]$, $k=-1,0,1$, $\delta=-0.37,0,0.37$ | The fit recovers $\delta$ within $2\times10^{-15}$ bins. A half-bin offset has two equal maxima. |
| Eight rectangular samples $x[n]=(0.5+2\cos\theta_n+\cos 2\theta_n)/8$, $\theta_n=2\pi n/8$ | The raw DFT magnitude triplet at bin 1 is $(0.5,1,0.5)$. A naive fit to the calibrated bins shifts by $+1/6$ bin. Multiplying $x[n]$ by $(-1)^n$ mirrors the triplet around bin 3 and shifts the naive fit by $-1/6$ bin. Require both coarse results. |
| Peak at bin 3 with neighbors at bins 2 and 4 | With $N=8$, the right flank is unpaired Nyquist. With $N=9$, both flanks are paired and a strict positive maximum can be refined. The $N=9$ bin 4 itself has no right flank. |
| Center $2^{-40}$ with neighbors one and two representable steps below it | Separate logs coincide in the tested runtime. The relative logs give an offset of $-1/6$ bin. |
| Zero flank, tied plateau, silence, or invalid ordinate | Expect coarse with a reason, unresolved plateau with a bin interval, no candidates, or rejection, respectively. |

## Tone frequency and resolution

Use a periodic Hann window at 48 kHz. The native grid for $M=2048$ has
23.4375 Hz spacing. For an isolated unit-peak cosine, use frequency
$(173+d)\,48000/2048$ and phase $0$, $0.7$, or $1.9$ rad. The audited
sweep used offsets $-0.49$ through $0.49$ in steps of $0.01$ and compared
297 frequencies per FFT length. The maximum errors in hertz were
0.375163722, 0.038053080, 0.004555196, and 0.000563807 at FFT lengths 2048,
4096, 8192, and 16384. The maintained suite checks representative 4× cases
against the known frequencies with a 0.005 Hz bound for this fixture.
[PR #29 sweep](https://github.com/Kisuul/KestrelGaming/blob/e2e622d9644dad922a079653b9301826f73c4919/memory/projects/kisuul/kestrelgaming/handoffs/2026-11-20-audio-harmonic-analysis-research-r01.md#reproducible-checks)

For the following case, use unit-peak cosines at 4054.6875 and 4062.890625 Hz.
Use initial phases 0 and $0.65\pi$ rad. Keep $N=16384$ and a floor of half the
largest bin. At both lengths the search reports two peaks. Use known
frequencies as the oracle and a 0.1 Hz resolution bound for this comparison.

| Window length | Absolute errors in ascending peak order | Result |
| ---: | --- | --- |
| 2048 | 18.096646 Hz and 18.097616 Hz | Both estimates fail the bound |
| 16384 | 0.009617 Hz and 0.040635 Hz | Both estimates pass the bound |

With zero phase for both tones, the shorter window gives one peak at
$N=2048$ and at $N=16384$. For a weak-partial fixture, use $M=2048$, $N=8192$,
frequencies 4054.6875 and 4195.3125 Hz, peak amplitudes 1 and 0.1, and
initial phases 0 and 0.7 rad. A floor of 0.05 retains both candidates.
Half the largest bin retains one. The weak candidate's measured bin
amplitude is 0.1 and its frequency error is about 0.642 Hz. The maintained
tests evaluate the periodic Hann response with a finite geometric sum.

## Assignment and coverage

Use $f_0=100$ Hz, $\alpha=1/10$, band $[50,505)$ Hz, and orders 1 through 6.
Use the measured frequency and amplitude pairs
`(90,.4), (110,.7), (198,.9), (201,.2), (299,.6), (301,.6), (411,1)`.
The results stay the same when the input peaks are reversed.

| Order | Expected report | Residual or coverage |
| ---: | --- | --- |
| 1 | 110 Hz matched | +10 Hz, full gate |
| 2 | 201 Hz matched | +1 Hz, full gate |
| 3 | 299 Hz matched | −1 Hz, full gate |
| 4 | Missing | 411 Hz exceeds its gate |
| 5 | Partial band | The search band ends inside its gate |
| 6 | Out of band | The target lies above the band |

The result has three matches, five eligible targets, and four full gates.
With band $[90,110)$, frequency 110 Hz is outside the band. The unmatched
100 Hz target has a clipped gate. The gate with $\alpha=1/10$ includes 90 and
110 Hz when both belong to the band. The next binary64 value outward at
each edge fails the exact membership check. With $h=3$ and $\alpha=1/20$,
binary64 `f0=442.1, peak=1304.1950000000002` is inside. Binary64
`f0=110.1, peak=324.79499999999996` is outside.

Peaks at 440, 660, and 880 Hz match orders 2, 3, and 4 for supplied
$f_0=220$ Hz. They also match orders 4, 6, and 8 for supplied $f_0=110$ Hz.
The residuals are zero in both cases. The first order is absent in both.

## Agent review tasks

1. Give the agent the two equal-count spectra. Ask if both demonstrate
   resolution of the known 8.203125 Hz pair. Require the agent to trace the
   observation length and compare peak locations with the stimulus.
2. Give the agent an apparent low-bin drift. Ask for the raw and calibrated
   flank values. Require a checked explanation of the endpoint scale.
3. Give the agent the three peaks at 440, 660, and 880 Hz. Ask it to compare
   the two supplied fundamentals and state the measured order coverage.
   Use pitch estimation from an unlabeled recording as a routing check.

These tasks define behavioral trials. The automated tests cover arithmetic
and the peak-to-assignment workflow.
