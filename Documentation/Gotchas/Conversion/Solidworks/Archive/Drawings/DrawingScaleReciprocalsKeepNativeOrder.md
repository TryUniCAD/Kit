# Drawing scale reciprocals keep native order

## Expectation

The inverse sheet scale can use either `denominator / numerator` or `1 / (numerator / denominator)` because the algebra is equivalent.

## Actual behavior

The native sheet update divides the numerator by the denominator, then takes the reciprocal. Binary floating-point rounding makes that sequence observable in the stored double. For 11:3, the native sequence produces `0x1.1745d1745d175p-2`; direct `3 / 11` produces `0x1.1745d1745d174p-2`. The values differ by one unit in the last place.

The profile and plane use the inverse frame. The separate UI sketch uses the forward ratio. Changing the arithmetic order can break exact Definition parity while leaving ordinary numeric comparisons apparently unchanged.

## Correct use

Preserve `1.0 / (numerator / denominator)` for both inverse frames and `numerator / denominator` for the UI frame. The SDK sheet-construction process includes an 11:3 complete-document case and requires exact bytes against independent construction. This is an offline wire-precision check, not a new native acceptance measurement.

See the [native scale source rule](../../../../../../re/solidworks/records/DrawingEmptySheetConstruction2026.md), [SDK construction ledger](../../../../../../re/solidworks/records/DrawingSheetConstruction2026.md) and [process evidence](../../../../../../re/solidworks/measurements/2026/SdkDrawingSheetConstruction01.json).
