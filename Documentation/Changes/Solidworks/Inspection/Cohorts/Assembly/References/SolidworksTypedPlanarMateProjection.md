# Typed planar mate projection

The SOLIDWORKS SDK projects resolved planar mates from a decoded version-19000 archive graph. It follows the exact occurrence object to the persistent datum in the synchronized child. The projection returns the ordered occurrence and plane identities, stored frame, alignment, and ordinary driving length.

Run `ProjectPlanarMates.py ASSEMBLY CHILD` with the explicit native parent and child files. The CLI uses the SDK projection and shared child header reader. Its scope covers direct part occurrences in one assembly configuration. Public SLDASM admission requires a production loader for the complete linked configuration, resolved feature and mate-list maps.

Fresh processes reproduced the previous output for six disclosed and generated pairs, covering twelve endpoints. The A18 parent rejected the mismatched A17 child. [Process receipt](../../../../../../../re/solidworks/measurements/2026/PlanarMateSdkBoundary01.json) · [Field and loader dependencies](../../../../../../../re/solidworks/records/PlanarMateSdkProjection2026.md) · [Mate selection strings](../../../../../../Gotchas/Conversion/Solidworks/Oracle/MateSelectionStringsCanBeBlank.md)
