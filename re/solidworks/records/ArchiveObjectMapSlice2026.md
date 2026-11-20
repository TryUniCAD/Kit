# SOLIDWORKS 2026 archive object and map extraction

Task `B03-SW2026-ARCHIVE-OBJECTS` takes 27 production files from
[PR #121's aggregate revision](https://github.com/TryUniCAD/Kit/commit/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f).
They comprise `Archive/Maps`, `Archive/Objects` and the graph cursor modules
`GraphReader.py`, `ReadGraphNode.py` and `ReadTypedNode.py`. The
[initial extraction](https://github.com/TryUniCAD/Kit/commit/0d8b56f28c0ea4225fc5725a7dc86bedcbc1b604)
matched the pinned revision across all 27 files. Their direct dependencies
are `BinaryReader.py`, `ArchiveTag.py` and `ReadTag.py` from the
[wire primitive parent](https://github.com/TryUniCAD/Kit/commit/fcd4852563482c5af9299edb4a3096cc8f763f42).

The review revision retains 26 matching files. `ReadGraphNode.py` checks
new-body tags before advancing the cursor. `ReadNodeBodyMut.py` tracks open
bodies and `ReadTypeDescMut.py` owns descriptor framing and the empty-name
check. Its legacy counterpart also rejects a zero-length descriptor name.

The original 27-file manifest SHA-256 was
`2e8b69615518fa47afe3b2321764c80a0c60232f2f85e9b3fd7b1c17d2f06fe1`.
The revised 29-file manifest SHA-256 is
`f07dbcc65240bf4c6bfbd91b5627534e411b645028fa4512d3ea948265fcc7e5`.
The manifest concatenates sorted repository-relative paths, each followed
by a NUL, the lowercase file SHA-256 and a newline.

## Native ownership

The [build and compatibility record](Solidworks2026ArchiveCompatibility.md)
binds the archive rules to SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`.
`swccu.dll` allocates a slot for each new descriptor and object. The
load and store functions register a new object before visiting its
fields. Null and object references consume no map slots.
[Native function extents and hashes](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/ArchiveTagGrammar2026.md)

The native archive handoff at `swccu.dll` address `0x31a39210` carries
the map and counter to the next stream. The resolved-feature stream
prefix carries the inherited count as a u32. The direct-binding calls
assign slots to existing header objects with no wire body. The prior
record identifies the native owners, module manifest and an earlier
remote job that compared eight linked resolved streams.
[Native handoff and earlier compatibility evidence](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/ArchiveMapConstruction2026.md)

## Focused verification

The [authored linked graphs](../../../tests/Convert/Solidworks/ArchiveGraph/ArchiveGraphTests.py)
use two class descriptors, a shared leaf, a field-equal distinct leaf and
cyclic references. The writer computes the primary map and a linked
stream with inherited counter 6. The reader resolves its inherited class
and objects from the same entries, preserves the leaf identities and
allocates one new object. The test compares both outputs with independently
specified wire bytes and checks the decoded object and class slots.
The [malformed controls](../../../tests/Convert/Solidworks/ArchiveGraph/GraphRejectTests.py)
require failure on a class slot used as an object, a different inherited
counter or an empty nested descriptor name. The [depth boundary process](../../../tests/Convert/Solidworks/ArchiveGraph/GraphDepthTests.py)
resolves a terminal root backreference and null at 128 open bodies and
rejects an otherwise complete 129th body. Process verification is pending
remote CI.

Scoped Black, Ruff, Mypy, Pyright and steering checks passed. The
production donor scan found no recorded payloads across 3,183 files.
[Open body depth](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/ArchiveDepthCountsOpenBodies.md)
[Nonempty archive class names](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/EmptyArchiveClassNames.md)

The graph cursor handles descriptor framing and structural references.
Native header, configuration manager and feature stream bodies depend on
their typed field owners and admission rules. Full-file construction and
native acceptance have separate evidence requirements.
