# Attached FreeCAD box source projection

The internal SOLIDWORKS source projector reads a single FreeCAD
`PartDesign::AdditiveBox` attached to the whole XZ datum. It accepts the
measured FreeCAD 0.21.2, 1.0.2 and 1.1.4 source profiles. The projector checks
the actual object table, origin group, attachment, placement and three
millimetre drivers before it lowers the part to the shared signed Top-plane
profile. It retains the source names, literal properties, creation time,
parameter identities and declared unit settings. The source shape cache can
corroborate the geometry and is optional. [Source projector](../../../../../src/convert/adapters/solidworks/Core/Preparation/FreecadBox/Source/ReadBoxSource.py)

The comparison process checks nine projected fields against the research
projector for each of the three disclosed F14c records, both with and without
the shape cache. All six comparisons pass with zero runtime input file reads.
Both projectors reject ten unsupported variants. The port also rejects an
unowned neutral plane and a primitive record which differs from its object
table owner. [Comparison procedure](../../../../../re/tooling/sw2026/VerifyAttachedBoxSource.py)
· [Comparison receipt](../../../../../re/solidworks/measurements/2026/FreecadAttachedBoxSourceProjection01.json)

Public route qualification remains part of the SOLIDWORKS native writer
programme. [Measured signed construction](../../../../../re/solidworks/records/SdkFreecadOriginBox2026.md#generated-attached-top-plane-boxes)
