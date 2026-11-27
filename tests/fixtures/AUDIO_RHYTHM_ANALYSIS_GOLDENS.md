# Audio rhythm analysis fixtures

Use exact doubled sample coordinates. Unless specified, use 48 kHz.
Preserve the declared capture support, voice, event and anchor
identity, and data boundaries.
[Contract](../../skills/audio-rhythm-analysis/references/RHYTHM_ANALYSIS_CONTRACT.md) ·
[Regression checks](../test_audio_rhythm_analysis_reference.py) ·
[Research](../../memory/projects/kisuul/kestrelgaming/handoffs/2026-11-26-audio-rhythm-analysis-research-r01.md#executed-checks-and-portable-fixtures)

## Local geometry and grid ambiguity

| Fixture | Expected result |
| --- | --- |
| Anchors $[0,24000,45600,69600]$. First events $[12000,34800,57600]$, then $[16000,38400,61600]$. | The straight and swung phases are $1/2$ and $2/3$ on all three beats. With one labelled offbeat each, their ratios are 1 and 2. |
| Keep the same events and impose fixed 23200-sample spacing from zero. | Straight ratios become $15/14,1,14/15$. Swung ratios become $20/9,19/10,19/10$. |
| Event at 16000 and anchors at 0 and 24240. Check subdivision 3. | Phase $200/303$, ratio $200/103$, residual $-160$ samples to slot 2. |
| Event at 24000 with the local grid above, and one at 69600. | The first maps to phase zero of the second beat. The last has no right anchor. |
| Use origin $2^{60}+37$ and an event at offset $23999.5$. Use subdivision 4. | Phase $47999/48000$. The closest slot is zero of the next beat, with residual $-1/2$ sample. |
| Event at 6000 in beat $[0,24000)$ and $q=2$. | Tie at signed residuals $6000$ and $-6000$. Inclusive tolerance 6000 admits one event with ambiguous slot support. |
| Doubled sample anchors 100 and 105 with event at 101 and $q=3$. | The nearest slot is at doubled position $305/3$. Residual $-1/3$ sample, or $-2/15$ beat. |
| Sixteen midpoint events on distinct beats. Add one event at a quarter beat. | At zero tolerance, grids 2 and 4 give 16 and 17 matches with equal coverage. Only one beat supports the extra quarter slot. |
| Two same-voice events coincide, a different voice falls between them and a later event, and a capture gap follows. | Keep a zero IOI and the later same-voice interval. Keep each capture and voice separate. |
| Label two interior offbeats in one voice and beat. Add a single interior offbeat in a second voice. | The two competing labels remain ambiguous. Measure the second voice's independent ratio. |

## Merged timing seam

At origin $2^{60}+37$, use periodic Hann $M=N=960$, hop 480, lag one,
two right frames, four preceding scores, and margin 0.01. For a
pulse at frame $t$, place a unit impulse at offset $480t+480$.
Feed the analytically calibrated amplitude spectrum and weighted
RMS from each real window into Skill #36. Track beats with period
50 and a 48,000-sample support cap.

- With 400 complete frames, inject pulses at 20, 70, 120, 320,
  and 370. The beat spans are 20–120 and 320–370. The onset
  interval across the quiet section is 96,000 samples. A probe
  at frame 170 has unavailable beat phase.
- With 350 complete frames, inject pulses at $7+50j$ for
  $j=0\ldots6$ with $j=3$ omitted. The first onset is ready
  at offset 5280. Measure its phase using the first two beat
  anchors. The result requires the beat run through offset
  168480. The midpoint between 107 and inferred beat 157
  maps to $1/2$ when inferred anchors are accepted.
- For known event and anchor data boundaries, check that the
  maximum controls readiness. Exercise an unavailable component
  and an optional measured delivery boundary.

## Period evidence

In 800 frames at 100 Hz, use unit pulses at $7+50j$ for
$j=0,\ldots,15$. Raw linear autocorrelation at lags 25, 50, and 100
is $0,15,14$. The mean products at lags 50 and 100 are equal to
0.02. Rectangular Fourier magnitudes at 120 and 240 BPM are both
16. Applying a periodic Hann makes both magnitudes 8. Use the
declared pulse level and anchor evidence to interpret the rates.
