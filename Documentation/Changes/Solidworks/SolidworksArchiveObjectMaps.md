# Typed SOLIDWORKS archive objects and maps

The internal archive graph layer assigns map slots to runtime class
descriptors and objects during traversal. A new object enters the map
before its body is processed, so cyclic and repeated references resolve
to the same node. Distinct objects keep separate slots when their fields
match.

A stream can seed its map with the prior stream's snapshot. The initial
counter must agree with the snapshot, which freezes map membership and
retains node objects. The graph reader uses the shared cursor and class
descriptor framing. Callers supply the body grammar and its schema and
version checks. A failed body callback invalidates the stream's map and
cursor state.

Class descriptors require a nonempty ASCII name. The reader limits open
object bodies to 128 and resolves nulls and backreferences at that depth.

The [linked graph process checks](../../../tests/Convert/Solidworks/ArchiveGraph/ArchiveGraphTests.py)
compare two authored streams with independent expected bytes and verify
object identity through a fresh reader process. The
[rejection cases](../../../tests/Convert/Solidworks/ArchiveGraph/GraphRejectTests.py)
cover the wrong reference kind, a mismatched inherited counter and an
empty nested class name. The [depth process](../../../tests/Convert/Solidworks/ArchiveGraph/GraphDepthTests.py)
checks terminal references at the limit and refusal of an additional
body for both existing-class references and new declarations.
Current-revision results are pending remote CI.
[Implementation provenance and exact-build evidence](../../../re/solidworks/records/ArchiveObjectMapSlice2026.md)
