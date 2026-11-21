# Audio vectorscope fixtures

Check epoch IDs, capture bounds, sample indices, and exact viewport
positions before integer raster rounding. The axes use positive-right
and positive-up coordinates. Rows in the viewport increase downward.

## Coordinate and numerical checks

| Input | Expected result |
| --- | --- |
| $(1,1)$, $(1,-1)$, $(1,0)$, $(0,1)$, $(0,0)$ | $(0,\sqrt2)$, $(-\sqrt2,0)$, $(-1/\sqrt2,1/\sqrt2)$, $(1/\sqrt2,1/\sqrt2)$, and the origin. Swapping the input channels flips the sign of the first coordinate. |
| All ordered pairs from `[-1.25,-1,-0.75,-0.25,0,0.25,0.75,1,1.25]`. | Use the exact identity $x^2+y^2=L^2+R^2$ and the inverse pair. Apply $9\times10^{-16}$ absolute squared-norm and $5\times10^{-16}$ absolute inverse-component tolerances to this grid. |
| Two adjacent samples $(1,0)$ then $(0,1)$. Shift the right payload left one sample and preserve the labels. | The original points lie on different sign diagonals. The shifted sequence contains $(1,1)$ and $(0,0)$, producing a vertical point and an origin. Test the known impulse indices before interpreting the plot. |
| $R=L/2$ on a nonzero sequence. Repeat with common and opposite DC offsets. | Original slope $-3$. Common DC shifts only $y$, opposite DC shifts only $x$. Uncentered normalized inner product 1 and normalized plotted axis-energy difference 0.8. |
| $L$ is 1 and $R$ is the next binary64 value above it. | Horizontal coordinate is $2^{-52}/\sqrt2$. For the smallest positive binary64 $t$, $(t,t)$ yields $y=t$ after rounding. |
| $B$ is the maximum finite binary64 value. Set $L=R=(5/8)B$, then $L=R=B$. | The first yields a finite vertical coordinate. The second reports an out-of-range vertical axis at the exact sample index. |

## Point order and viewport

| Input | Expected result |
| --- | --- |
| 480 samples at 48 kHz. Equal amplitude 0.75, 1 kHz, right lag and lead of 12 samples. Use the cosine and its periodic shift. | Both traces have squared radius 0.5625. Determinant of the points at 0 and 12 is about $-0.5625$ for lag and $+0.5625$ for lead. Use $2\times10^{-15}$ absolute tolerance. For 2 kHz and a 12-sample lag, the trace is horizontal. |
| Draw that 1 kHz lagged trace at strides 1, 12 and 48 from index zero. | 48, 4 and 1 distinct positions to 12 decimal places. Check the full-rate input before diagnosing a trace that appears as a dot. |
| Fit the quadrature circle in square half-extents 180, 180 and rectangular half-extents 320, 180, with $A=1$. | The geometric radius is $180\cdot0.75/\sqrt2$ in both views. The horizontal and vertical distances use the same scale. |
| Center and half-extents 320, 180, with $A=1$. Use $(1,1)$, $(1,-1)$, $(1.25,-1.25)$, and $(1.25,1.25)$. | Pixel positions $(320,0)$, $(140,180)$, $(95,180)$, and $(320,-45)$. The last two are over nominal. Only the last is out of view. |
| Same geometry with $A=t$ and pair $(t,0)$, then $A=B$ and pair $(B,0)$. | Both yield $(230,90)$ inside the viewport. The ratio is applied without a floating intermediate gain. |

Use direct tape slices to check a capture producer after a callback split,
a ring wrap, a rejected block, and a fresh epoch. Include exact origins
above $2^{53}$ and reversed channel-list order. Project a completed
trigger capture using the same two selected channel IDs.

## Review tasks

1. Give an agent a dot on a known quadrature tone. Ask which measured
   sample pairs, axis signs, and point-selection rule distinguish the
   cause.
2. Give it an above-nominal point inside a wide rectangle and one outside
   it. Ask for separate evidence for level, viewport bounds, and clipping.
3. Give it aligned labels on a right plane shifted by one sample. Ask
   which signed impulse fixture can expose the bad payload.

Record observed agent decisions separately from the reference tests.
