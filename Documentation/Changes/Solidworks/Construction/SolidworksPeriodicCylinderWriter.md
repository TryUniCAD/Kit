# SOLIDWORKS periodic cylinder writer

Call `write_document(document, path)` with an ordinary `.SLDPRT` path and
a millimetre document containing one closed periodic cylinder B-rep and
one active configuration. The destination supplies the part name. The
writer preserves the actual configuration name and builds a single native
BaseBody feature named `Imported geometry`. This geometry-only profile
supplies no sketches or driving dimensions.

The input must have two outward cap planes and two full circular rims
with their exact seam ownership. Their centres must share the positive
mantle axis. Source file identity, geometry provenance, extra document
content and alternative boundary profiles are refused before publication.
The result reports two native transfers, B-rep and configurations.

Kit authors one `Import ambient` light with the same creation event as
the part. The chosen coefficients and names are explicit target settings.
SOLIDWORKS obtains its session defaults from a separate preference vector.
[Native lighting rules](../../../../re/solidworks/records/StockPartLighting2026.md)
· [Periodic span guard](../../../Gotchas/Conversion/Solidworks/Archive/Partition/LocalBodies/PeriodicCapsMustShareAxis.md)

Guarded preparation at the disclosed TranslatedZ file's exact logical
destination and creation time reproduced the 8,995-byte archive that
passed clean native open, rebuild, save and fresh reopen on
SOLIDWORKS 2026 SP05.2. The staged SDK path also produced a signed
oblique solid in its authored configuration, passed strict SDK readback
and preserved the existing destination through invalid requests. The
host staging check starts no native application and uses zero input
file reads during construction.
[Disclosed native lifecycle](../../../../re/solidworks/measurements/2026/GeneratedLocalCylinderPartNative01.json)
· [Guarded SDK proof](../../../../re/tooling/sw2026/imported_body_source/VerifyPublicCyl.py)
· [Locked geometry lifecycles](../../../../re/solidworks/measurements/2026/SealedPeriodicCylinderLocalNative01.json)
