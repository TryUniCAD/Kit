# Foot topology factor rounding

## Expectation

Equivalent area and volume measurements should compare equally after explicit feet-to-millimetre scaling at zero tolerance.

## Actual behavior

Exponentiating the binary floating length factor first produces `304.8**2 = 92903.04000000001` and `304.8**3 = 28316846.592000004`.
Converting those rounded products to exact rational values preserves the error and can report differences between equivalent declared decimal measurements.

## Workaround

Construct the exact rational length factor before exponentiation.
The [research comparator correction](../../../Changes/Research/Readers/Comparison/ExactTopologyUnitFactors.md) applies this order and adds real-command process coverage.
Keep tolerances unchanged; increasing them would hide the factor defect.
This correction cannot restore precision already lost in the input document.
