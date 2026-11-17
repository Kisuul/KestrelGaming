# Audio envelope dynamics — independently defined fixtures

## Provenance and precision

These are mathematical consequences of a **declared Kestrel one-pole model**, not EBU/IEC instrument targets. Values are frozen before reference verification using `Decimal` with at least 80 decimal digits, and are rounded here for readability. The stated contract uses a nonnegative amplitude envelope, `one_e` attack/release and `fs=1000 Hz` unless a row says otherwise. The [reference contract](../../skills/audio-envelope-dynamics/references/ENVELOPE_DYNAMICS_CONTRACT.md) defines units and sample clocks. A `1/e` time of 0.1 s contains 100 samples, whose final index is `origin+99`.

| Scenario | Independent expression | Expected numerical value |
| --- | --- | --- |
| One-sample attack coefficient, `tau=0.1` | `1-exp(-1/100)` | `0.00995016625083194642609` |
| Peak step `0 -> 1`, after 100 samples | `1-exp(-1)` | `0.63212055882855767840448` amplitude |
| Peak release `1 -> 0`, after 100 samples | `exp(-1)` | `0.36787944117144232159552` amplitude |
| Exponential RMS step `0 -> 1`, after 100 samples | `sqrt(1-exp(-1))` | `0.79506009762065010729577` RMS amplitude |
| Exponential RMS first sample | `sqrt(1-exp(-1/100))` | `0.09975052005293980634533` RMS amplitude |
| 90%-rise convention after `T=0.1 s` | `1-exp(-ln(10))` | `0.9` amplitude |
| −60 dB residual convention after `T=0.1 s` | `exp(-ln(1000))` | `0.001` amplitude residual |
| Gain-reduction step `0 -> 12 dB` after 100 samples | `12*(1-exp(-1))` | `7.58544670594269214085371` dB attenuation |
| Applied gain at previous checkpoint | `10**(-12*(1-exp(-1))/20)` | `0.41756843772092928605487` linear gain |
| Compressor `L=-10 dBFS, T=-20 dBFS, R=4` | `-(1-1/4)*10` | `-7.5 dB` gain request |
| Downward expander `L=-30 dBFS, T=-20 dBFS, R=2` | `-(2-1)*10` | `-10 dB` gain request |

Analytic invariants: `|x| == |-x|`; a DC magnitude is not zero; opposite-polarity stereo does not cancel under `independent` or `max`; linked channel order must not affect the shared envelope; with `tau=0` the result equals target **exactly**; the empty callback leaves state unchanged. A one-pole amplitude follower and a one-pole **energy** follower do not have the same step profile.

## Precision and exclusions

Use independent real-number expressions (e.g. `Decimal` exponential/square-root with a separately specified coefficient) to derive checkpoints. Compare finite binary64 outputs to appropriate test-specific tolerances; do not use an `epsilon` to select branches or treat formatted dB values as exact decision inputs. At the strict target/state equality boundary the reference reports `steady`. Extremely long positive time constants may have nonzero update weight but an unchanged rounded output sample; exact arithmetic cannot recover a change smaller than the state representation's resolution.

This fixture bank does **not** validate stereo image audibility, true-peak safety, production compressor design, physical VU/PPM meters, Web Audio compatibility, or algorithmic loudness.

Sources: [AES tutorial](https://aes.org/publications/elibrary/elibrary-page/?id=16354), [JUCE ballistics](https://docs.juce.com/master/classjuce_1_1dsp_1_1BallisticsFilter.html), [W3C Web Audio](https://www.w3.org/TR/2026/WD-webaudio-1.1-20260922/). Source implementations have different time conventions and are not an exact golden oracle for this custom model.
