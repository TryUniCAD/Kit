# A linear pattern overhang changes the joined face count

The six plate faces plus five faces per raised instance describe rectangular bosses fully contained in the stock footprint. In the disclosed pitch edit from 20 to 36 mm, one instance extends beyond the plate by about 3.456 mm. SOLIDWORKS opens and rebuilds the joined model with one solid and 17 faces, one more than the contained 16-face result with the same instance count.

The ordinary saved pattern path checks its existing face inventory before projecting typed body ownership. The finite hinge, angular plane and owned driving angle can be verified independently of that body profile. Use the linked partition and a topology-specific proof when adding the overhanging case. [Native source measurements](../../../../../../re/solidworks/measurements/2026/LocalLinearPatternDatumPlacement01.json)
