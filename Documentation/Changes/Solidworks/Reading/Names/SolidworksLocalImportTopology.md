# SOLIDWORKS local import topology counts

The ordinary SOLIDWORKS reader reports solid, shell, face, edge and
vertex counts from a proven local import. The existing body binding
must establish the actual import, shared atom, group name and complete
B-rep ownership. It retains the ordinary geometry selection and bounds.

All six disclosed original and native-saved snapshots report one solid,
one shell, six faces, twelve edges and eight vertices. Their selected
B-rep, design IDs and raw payloads agree with the previous reader.
Removing the actual feature-to-atom reference with the ordinary body
payload intact leaves the topology proof unavailable.

[Reader scope](../../../../../re/solidworks/records/SdkImportedLocalBodyReadback2026.md)
· [Topology replay](../../../../../re/solidworks/measurements/2026/ImportedNativeKeywordTopology01.json)
· [Owner proof gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Partition/LocalBodies/ImportedCountsFollowBoundSolid.md)
