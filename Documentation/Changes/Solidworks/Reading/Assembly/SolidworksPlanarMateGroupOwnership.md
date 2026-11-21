# Read native planar mate group membership

The strict SOLIDWORKS 2026 SDK reader now projects the ordinary flat mate group into `CadDocument.assembly.mate_groups`. The group retains its saved name, root owner and resolved-feature provenance. Its ordered member IDs refer to the existing portable mates from the linked separate mate list.

Use `convert.open_document` with component resolution enabled and check `metadata["solidworks.typed_mates_semantics"]`. The route requires one concrete group at its inherited resolved map slot and a complete ordered mate list. Alternative group owners, hierarchy, inline children or unresolved member identity stay outside typed admission.

Guarded normal SDK reads reproduce both previously disclosed native groups and compare exact linked streams. Generated and saved controls, including the existing concentric path, cover compatibility. The existing source-side writer refusals still apply. [Adapter guide](../../../../Reference/Adapters/Solidworks.md) · [Ownership and verification](../../../../../re/solidworks/records/SdkPlanarMateGroupRead2026.md)
