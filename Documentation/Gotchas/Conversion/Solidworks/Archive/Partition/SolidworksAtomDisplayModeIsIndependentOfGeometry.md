# SOLIDWORKS atom display mode is independent of geometry

The atom serializer field `f19c` is the atom's display mode. Both 2026 atom
constructors set it to six before a body exists, and
`moAtom_c::getDisplayMode` reads it directly. The six faces in an ordinary
rectangular boss happen to equal that default.

For a fresh atom, construct the display mode from its constructor or the
authored appearance state. Count faces from the Parasolid topology.

[Constructor and geometry evidence](../../../../../../re/solidworks/records/GeneratedRectanglePartition2026.md)
