# Through-all ends have no driving depth

## Expectation

A through-all cut can reuse a blind cut's active depth graph, with its enum changed. A zero returned by `GetDepth` might be treated as an editable zero-length parameter.

## Actual behavior

The disclosed 2026 forward through-all source has native type 1, null `f18/f20` distance owners, no feature-owned displays and native forward/reverse depth queries of zero. Its mid-plane stock has a separate real driving length. Editing that stock depth changes the cut's extent automatically while the cut remains distance-less.

The original typed reader required `f18` and a `DepthOwner` for every extrusion. The neutral definition also required a primary length. The stock driver has its own feature owner.

## Workaround

Use the explicit depthless end and preserve the actual end type, direction, sketch support and consumed body aliases. The current public reader uses this projection for three disclosed through-all directions on the measured single mid-plane stock.

The [typed source record](../../../../../../re/solidworks/records/ThroughAllD01TypedRead2026.md) binds the exact forward original and edited saves. The [public read receipt](../../../../../../re/solidworks/measurements/2026/PublicThroughAllEndRead01.json) also covers the reverse and two-direction disclosed designs.
