# Independent circular drafts can form a concave meridian

An unequal two-sided extrusion cannot generally be represented by one cone between its far radii. Each side starts at the same profile radius, and a positive taper expands away from the sketch along that side's own direction. Two positive tapers therefore produce an hourglass radial section with its minimum at the shared profile plane.

The existing full-revolve polygon builder deliberately requires a strictly convex meridian. Removing that guard would admit unrelated unsupported profiles. Build the validated two-segment radial graph with one shared profile rim and two exposed far caps, and integrate each frustum independently. The profile radius must participate in bounds even when both far ends contract.

The [captured source and offline proof](../../../../../../re/Fusion/DecodedPromotion20261127/DualDraft/Findings.md) retain independent side-angle edits, swapped sides, held-out values and native cone/rim geometry. `BuildDualSide` reuses exact periodic topology primitives without changing the general revolve guard. This geometry rule does not establish strict reader admission or native writer acceptance.
