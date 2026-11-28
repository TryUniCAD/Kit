# SOLIDWORKS bare cylinder composition

The internal `MakeBareImport` composer accepts a typed millimetre B-rep
with one closed cylindrical solid and one active configuration. It uses the
supplied axis, cap stations, circle frames, radius and actual loop ownership
to build the two full circular rims. Their source seam points must agree
with the circle reference directions. The local kernel carries 23 resident
nodes. Readback derives one neutral seam vertex for each circular edge.
[Composer](../../../../src/convert/adapters/solidworks/Archive/Construction/Part/Imports/MakeBareImport.py)
· [Periodic topology](../../../../re/solidworks/records/GeneratedLocalCylinderKernel2026.md)

Call the composer with the neutral document and explicit target settings
and labels. The selected cap and mantle frames must already agree with the
documented periodic profile. The composer refuses alternative seam frames,
partial rims, unsupported source domains and additional configurations.
The target uses a single native BaseBody feature with the ordinary import
atom and two linked rollback marks. This geometry-only profile has no driving
dimensions in the source.
[Neutral profile](../../../../src/convert/adapters/solidworks/Archive/Partition/LocalCylinder/ReadCylShape.py)
· [Canonical seam readback](../../../Gotchas/Conversion/Solidworks/Archive/Partition/LocalBodies/DerivedCircleTrimCanRoundOffZero.md)

A guarded host process regenerates the two disclosed archive hashes and
all 24 logical streams from independently authored neutral boundaries. The
two corresponding planar controls reproduce their previous archive hashes.
A signed oblique source and a same-locator radius change pass strict SDK
readback with correct carrier orientation, seam points, volume, area,
centroid and bounds. The radius change reduces the compressed LocalBodies
stream from 848 to 846 bytes. Eight malformed geometry or document requests are
refused. The process uses zero runtime file reads during construction and
verification.
[Reproducible process](../../../../re/tooling/sw2026/imported_body_source/VerifyLocalCylinderWrite.py)
· [Guarded result](../../../../re/solidworks/measurements/2026/SdkBareCylinderComposition01.json)
· [Disclosed native lifecycle](../../../../re/solidworks/measurements/2026/GeneratedLocalCylinderPartNative01.json)

The private source lock predates this constructor. Native evaluation of those
sources and public writer qualification are separate milestones.
[Prospective source lock](../../../../re/solidworks/measurements/2026/SealedPeriodicImportedSourceLock01.json)
