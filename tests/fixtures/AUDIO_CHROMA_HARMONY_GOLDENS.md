# Audio chroma and harmony fixtures

[Reference](../../skills/audio-chroma-harmony/scripts/reference_chroma_harmony.py) ·
[Contract](../../skills/audio-chroma-harmony/references/CHROMA_HARMONY_CONTRACT.md) ·
[Executable checks](../test_audio_chroma_harmony_reference.py)

Use A440, C as class zero, and squared cosine for the
template tests. Compare exact coordinates and ratios exactly.
Use tolerances for frequencies generated with exponentials,
logarithms, or a floating-point transform.

## Pitch and power

| Probe | Expected evidence |
| --- | --- |
| A3, A4, A5 with masses 2, 1, 4. | Class 9 holds 7. All other masses are zero. |
| Unit point at MIDI 71.75 and at $-0.25$. | B gets $1/4$ and C gets $3/4$. Transpose by one semitone to rotate the vector by one class. |
| Exact MIDI pitch 72 and its binary64 neighbors. | At 72, all power goes to C. A point just below shares between B and C. A point just above shares between C and C-sharp. |
| Frequencies one binary64 step below and above 440 Hz. | Retain positive mass in the appropriate neighbor of A. Sum both assignments to the input total. |
| Band $[220,880]$ and point floor 2. In Hz, supply points $(0,5),(100,3),(220,2),(440,1/2),(880,4),(881,1)$. | DC power 5, outside-band 4, below-floor $1/2$, admitted 6. The accepted centers include 220 and 880. Class A holds 6. |
| Deliver twenty samples for a nominal 64-sample frame. Then supply complete silence or DC only. | The partial frame has no tuned vector or ready boundary. Complete frames have zero admitted mass, a zero vector, and empty rankings. |

For the even PSD probe, use 64 rectangular samples at
3,520 Hz with $x[n]=0.125+0.4\cos(2\pi\,8n/64)+0.2(-1)^n$.
The merged PSD gives 55 Hz spacing and power 0.015625 at
DC, 0.08 at 440 Hz, and 0.04 at the 1,760 Hz Nyquist.
Total power is 0.135625. After excluding DC, A holds
approximately 0.12. Keep the numerical tolerance for the
small residual from the transform. For an odd transform, use
63 samples at 3,465 Hz with $x[n]=0.2\cos(2\pi\,31n/63)$.
The last positive bin at 1,705 Hz holds 0.02 power.

## Chord and bass decisions

| Input | Expected evidence |
| --- | --- |
| Equal masses at C, E and G. | C major is unique at $S=1$ on exact pitch classes. |
| Equal masses at C and G. | C major and C minor tie at $S=2/3$. |
| Equal masses at C, E, G and A. | C major and A minor tie at $S=3/4$. |
| Same four classes with G raised to $4097/4096$. | The squared margin is $3511/28764453$. Include A minor at equality or with margin $1/8000$. |
| All twelve classes with equal mass. | All 24 templates tie at $S=1/4$. |
| Scale the C, E and G masses by $10^{-6}$. Set an absolute floor of $10^{-3}$. | Their shape has the same candidate scores before gating. The complete frame is below the absolute floor. Preserve the raw mass. |
| C4–E4–G4 and E3–G3–C4 with matched weights. | Both have the same chroma. Independent bass observations C4 and E3 yield inversion indices 0 and 1. Without bass evidence the inversion field is unset. |
| Equal masses at harmonics 1, 3 and 5 of a single C4. | Leading C-major squared score is about 0.9889659210. Inspect the known source to distinguish partial evidence from separate fundamentals. |

## Tuning and timing

Use C4, E4 and G4 on an A442 grid. The wrapped tuning
offset from A440 is about $+7.85141504$ cents. The declared
A442 grid and an A440 estimate with a lift of zero agree
within numerical tolerance. The nominal A440 result
spreads about 0.235542 of the total mass 3 into neighboring
higher classes. Applying both corrections spreads the same
mass into lower classes.

For a true $+55$ cent displacement, the tuning reference
returns a wrapped value near $-45$. Its best relative
candidate is C-sharp major. Keep the absolute label
unavailable until the caller supplies a lift. A lift of
one selects a $+55$ cent correction and C major. Equal
evidence at $-25$ and $+25$ leaves tuning ambiguous.

Use $O=2^{60}+37$ and frame support $[O+20,O+60)$, ready at
$O+63$ and delivered at $O+66$. Fit tuning within the same
epoch with readiness at $O+128$ and delivery at $O+140$.
Give a separately qualified bass with support
$[O+39,O+41)$, ready at $O+146$ and delivered at $O+158$.
The center twice is $2O+79$. The full result is ready at
$O+146$ and the evidence delivery is $O+158$. The delivery
becomes unknown if an in-scope dependency omits it.
For a 65-sample frame at $O$, the center is $O+32$.
Bass support ending there falls outside the half-open
condition. Bass support starting there qualifies.

When nominal 48,000 Hz and actual 48,004.8 Hz generate
the tuning factor $10001/10000$, provide a nominal bin or
peak at $440/(10001/10000)$ Hz. It lands exactly at 440 Hz
after correction. A band of $[440,440]$ admits the corrected
point. The original frequency, power and support survive.

## Resolution and evaluation

At 48 kHz combine E2 at about 82.406889 Hz and F2 at
87.307058 Hz with amplitudes 0.4 and 0.1. Set phase zero
at the frame center for each cosine. Use symmetric Hann
windows with 2,048 or 48,000 observed samples and a padded
transform of 262,144 points. At a prominence floor of 10%
of peak magnitude, inspect the 70–100 Hz range. Expect
one peak near 83.49609 Hz for the short frame and two near
82.39746 and 87.34131 Hz for the long frame.

For time-weighted pooling, clip the disjoint cells
$[O,O+300)$ and $[O+300,O+480)$ to $[O+120,O+420)$.
Their admitted lengths are 180 and 120 samples. Moving
the second start to $O+330$ gives coverage $9/10$ and mean
weights $2/3$ and $1/3$. Preserve the original transform
window supports separately.

For interval scoring, label C major on $[0,2)$ and G major
on $[2,4)$. Estimate C major on $[0,1)$ and G major on
$[1,3)$. The overlap with a correct label lasts 2 units.
The covered duration is 3 of 4 units. Agreement on covered
time is $2/3$, or $1/2$ if the missing duration is scored
as missed. Declare the policy with the score.
