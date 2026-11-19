# Assigned material identity and density have separate owners

Expectation: a field named material, a material-folder caption, the UI density preference or the density-unit selector identifies the model's physical material and mass response.

Actual behavior in the pinned SOLIDWORKS 2026 SP05.2 implementation:

- The UI Definition density preference is a separate owner from the physical part density parameter
- Part `f1420` points to `moMaterial_c`, whose current serializer owns a density-parameter reference and no database/material name
- Database/material identity is an IdName CString in configuration visual properties, alongside appearance state
- Body assignment resolves the actual atom ID through active-configuration association records; custom density IDs below -9 use a separate manager map whose property `f28` is density
- The material folder's visible title is presentation and can be regenerated independently

The [prior default-density evidence](../Oracle/Parts/DefaultPartDensityHasTwoOwners.md) measured effective unassigned density 1 kg/m³ while the document preference is 1000 kg/m³. The [custom mass-unit lifecycle](../../../../../re/solidworks/measurements/2026/SdkCustomMassUnitsNative01.json) retained effective density 1 kg/m³ in all its variants. Neither proves assigned material support.

Use the actual configuration/material getter, body ownership and independent `mass / volume` together. Keep part assignment, body override, rendering appearance and unit display separate. Setter completion is not sufficient: the documented part material setter has no Boolean success result, and a valid material database is an independent API dependency.

The [exact native owner record](../../../../../re/solidworks/records/AssignedMaterialOwners2026.md) and [proposed controlled source protocol](../../../../../re/solidworks/v2026/AssignedMaterialSourceRecipe01.json) retain the open construction, XML and cold-reopen questions. No new assigned-material native result exists in this tranche.
