# Through-all ends have no driving depth

## Expectation

A through-all cut can reuse a blind cut's active depth graph, with its enum changed. A zero returned by `GetDepth` might be treated as an editable zero-length parameter.

## Actual behavior

The disclosed 2026 forward through-all source has native type 1, null `f18/f20` distance owners, no feature-owned displays and native forward/reverse depth queries of zero. Its mid-plane stock has a separate real driving length. Editing that stock depth changes the cut's extent automatically while the cut remains distance-less.

The existing `ReadExtrude` always requires `f18`, the internal `ExtrudeOwner` requires a `DepthOwner`, and the neutral extrusion definition requires `length`. Those contracts cannot be bypassed by attributing the stock parameter or an API placeholder depth to the cut.

## Workaround

Use an explicit depth-less end branch and retain no cut driving parameter. Preserve the actual end type, direction, profile/support and consumed body aliases. Keep the public projection unsupported until its neutral definition can express the absent length and its complete profile qualifies.

The [typed source record](../../../../../../re/solidworks/records/ThroughAllD01TypedRead2026.md) and [receipt](../../../../../../re/solidworks/measurements/2026/ThroughAllD01TypedSource01.json) bind the exact original and edited saves. This is one disclosed forward profile, not a qualification of other end modes or generated output.
