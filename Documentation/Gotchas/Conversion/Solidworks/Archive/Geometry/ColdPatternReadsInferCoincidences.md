# Cold pattern reads infer endpoint coincidences

## Expectation

The recovered rectangle's relation list contains only the authored axis constraints in the cold archive.

## Actual behavior

The aggregate's strict geometry decoder reconstructs both stock rectangles and derives four additional endpoint coincidences per sketch. Each disclosed archive originated from four authored axis constraints per rectangle. The default readback recovers one solid and the live pattern count and pitch. The history-only projection follows a different path and still retains opaque native definitions. [Exact disclosed comparison](../../../../../../re/solidworks/measurements/2026/AggregateMeasuredLinearPattern01.json)

## Workaround

Publish from the original neutral model and its typed presentation using the matching native receipt. Keep the inferred constraints and retained history visible when inspecting the decoded source. Whole-source republication requires a verified typed stock and presentation projection. [Publication boundary](../../../../../../re/solidworks/records/AggregateMeasuredLinearPattern2026.md)
