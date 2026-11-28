# Feature output IDs do not publish created atoms

The expected shortcut is that a saved extrusion's `f498` atom IDs, or one atom in its manager, are sufficient for ordinary cold-open body publication.

In the pinned 2026 source, `getNumberOfOutputAtoms` reads `f538` or the actual `f528` created-object array. It never reads `f498`. Current loading can extend the ID array from existing created objects, but does not synthesize created objects from IDs. The modern zero-output path can therefore skip `setBody` even when a valid partition body has a positive atom ID.

Preserve separate typed ownership: created-array presence, actual atom object aliases shared with the manager, retained signed IDs, creator/last-modifier identities and runtime body publication. Generate the graph from actual model/allocation rules. Do not copy a saved atom number, replace the created array with equal-looking duplicate objects, or rely on a legacy implicit-creation branch.

The [source rule and exact guards](../../../../../../re/solidworks/records/FeatureOutputAtomOwnership2026.md) and [numeric metadata](../../../../../../re/solidworks/records/FeatureOutputAtomOwnership2026.json) establish this boundary. No same-invocation native cause or new product qualification is claimed.
