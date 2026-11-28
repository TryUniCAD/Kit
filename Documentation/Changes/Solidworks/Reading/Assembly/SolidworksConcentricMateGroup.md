# Read the saved concentric mate group

The normal SOLIDWORKS 2026 reader now includes the native group's stored name and ordered member in `CadDocument.assembly.mate_groups` for the admitted single solved concentric mate. The group is a direct child of the assembly and carries provenance to its resolved feature record. The ordered member references the same portable mate already in the assembly graph.

Read through `convert.open_document` and check the `solidworks.typed_mates_semantics` status. This route requires a unique top-level native group and an exact linked mate list. A pending group, extra group contents or another hierarchy stays outside typed admission.

Ten normal SDK reads reproduce the group seen in the frozen native trees. Four existing fallback cases stay identical, and two additional unsupported group states refuse. [Usage](../../../../Reference/Adapters/SolidworksConcentricReading.md) · [Evidence](../../../../../re/solidworks/records/ConcentricMateGroupRead2026.md)
