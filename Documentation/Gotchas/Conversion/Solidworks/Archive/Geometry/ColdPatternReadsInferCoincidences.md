# Cold pattern reads infer endpoint coincidences

## Expectation

The recovered rectangle's relation list contains only the authored axis constraints in the cold archive.

## Actual behavior

The strict decoder reconstructs both stock rectangles and derives four additional endpoint coincidences per sketch. Each disclosed archive originated from four authored axis constraints per rectangle. Full and design-only reads recover the same typed owner graph and live parameters. The full read also emits a derived solid. [Strict design-only comparison](../../../../../../re/solidworks/measurements/2026/SdkColdPatternDesignRead01.json)

## Workaround

Use the matching native receipt and measured publication settings. For strict readback, bind the presentation to the actual readback parameter identifiers and keep the inferred constraints and retained history. The writer checks that the four inferred incidences on each sketch also hold in its independently regenerated read. [Measured readback](../../../../../../re/solidworks/records/AggregateMeasuredLinearPattern2026.md#measured-strict-source-republication)
