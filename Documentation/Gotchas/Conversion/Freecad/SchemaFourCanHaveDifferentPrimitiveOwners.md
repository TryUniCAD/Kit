# Schema four can have different primitive owners

FreeCAD 0.21.2, 1.0.2 and 1.1.4 all write schema 4 for the origin-fixed AdditiveBox. The older release uses `Support`. Newer releases write `AttachmentSupport`, explicit unit and material settings and suppression owners. The 1.1 release also retains an owned origin point and a fuzzy tolerance field.

Validate the actual owner inventory, attachment, material, active unit selector and origin before lowering the shape. Preserve the scoped source fields separately from cached shape and element-map data. [Source version and construction receipt](../../../../re/solidworks/records/FreecadOriginBoxReleases2026.md)
