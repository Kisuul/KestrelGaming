# Independent programme loudness fixtures

Freeze these expectations from [EBU Tech 3341 v4, Table 1 (11/2023)](https://tech.ebu.ch/docs/tech/tech3341.pdf)
and [ITU-R BS.1770-5, Annex 1 (11/2023)](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I%21%21PDF-E.pdf).
The values below are published requirements or independent arithmetic.
The Python filter is specified by the ITU tables and has no fit parameters.

## Tech 3341 Table 1, cases 1–14

Tones are 1 kHz. Stereo tones are in phase with the stated peak dBFS **in
each channel**. Each expected value has the published tolerance ±0.1 LUFS.
For maxima, use complete windows. The rows for live cases describe the
signal and window readings an offline reference can check.

| Case | Signal | Expected LUFS |
| --- | --- | --- |
| 1 | Stereo, 20 s at −23 dBFS | M, S, I −23 |
| 2 | Stereo, 20 s at −33 dBFS | M, S, I −33 |
| 3 | Stereo, 10 s −36, 60 s −23, 10 s −36 | I −23 |
| 4 | Stereo, 10 s −72, 10 s −36, 60 s −23, 10 s −36, 10 s −72 | I −23 |
| 5 | Stereo, 20 s −26, 20.1 s −20, 20 s −26 | I −23 |
| 6 | 5.0, 20 s, L/R −28, C −24, LS/RS −30 | I −23 |
| 7 | Stereo authentic programme with narrow loudness range | I −23 |
| 8 | Stereo authentic programme with wide loudness range | I −23 |
| 9 | Stereo, 1.34 s −20 then 1.66 s −30, repeated five times | S −23 after 3 s |
| 10 | Twenty files, `i × 150 ms` silence, 3 s −23, 1 s silence, `i=0..19` | Max S −23 per file |
| 11 | Twenty segments, `i × 150 ms` silence, 3 s at `−38+i`, silence to 6 s total | Max S `−38+i` per segment |
| 12 | Stereo, 180 ms −20 then 220 ms −30, repeated 25 times | M −23 after 1 s |
| 13 | Twenty files, `i × 20 ms` silence, 400 ms −23, 1 s silence, `i=0..19` | Max M −23 per file |
| 14 | Twenty segments, `i × 20 ms` silence, 400 ms at `−38+i`, silence to 800 ms total | Max M `−38+i` per segment |

Use the [EBU Loudness Test Set v5.0](https://tech.ebu.ch/publications/ebu_loudness_test_set)
for original recordings, including cases 7 and 8. Follow the published use
terms. Keep the original ZIP outside the repository and do not distribute its
audio. Use the release archive's README to resolve variants and layout.
Seq 6 includes a five-channel L/R/C/LS/RS PCM file and a six-channel
WAVE_FORMAT_EXTENSIBLE version with silent LFE. The 2011 v02 files for cases
3, 4, 5 and 8 use the −10 LU relative gate. Cases 15–23 test true peak and
Tech 3342 tests LRA. Neither measurement belongs to this reference.

## ITU and independent arithmetic

- BS.1770-5 Annex 1 §2 uses a 997 Hz unit-peak sine on L, C, or R as an
  approximately −3.01 LKFS alignment check. The analytical steady-state
  response of the two supplied transfer functions predicts about −3.0103.
- For gate arithmetic alone, use equal-length blocks with already weighted
  readings `[-23, -40, -23, -40]` LUFS. The absolute-gated energy mean reads
  −25.9244999643 LUFS. The relative threshold is −35.9244999643 LUFS, so the
  two −23 blocks survive and their energy mean reads −23.0 LUFS. The arithmetic
  mean of the four displayed values is −31.5 LUFS. It measures a different
  quantity. This input does not specify a realizable sequence of overlapping
  PCM windows.
- For a relative-gate equality test, give the gate RMS roots `1`, `2`, `5`.
  Their squares average to 10, so the relative threshold is exactly power 1
  in real arithmetic. Only roots 2 and 5 pass. Test neighboring binary64
  candidates on both sides in the representation the algorithm compares.
- The [ITU BS.2217-2 report](https://www.itu.int/pub/R-REP-BS.2217-2-2016)
  and [audio files](https://www.itu.int/oth/R1102000001) provide separate
  external test material. Inspect the case edition and expected response
  before making a conformance claim.

## Observed offline results

Test sequences © EBU. The [fixture checker](../../skills/audio-program-loudness/scripts/check_ebu_loudness.py)
ran with Python 3.12.14 on the v5.0 ZIP from the EBU publication page. ZIP
SHA-256 was `9cc500b4df83f7c21855c74dce795ef5209a752bf884253ae57d0ce512efb062`.
Use the separately obtained archive with Python 3.12 or later.

```sh
python3 skills/audio-program-loudness/scripts/check_ebu_loudness.py /path/to/ebu-loudness-test-setv05.zip
```

| Cases | Original files passed | Largest absolute error (LU) |
| --- | ---: | ---: |
| 1–2, steady stereo M/S/I | 2/2 | 0.046486 |
| 3–6, stereo gating and 5.0/5.1 I | 5/5 | 0.020971 |
| 7–8, authentic programme I | 2/2 | 0.013841 |
| 9–11, short-term windows and maxima | 22/22 | 0.013733 |
| 12–14, momentary windows and maxima | 22/22 | 0.039556 |
| Total | 53/53 | 0.046486 |

For cases 11 and 14 the checker takes the maximum of windows contained in
each authored segment of the continuous file. These checks exercise the
window outputs offline. Live transport, display, pause and reset controls
require separate tests. The original six-channel case 6 WAV declares its
RIFF end 12 bytes before the end of its `data` chunk. The checker reads that
last PCM frame directly and leaves the archive intact.

The I values for cases 1–8, including both case 6 layouts, were compared with
libebur128 1.2.6 (`EBUR128_MODE_I`, explicitly mapped channels, no histogram)
and FFmpeg 7.1.5-0+deb13u1 `ebur128` (explicit matching channel layout, final
I from 0.001 LUFS metadata). Maximum absolute differences were
`9.363e-11 LU` and `0.006859 LU`, respectively. For example, run FFmpeg on
case 7 with the declared stereo layout.

```sh
unzip -p /path/to/ebu-loudness-test-setv05.zip seq-3341-7_seq-3342-5-24bit.wav |
  ffmpeg -v error -ch_layout stereo -i pipe:0 \
    -af 'ebur128=metadata=1,ametadata=mode=print:key=lavfi.r128.I:file=-' -f null -
```

SciPy 1.17.0 `freqz` with NumPy 2.3.5 supplied separate steady-state filter
expectations at 25, 100, 500, 2,000, 10,000 and 16,000 Hz. Those checks
verify the implemented response of the supplied coefficients. Official file
testing here covered EBU loudness cases 1–14. Full ITU BS.2217 testing and
full EBU Mode coverage require more evidence.
