# SOLIDWORKS 2026 classic roughness replay

The research audit reads the populated Definition appearance manager
using the 98 ordered typed fields of `PWMaterialProperties_c`. It
preserves both definition objects with the same material ID. The
native manager lists them separately and uses the later row for
its ID lookup.

Two independent native edits keep stock RGB 229 and preserve the
authored values 0.3125 and 0.6875 across save and fresh reopen.
Both complete Definition streams replay exactly. The changed value
appears in two Definition records and in the classic appearance of
the part, selected configuration and part-self display state.
The DSPBR roughness stays at its prior value. Both controls and
all 176 numeric checks pass in six processes.

This is a disclosed source audit. Colour publication and generated
appearance writing require separate evidence.
[Codec evidence](../../../../re/solidworks/records/ConcentricStockChildAppearanceCodec2026.md)
[Measurements](../../../../re/solidworks/measurements/2026/ConcentricStockChildRoughness01.json)
