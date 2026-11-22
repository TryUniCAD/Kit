# SOLIDWORKS part material visual records

Supply an in-memory `SldprtArchive` to the internal `ReadPartVisual`
reader to inspect the ordinary format-4, version-19000 part visual
record. It reads the physical ModelHeader and part root, then follows
the actual part-owned name and `f78` visual records inside the declared
lightweight section. The result retains typed fields, map identities and
the next cursor.

The bounded reader supports the observed material texture, renderer
appearance and physically based rendering layouts. Its scope ends at
the part visual record. Physical material assignment and whole
configuration admission have separate ownership requirements.

Eight disclosed native files preserved every byte of their typed prefix
during guarded replay. The existing tracked L1 and ConcaveOwned files
provide a positive process case and a distinct selector refusal.
[Format and process evidence](../../../../../re/solidworks/records/PartMaterialVisualRead2026.md)

[Adapter guide](../../../../Reference/Adapters/Solidworks.md)
