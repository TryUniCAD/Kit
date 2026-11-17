# Construct a coincident planar mate in a generated assembly

The version-19000 research builder writes an aligned coincident mate
between two principal planes on separate occurrences of one generated
child part. It writes the full mate-list record and derives the assembly
counter, configuration progress, paired header logs and authored fixed
anchor.

Two authored assembled graphs pass exact round trips over six logical
streams. The changed placement and mate name produce different stream
lengths with zero runtime input file reads. Unsupported alignment or
missing selection fails the process. Native solve, save and held-out
acceptance are measured separately. The first generated pair passed native
load, rebuild, child edit, save and reopen starting from coplanar positions.
Placement correction and held-out acceptance remain open.

[Input and stream rules](../../../../../../re/solidworks/records/AssemblyCoincidentConstruction2026.md)
· [Guarded receipt](../../../../../../re/solidworks/measurements/2026/GeneratedCoincidentMateBundle01.json)
· [Native trial](SolidworksCoincidentMateNativeProof.md)
