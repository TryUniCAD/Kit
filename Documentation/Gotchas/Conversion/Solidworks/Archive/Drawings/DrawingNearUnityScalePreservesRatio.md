# Near-unity drawing scale preserves the authored ratio

## Expectation

Every nonunit drawing scale multiplies the geometric point coordinates, or a scale close to one can be rounded to one in the stored view fields.

## Actual behavior

The native scale setters retain the supplied ratio terms. The point-transform routine separately skips geometric multiplication when `abs(scale - 1) <= 1e-8`. A view with authored scale `1.000000005` therefore retains that value in its ratio and transform owner while point application uses the unity branch.

The source rule is bound to `sldmgu!0x31f09925..0x31f09963` in the pinned 2026 geometry module. The new named-codec cohort exercises the distinction with a fresh Front drawing. Its entire Definition matches independent generation, its SDK read/write preserves the original ratio, and an eight-corner predictor applies the geometric tolerance separately. This is offline codec evidence, without a new native acceptance run.

## Correct use

Preserve the explicit scale fields. Apply the documented tolerance at the geometric point-transform boundary. Keep the sheet/model sketch support formulas separate and do not round their authored owners to force an exact unit ratio.

See the [source rule](../../../../../../re/solidworks/records/DrawingScaledViewProjection2026.md#point-transform), [named codec ledger](../../../../../../re/solidworks/records/DrawingNamedDefinition2026.md) and [58-process receipt](../../../../../../re/solidworks/measurements/2026/SdkDrawingNamedDefinition01.json).
