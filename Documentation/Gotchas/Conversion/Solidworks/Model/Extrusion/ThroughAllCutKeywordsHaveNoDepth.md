# A through-all cut has no depth keyword

## Expectation

The existing cut keyword constructor required one `D1` dimension in every `Extrusion` row.
That rule described the ordinary blind-cut subset.

## Actual behavior

All three disclosed through-all cuts have no active distance display or cut dimension.
Their end words preserve the actual first and second termination.
The corresponding keyword row has no `Dimension` child.
Its `DissectableChildren` value identifies the actual profile.

A zero-valued `D1` would invent a dimension and change the feature intent.
Saved through-all records retain a nonzero inactive `f158` word.
That word must not be normalized to a fresh constructor zero.

## Workaround

Construct the end from its actual termination and direction.
Keep the cut distance graph absent.
Allow no keyword dimensions for that exact graph.
Keep the existing single-`D1` blind-cut behavior.
Reject unsupported dimension names and additional owners.

The [construction record](../../../../../../re/solidworks/records/ThroughAllColdConstruction2026.md) binds native code and process evidence.
The [directional receipt](../../../../../../re/solidworks/measurements/2026/ThroughAllDirectionsTyped01.json) preserves all six disclosed saves.
This remains research scope until independent native and held-out acceptance passes.
