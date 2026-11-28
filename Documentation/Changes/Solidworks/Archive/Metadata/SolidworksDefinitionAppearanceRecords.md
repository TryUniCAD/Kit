# Preserve populated SOLIDWORKS part Definition appearances

The internal Definition codec reads and re-emits `PWMaterialProperties_c` records from an ordinary version-19000 SOLIDWORKS part. It accepts class schema 1 and internal `f20=1` through the part's appearance manager. The manager preserves the ordered list and distinct object identities when multiple records share a material ID.

Use `ReadModelDef` with the actual Definition stream and archive version. Pass the returned graph to `WriteModelDef` for a typed archive round trip. Appearance construction and public material projection remain outside this codec. The existing empty-manager projection still refuses populated reference lists.

The codec requires a concrete appearance object in each populated manager row. The body guard rejects material objects first defined outside the measured manager. Existing shared object tags can still reference an already-admitted appearance from a later untyped field. A separate ownership rule would be needed to reject that edge.

The disclosed process replay reproduced both 2,365-byte populated Definitions and three absent or empty controls byte for byte. Both populated records retained their distinct archive slots and duplicate material IDs. The process checked 20 read and write refusals for unsupported versions, schema, placement, presence and row tags, plus the existing empty-manager refusal. [Disclosed source and native analysis](../../../../../re/solidworks/records/ConcentricStockChildAppearanceCodec2026.md) · [Process replay](../../../../../re/tooling/sw2026/para/concentric/ProveDefinitionAppearanceCodec.py) · [Receipt](../../../../../re/solidworks/measurements/2026/SdkDefinitionAppearanceProof01.json)
