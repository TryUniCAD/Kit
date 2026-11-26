# Standard view rounding changes measured hashes

The standard view rotations in a generated part are independent of its
feature geometry. The *Left*, *Right*, *Top* and *Bottom* transforms use
the native rotation plan with a binary64 half angle of magnitude
`0x1.921fb54442d28p-1`. The host math library can round the cosine of that
angle differently. The difference can change two diagonal entries per
view and therefore change the whole file hash.
[Measured Windows and Mac matrix contrast](https://github.com/TryUniCAD/Kit/blob/0b23a8901a675740086d3326ff6fa2be67244ac8/re/solidworks/measurements/2026/NestedRuntimeStdViewContrast01.json)

Compute sine and cosine from the actual binary64 half angle using the
alternating Taylor series in exact rational arithmetic. The omitted tail
lies between the sums ending at indices 23 and 24, with the first index
at zero. Publish the rounded value only when both sums round to the same
binary64 word. Carry positive and negative zero through the sine and
quaternion arithmetic. The serializer then applies the recovered matrix
formulas and operation grouping.

Skew and Step both reproduce their complete native-measured file hashes,
including ten typed view rows. Forcing the adjacent cosine changes exactly
eight matrix words in `Contents/Config-0` and invalidates both hashes.
The replay takes its inputs from two neutral requests and their measurement
metadata. The input-file audit recorded zero reads during construction.
[Exact arithmetic contrast and measurement hashes](../../../../../../re/solidworks/measurements/2026/PlainStdViewRounding01.json)
