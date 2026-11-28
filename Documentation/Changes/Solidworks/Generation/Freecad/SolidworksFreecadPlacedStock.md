# Translated FreeCAD box stock preparation

The internal `PrepFcStock` preparer accepts the explicit `Placed=True` option for a verified, unlinked `Part::Box` with a translation and identity rotation. It takes all three placement coordinates from the actual FreeCAD property. The generated sketch fixes its first corner at the translated planar coordinates. A nonzero normal displacement uses the native signed offset-plane graph and its own driving distance. Length, Width and Height retain their original aliases and independent owners.

Two disclosed source primitives pass guarded construction and linked archive readback. One is an intact single-feature, single-solid document. Current public publication and full strict output reading require further qualification. The disclosed oblique box still refuses. [Placed stock evidence](../../../../../re/solidworks/records/SdkFreecadPlacedStock2026.md)
