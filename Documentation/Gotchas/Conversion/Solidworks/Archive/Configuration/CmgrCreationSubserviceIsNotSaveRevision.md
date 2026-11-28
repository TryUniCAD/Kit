# CMgr creation subservice is not the save revision

## Expectation

A 2026 SP05.2 source gives every manager/configuration feature creation field subservice 2, or a source component can substitute its output target's revision.

## Actual behavior

Both disclosed SP05.2 through-all saves store creation subservice 0 in the separate inherited feature owners. The exact native `getCreateVersion` and ordinary explicit `setCreateVersion` bind `f301` to creation provenance. Last-update versions and header/save metadata have other owners.

## Workaround

Read and retain explicit source creation provenance. Supply it independently from the output save target. The bounded component admits creation subservice 0 or 2 with matching explicit build/kernel/service settings; it does not infer why a native author selected a given creation subservice.

[Source trace and scope](../../../../../../re/solidworks/records/ThroughAllCmgrFeatureEvents2026.md) · [Host receipt](../../../../../../re/solidworks/measurements/2026/ThroughAllCmgrFeatureEvents01.json)
