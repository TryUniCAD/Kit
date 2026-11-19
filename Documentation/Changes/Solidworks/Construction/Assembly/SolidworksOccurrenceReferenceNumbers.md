# Accept matching occurrence reference numbers

The shared SOLIDWORKS assembly writer accepts an explicit portable `reference_number` when it matches the occurrence name's canonical positive decimal suffix. For example, an occurrence named `Part-2` may carry `"2"`. An empty field continues to derive the value from the name. A conflicting number, a leading zero or extra unsupported occurrence state fails before construction.

The disclosed D01 read matches the actual component index for both numbers. A guarded neutral discriminator with explicit numbers produces the same parent and child bytes as the equivalent request with the numbers omitted, including the prior SDK snapshot. The public read recovers both numbers. The whole native D01 assembly source still requires independent ownership and presentation projection. [Usage](../../../../Reference/Adapters/SolidworksAssemblyWriting.md) · [Evidence](../../../../../re/solidworks/records/ConcentricOccurrenceNumbers2026.md)
