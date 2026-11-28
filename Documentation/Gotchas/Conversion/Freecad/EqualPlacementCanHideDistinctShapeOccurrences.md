# Equal placements can hide different FreeCAD shape occurrences

Both disclosed F14a body shapes contain multiple separately stored locations whose matrices are identity. The Body uses a nonzero child occurrence location, while the actual AdditiveBox `Shape` uses only its root identity location. Applying the matrices alone removes that distinction. [Typed input proof](../../../../re/solidworks/measurements/2026/SdkFreecadF14aTypedOwner01.json) · [Original shape lineage](../../../../re/solidworks/records/FreecadF14aTopologyLineage2026.md)

Walk first occurrences in native child order and check repeated records against the same symbolic path before joining the placed neutral IDs. The verification changes one repeated occurrence to another identity location in memory. The matrix stays identical and the reader refuses the ambiguous alias. [Occurrence walk](../../../../src/convert/adapters/freecad/BodyLineage/BoxOccurrences.py)
