# Custom property order changes file bytes

The custom property stream assigns property IDs in input order. Two Python
mappings with equal keys and values can therefore produce different
`docProps/custom.xml` bytes. The attached FreeCAD box projector preserves
the established body, origin, attachment and feature order. Compare ordered
items and the complete stream when checking a port of this projector.
[Shared box construction evidence](../../../../../../re/solidworks/measurements/2026/FreecadAttachedBoxSharedBuild01.json)
