# Face reference IDs keep Parasolid loop separators

One surface plus four geometric boundary edges appears to need five inline IDs. The exact ordinary Parasolid initializer keeps an additional null loop separator, including the terminal separator.

For each selected actual loop, it appends its ordered coedges then a null. The own surface is index0. A one-loop four-coedge face therefore has six inline `moEntityId_c` rows. Boundary rows use actual edge permanent IDs when present, otherwise actual right-face surface IDs. The null row is an inline wrapper with a null representation pointer, not an omitted object.

Compute `1 + sum(coedge_count + 1 per selected loop)` for this branch and preserve every separator. Do not transplant the other kernel branch's compaction or derive row count from the number of nonnull representations.

The [source checkpoint](../../../../../../re/solidworks/records/DownstreamFreshFaceRows2026.md) and [receipt](../../../../../../re/solidworks/measurements/2026/DownstreamFreshFaceSource01.json) retain the exact branch. They are not native acceptance of a generated cache.
