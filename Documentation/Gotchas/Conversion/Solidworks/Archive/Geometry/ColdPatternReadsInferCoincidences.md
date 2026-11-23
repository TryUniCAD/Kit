# Cold pattern reads infer endpoint coincidences

## Expectation

The recovered rectangle's relation list contains only the authored axis constraints in the cold archive.

## Actual behavior

The strict decoder reconstructs both stock rectangles and derives four additional endpoint coincidences per sketch. Each disclosed archive originated from four authored axis constraints per rectangle. Full and design-only reads recover the same typed owner graph and live parameters. The full read also emits a derived solid. [Strict design-only comparison](../../../../../../re/solidworks/measurements/2026/SdkColdPatternDesignRead01.json)

## Workaround

Publish from the original neutral model and its typed presentation using the matching native receipt. Keep the inferred constraints and retained history visible when inspecting the decoded source. Whole-source republication requires a verified typed stock and presentation projection. [Publication boundary](../../../../../../re/solidworks/records/AggregateMeasuredLinearPattern2026.md)
