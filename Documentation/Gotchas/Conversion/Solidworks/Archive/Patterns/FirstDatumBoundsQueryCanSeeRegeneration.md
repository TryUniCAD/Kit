# First datum bounds can already reflect regeneration

## Expectation

Reading the principal `IRefPlane.BoundingBox` before an explicit rebuild appeared sufficient to distinguish unset wire display state from a populated display rectangle.

## Actual behavior

The same-locator plain and sized generated origin plates returned identical diagonals on their first native query. The plain input had zero stored dimensions. Both native edits and fresh reopens gave the same new bounds. The measurement does not distinguish implicit Open refresh from lazy getter work. [Measured contrast and source boundary](../../../../../../re/solidworks/records/LocalLinearPatternPrincipalDisplayContrast2026.md#native-result)

## Workaround

Compare the stored owners and observed document separately. Use a generated dependent axis to exercise load-time ordering before relying on unset principal display state in an angled datum or pattern.
