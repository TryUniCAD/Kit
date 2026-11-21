# Source-aware through-all owner components

The internal SDK can now project the complete measured ordinary through-all source into typed geometry owners while retaining the original document and unsupported fields in a separate explicit envelope.

`ProjectThruSrc` checks the original 28-entry presentation, all three datums, both sketch normals, actual profile and stock dependencies, real circle/centre relationship, one stock driver and explicit selected-body scope. `MakeThruOwners` reuses the shared generative constructors and returns an owner graph with fresh allocation and 27 explicit source correspondences. The final cut body is kept distinct from the stock atom.

This is a component API. It emits no complete native document. `RequireThruFull` visibly refuses the remaining source style, presentation, provenance, native sketch state, body-caption and continuous automatic-selection fields, including when a caller clears the envelope's stored status. No normal writer registration or held-out/native acceptance is added.

Verification: 68 fresh isolated SDK processes, 18 exact partial-archive round trips, 52 targeted refusals, zero runtime build input reads, four unchanged legacy construction/public-read comparisons, strict static checks and the donor scan. The [guide](../../../../../Reference/Research/Solidworks/Construction/ThroughAll/SourceOwners.md), [field record](../../../../../../re/solidworks/records/ThroughAllSourceOwners2026.md), [receipt](../../../../../../re/solidworks/measurements/2026/ThroughAllSourceOwners01.json) and [body-ownership gotcha](../../../../../Gotchas/Conversion/Solidworks/Model/ThroughAll/SourceFinalBodyIsNotStockAtom.md) describe the exact limits.
