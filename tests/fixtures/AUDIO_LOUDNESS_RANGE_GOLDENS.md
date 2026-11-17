# EBU Tech 3342 Loudness Range test targets

Source: EBU Tech 3342 v4 (November 2023), §4 Table 1 and the repeat rule below
the table. [EBU publication](https://tech.ebu.ch/publications/tech3342)

| Case | Stereo material | EBU v5.0 ZIP entry | LRA (LU) |
| --- | --- | --- | ---: |
| 1 | 20 s at −20, 20 s at −30 dBFS | `seq-3342-1-16bit.wav` | 10 ±1 |
| 2 | 20 s at −20, 20 s at −15 dBFS | `seq-3342-2-16bit.wav` | 5 ±1 |
| 3 | 20 s at −40, 20 s at −20 dBFS | `seq-3342-3-16bit.wav` | 20 ±1 |
| 4 | 20 s each at −50, −35, −20, −35, −50 dBFS | `seq-3342-4-16bit.wav` | 15 ±1 |
| 5 | Narrow-range excerpt | `seq-3341-7_seq-3342-5-24bit.wav` | 5 ±1 |
| 6 | Wide-range excerpt | `seq-3341-2011-8_seq-3342-6-24bit-v02.wav` | 15 ±1 |

The tones are 1 kHz with the same phase in both channels. The levels in the
table are the peak levels of each channel. The expected response also
applies when you repeat the entire signal. Start a new measurement for
each repetition count and keep filter and window state between copies.

Obtain the original [EBU Loudness Test Set v5.0 ZIP](https://tech.ebu.ch/publications/ebu_loudness_test_set).
Test sequences © EBU. The file names are from the original ZIP and its README.
The byte identity matches the archive already pinned in the
[Skill #20 ledger](AUDIO_PROGRAM_LOUDNESS_OFFICIAL_GOLDENS.md).

```text
SHA-256 9cc500b4df83f7c21855c74dce795ef5209a752bf884253ae57d0ce512efb062
```

Run the [offline checker](../../skills/audio-loudness-range/scripts/check_ebu_lra.py)
on that ZIP. The checker measures one and two copies of each case, with
1.5 s of analysis silence after the final copy. The ±1 LU tolerance applies
to this corpus. The arithmetic tests below have their own exact expectations.

## Independent short-term vectors

The inputs below are synthetic ungated short-term readings in LUFS. The
expected counts and order statistics follow from §5 of Tech 3342.

| Input | Expected result |
| --- | --- |
| An empty vector, all `-inf`, or finite values strictly below −70 mixed with `-inf` | In order: insufficient data, silence, below absolute gate |
| Binary64 predecessor of −70, −70, and its successor | Two absolute and final survivors, P10 = −70 and P95 = the successor |
| Ten values at 0, nine at 10, and two at 30 | The powers are 1, 10 and 1,000. The sum is 2,100 for 21 windows, so 0 LUFS is exactly at the −20 LU relative gate. All 21 survive. LRA = 30 LU. |
| Move all ten zeros in that vector to the next lower or higher binary64 number | 11 survivors below the tie and 21 above it. The LRA is 20 and 30 LU respectively to binary64 rounding. |
| Six consecutive integer levels from −26 to −21 | P10 uses index 1 because `0.10 × 5 = 0.5`. P95 uses index 5. LRA = 4 LU. |
| 31 levels from −40 to −32.5 in 0.25 LU steps | P10 uses index 3 and P95 uses index 29 because `0.95 × 30 = 28.5`. LRA = 6.5 LU. |
| One −10 among 100 values at −20 | Both percentiles are −20. LRA = 0 LU. |
| 100 readings at −15 appended to 10 readings at −50 | The previous −50 readings now fall below the relative gate. All 100 surviving readings are −15. |

The near-zero neighboring cases exercise input differences that disappear
if the implementation makes a gate decision from a rounded LUFS threshold.
The PCM tests check a fixed partition, their exact sample coordinates, and
the effect of EOF padding. The corpus above supplies an independent
end-to-end PCM check.
