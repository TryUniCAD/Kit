# Fusion body appearance and physical finish have separate owners

The body's `visualMaterial` selects a package asset through the material manager. The physical asset's `physmat_aspects` can point to a different finish. A strict public read projects the body-visible RGBA. Reading the physical material's typed properties projects the physical aspect color and finish.

Use the [distinct appearance research request](../../../../Changes/Research/Encoder/FusionDistinctMaterialAppearances.md) to specify both roles and generate fresh links. Editing the body finish leaves the physical aspect intact. Historical compatibility aliases add an independent legacy asset and require their own rules.
