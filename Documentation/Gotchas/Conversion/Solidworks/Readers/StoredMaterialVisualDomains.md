# Part visual labels do not assign body materials

A native part visual can store "Steel" with an unassigned physical density.
Its model color, classic renderer color and DSPBR albedo can disagree.
Classic renderer roughness and PBR roughness also have independent owners.

Keep these values in separate part-level appearance evidence. A texture
CString is a saved wire field. Decoding it does not identify a resource,
coordinate system or mapping unit. Use independently measured assignment,
scope and effective rendering evidence before linking to a portable material
or publishing native output.

See [stored part appearance](../../../../Changes/Solidworks/Inspection/Parts/SolidworksStoredPartAppearance.md)
and [archive evidence](../../../../Changes/Solidworks/Archive/Configuration/SolidworksPartMaterialVisual.md).
