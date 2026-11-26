---
schema: 1
id: 2026-11-26-audio-color-scale-design-research-r01
kind: handoff
scope: project:kisuul/kestrelgaming
status: active
evidence: observed
author: VeNerVRA
created: 2026-11-26
updated: 2026-11-26
sources: "Audio branch a435c790546b7aefc8ba35ba18be1d7c235f916f; Crameri et al. (2020); Matplotlib colormap guidance; W3C WCAG 2.2; executed normalization and sRGB contrast checks."
---

# Skill 71 research for color scale design

## Summary

**Task outcome:** COMPLETE

Map analysis values to colors with a declared range,
unit, and reference. Use a stable mapping for comparisons.
Make level, sign, and data availability recoverable with
labels or other cues. The fixtures expose an autoscale
that hides a 40 dB difference and a contrast threshold
that an early rounding step can misclassify.
[Crameri et al. (2020)](https://doi.org/10.1038/s41467-020-19160-7) ·
[WCAG 2.2 use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html)

## Evidence

### Match color to the quantity

| Display quantity | Palette and scale requirement |
| --- | --- |
| Ordered level or energy | Use a sequential map with an ordered lightness progression. State the unit, range and reference, including the floor for logarithmic values. |
| Signed difference about a meaningful reference | Use a diverging map with a distinct center at the reference. Set both sides from the comparison semantics and label their endpoints. |
| A wrapped angle such as phase | Use a cyclic map with a continuous seam where the endpoint angles are equivalent. Mark the direction and label the angle. |
| Named classes | Use distinct qualitative colors with labels or shapes. Keep class identities stable across views. |

Evaluate the chosen ramp at its output quantization and
in the presentation colorspace. Inspect lightness
progression and legibility, including color vision
deficiency. For an absolute comparison, use one
normalization, palette and reference on all views.
An adaptive view needs its visible range and mode.
Distinguish a valid zero or a value below the display
floor, a value above the displayed range, and a
missing result. A color at an endpoint does not convey
which state produced it. Give support and status a
label, pattern, outline, or textual equivalent when
they carry meaning.
[Crameri et al. (2020)](https://doi.org/10.1038/s41467-020-19160-7) ·
[Choosing colormaps](https://matplotlib.org/stable/users/explain/colors/colormaps.html) ·
[Visualization integrity](2026-11-26-audio-visualization-integrity-research-r01.md)

### Check contrast for the presentation

Use the actual composited sRGB colors for legend text,
grid lines and essential marks. For each normalized
sRGB component $c$, use linear value $c/12.92$ for
$c\le0.04045$ and $((c+0.055)/1.055)^{2.4}$ otherwise.
Compute relative luminance with linear RGB weights
$(0.2126,0.7152,0.0722)$. The contrast ratio is
$(L_\mathrm{light}+0.05)/(L_\mathrm{dark}+0.05)$.
Apply the criterion to the relevant pair. WCAG 2.2
uses 4.5:1 for normal text under 1.4.3 and 3:1
for applicable UI states and required parts of graphics
under 1.4.11, subject to their stated exceptions.
Compare before rounding. Check actual themes and
adjacent colors for the required elements.
[WCAG 2.2 contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) ·
[WCAG 2.2 non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)

### Executed checks and portable fixtures

Use $t=\operatorname{clip}((x-a)/(b-a),0,1)$ for a
finite level $x$ on the declared range $[a,b]$, with
$b>a$. The probe computes coordinates before palette
lookup.

| Input and mapping | Verified coordinates |
| --- | --- |
| dBFS traces `[−80,−60,−40]` and `[−40,−20,0]`, each with its own minimum and maximum | Both give `[0,0.5,1]`. Their relative patterns are identical. |
| The same traces with shared range `[−80,0]` dBFS | `[0,0.25,0.5]` and `[0.5,0.75,1]`. The shared −40 dBFS value maps to 0.5 in both. |
| Signed differences `[−6,0,6]` on range `[−6,6]` dB | `[0,0.5,1]`. The center is exactly 0 dB. |
| Levels `[−85,−80,1,unavailable]` on range `[−80,0]` | `[0,0,1,unavailable]`. Saturation shares a coordinate with valid boundary levels and needs a retained status. |

On opaque white, `#777777` gives 4.478089:1 and
`#767676` gives 4.542225:1. The first is below the
normal text threshold. Likewise `#959595` gives
2.995346:1 and `#949494` gives 3.033470:1. The
first ratio is below 3:1 even when it displays as
3.00. These are solid-color arithmetic checks.
Evaluate the rendered controls, labels and marks
when assessing a user interface.

## Next action

Give Gauge the shared and adaptive range checks,
zero-centered differences, the cyclic seam, and
unavailable or saturated data. Verify the legend
mapping and contrast with the rendered marks and
labels in every supported theme.

## Revisit when

The analyzed quantity, reference, normalizer, palette,
theme, renderer, or required visual distinction changes.
