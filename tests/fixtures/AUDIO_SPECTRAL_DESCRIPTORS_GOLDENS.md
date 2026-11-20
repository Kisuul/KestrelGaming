# Spectral descriptor fixtures

The inputs are linear one-sided PSD ordinates on a uniform DFT grid. Set
$\Delta f=1$ Hz when a row gives bin powers directly. The tabulated bin numbers
are zero-based DFT indices. The descriptor selects positive frequencies by
default, including an even transform's Nyquist bin at the upper edge.

| Fixture | Independent expected result | Test |
| --- | --- | --- |
| Centers 100 and 200 Hz, PSD ordinates 1 and 3, $\Delta f=100$ Hz | Total power 400. Centroid 175 Hz. Variance 1875 Hz² and spread $25\sqrt{3}$ Hz. At 25%, rolloff is 100 Hz. At 85% and 95%, it is 200 Hz. Magnitude weighting would give 163.397459622 Hz. | `test_two_bin_power_moments`, `test_two_bin_rolloff` |
| Positive-bin powers [9, 25, 6] and [47, 48, 5] | At 85% and 95% respectively, the sum through DFT bin 2 is exactly the threshold. The max-scaled binary64 sum can select bin 3. Increasing the last power by one binary64 step moves the exact crossing to bin 3. | `test_rolloff_exact_overtakes_rounded_total` |
| Three selected powers [1, 1, 1] and [1, 0, 0] | Flatness, crest, and normalized entropy are (1, 1, 1) and (0, 3, 0). Raw entropy of the uniform case is $\ln 3$. Spread of the occupied bin is 0 Hz. | `test_flat_and_single_occupied_bin` |
| Same two-bin powers [1, 3] and [2, 6] on consecutive frames | L2 power flux $\sqrt{10}$ in squared amplitude units. L2 normalized shape flux 0. For [1, 3] followed by [3, 1], the two fluxes are $\sqrt{8}$ and $\sqrt{1/2}$. | `test_gain_only_flux`, `test_shape_redistribution` |
| Adjacent frames with powers [0, 0] and [1, 3] | Power flux $\sqrt{10}$. The silent frame has power 0 and unavailable shape. Shape flux is unavailable in either order. | `test_valid_silence_in_either_flux_operand` |
| Two occupied bins at 100 and 200 Hz with PSD $2^{800}$ and $2^{-800}$ | The geometric mean is 1. Flatness rounds to $2^{-799}$. Spread rounds to $100\cdot 2^{-800}$ Hz. Entropy underflows in binary64. Taking the log after dividing the smaller ordinate by the larger loses valid flatness. | `test_flatness_and_spread_survive_ratio_underflow` |
| 1024 selected bins with ordinates $2^{600}$ once and $2^{-486}$ for every other bin | Each small entropy contribution is below the minimum binary64 positive value. The sum is representable. Compute the binary64 expectation from Decimal at 410 digits. | `test_entropy_aggregates_subnormal_terms` |
| Rectangular even DFT of $x[n]=3/8+(-1)^n/4+(1/2)\cos(\pi n/2)$, length 8 | DC, bin 2, and Nyquist powers are $9/64$, $1/8$, and $1/16$. Full power is $21/64$. Power with DC excluded is $3/16$. | `test_even_psd_keeps_endpoint_mass` |
| Rectangular odd DFT of a $5/8$ peak cosine at bin 3, length 7 | The highest returned bin is paired. Its power and the integrated frame power are $25/128$. | `test_odd_psd_keeps_last_paired_bin` |
| Selected result followed by a gap, duplicate start, wrong clock, or invalid last ordinate | Reject the frame. A later frame at the original expected start still compares with the last valid frame. Reset clears the comparison. Use integer sample indices above $2^{53}$. | `test_gap_duplicate_and_late_invalid_are_atomic`, `test_comparison_rejects_changed_measurement_identity`, `test_reset_primes_new_epoch` |

For ordinary nonzero results, use relative tolerance $2\cdot10^{-12}$ unless a
test specifies a tighter absolute check. Compare bin indices, sample indices,
statuses, and exact zeros directly. Tests for an upstream DFT can have small
residuals at analytic spectral nulls. Use explicit zero PSD ordinates to isolate
the descriptor's zero rules.

## Agent review tasks

1. A centroid changes when an operator applies a uniform gain. Trace the
   original frame. Compare the expected 175 Hz result with the two-bin fixture.
   Verify the bin grid and any floor, clipping, or gain change in the signal tap.
2. A displayed flux spikes immediately after a seek. Inspect the epoch, exact
   start index, expected hop, profile, and bin support. Verify that the new
   epoch starts without a comparison.
3. A spectrum analyzer must report a peak sine amplitude in volts. Use the
   FFT amplitude skill for that task. Use this skill for a power-weighted
   spectral shape measurement.

These are tasks for an agent-use trial. The automated suite runs the arithmetic
and frame checks.
