# Nested assembly index captions can mirror the root

Both disclosed generated version-19000 Frame assemblies expose the root
caption in every `swModel.swName` even though their external file keys and
physical target names are distinct. The XML reader also assigns a global
placement index across model records, so a containing assembly's first
placement can have a nonzero order. Relative child order is still intact.

Bind a definition title to the actual child's typed root `f18` after
checking its full file key and configuration. Use the owning assembly's
`f68` occurrence list to check local order. A displayed caption, stem, or
global occurrence index alone cannot identify a typed owner.

[Disclosed readback](../../../../../re/solidworks/records/SdkNestedColdReadback2026.md)

The normal resolved reader now applies this rule to ordinary nested
version-19000 graphs after every physical dependency and direct placement
passes these checks. Distinct stored captions and the original index
attributes remain available. [Reader change](../../../../Changes/Solidworks/Reading/Assembly/SolidworksNestedIndexOwnerReadback.md)
