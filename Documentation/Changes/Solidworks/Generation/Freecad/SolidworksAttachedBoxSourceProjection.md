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
the shape cache. The property comparison requires both values and their
serialized field order. All six comparisons pass with zero runtime input file reads.
[Custom property ordering](../../../../Gotchas/Conversion/Solidworks/Archive/Properties/CustomPropertyOrderChangesBytes.md)
Both projectors reject ten unsupported variants. The port also rejects an
unowned neutral plane and a primitive record which differs from its object
table owner. [Comparison procedure](../../../../../re/tooling/sw2026/VerifyAttachedBoxSource.py)
· [Comparison receipt](../../../../../re/solidworks/measurements/2026/FreecadAttachedBoxSourceProjection01.json)

The internal constructor reproduces all six candidate containers and 72
stream hashes from the native-measured files. The standard SDK refuses the
original sources with zero published bytes. The public transfer contract
still needs B-rep, native payload, provenance and round-trip metadata
coverage. [Shared construction and SDK refusal](../../../../../re/solidworks/measurements/2026/FreecadAttachedBoxSharedBuild01.json)
· [Measured signed construction](../../../../../re/solidworks/records/SdkFreecadOriginBox2026.md#generated-attached-top-plane-boxes)
