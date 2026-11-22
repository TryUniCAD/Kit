# One assigned material can carry several colors

Two SOLIDWORKS 2026 saves bind the same selected configuration material
and density while retaining different model colors and shader albedos.
In the first save, the model's packed RGB, the classic RealView primary
color and DSPBR albedo also differ from one another. The separate
`MATERIALTREE` swatch varies across the pair.

The physical material's identity, part visual, active configuration and
display-state holder have distinct ownership. The primary texture
record can also be present with an empty embedded CString. Keep those
owners and typed values separate when inspecting the archive. A
portable RGBA requires independent evidence for the display and color
domain it represents.

[Disclosed guarded comparison](../../../../../re/solidworks/records/AssignedMaterialAppearanceProjection2026.md)
