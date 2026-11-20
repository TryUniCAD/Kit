# Archive body values for SOLIDWORKS 2026

| Delivery item | Scope |
| --- | --- |
| Task | `B03-SW2026-BODY-VALUES` |
| Owner | PR #121 takeover team |
| Delivery | [PR #177](https://github.com/TryUniCAD/Kit/pull/177) from `codex/solidworks-archive-body-values` |
| Prerequisite | [Counted body rows](CountedBodyRowSlice2026.md) at [PR #176's queue revision](https://github.com/TryUniCAD/Kit/commit/002c4f6d5967788bd1734220148adb1526a465fa) |
| Exit | Independent wire bytes, field values and alias identity in fresh read and write processes, malformed-case refusals, current-revision CI and review |

## Source closure

Six production files come from [PR #121's pinned aggregate](https://github.com/TryUniCAD/Kit/commit/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f).
`ReadRuleValue`, `EncodeBodyText` and `WriteValueMut` match the pin.
`ReadValueMut` adds a canonical text check through the new
`ReadBodyTextMut` operation. The tag and descriptor callbacks keep their
pinned bodies and live in separate modules. `WriteNodeMut` checks the
object map before opening a body and restores depth around the store.
The existing `RuntimeClass` constructor enforces a nonempty name before
a descriptor can reach graph allocation or serialization.

The six pinned source files have manifest SHA-256
`d6e30ea69562b65f1301052db80c4b66cc2e2a871cbf469c5765aa62dfdcb7cb`.
The nine delivered production files have manifest SHA-256
`6c0be2c7ad2d4482a37a47cf4c1c0722af17e35c9330598fbf324cedf46f92ad`.
Each manifest hashes the concatenation of sorted repository-relative
paths, each followed by a NUL, the lowercase file SHA-256 and a newline.

Field rules, scopes, frames and counted rows come from the prerequisite.
The handlers call the existing scalar, string, tag, graph and map
operations. The process supplies explicit field callbacks. Full body
dispatch and CMgrHdr2 stream support have separate acceptance gates.

## Inherited body links

The body codec accepts nulls and concrete archive nodes, including
nodes from a materialized preceding map. The pinned body writer
requires an archive node and its graph reader rejects unresolved
external object references. The low-level object routines retain a
symbolic `ExternalRef` for a missing inherited slot. The research
serializer uses those routines for sparse-prefix inspection.
[Pinned body writer](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/src/convert/adapters/solidworks/Archive/Bodies/Writing/WriteNodeMut.py)
[Pinned graph reader](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/src/convert/adapters/solidworks/Archive/Reading/ReadGraphNode.py)
[Research bridge](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/tooling/sw2026/serial/Core.py)

Ordinary configuration loading binds actual header nodes to the
configuration map. ResolvedFeatures and MatesList each take an actual
preceding snapshot. Body-value support at this scope requires those
referenced objects to be present.
[Header bindings](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/src/convert/adapters/solidworks/Archive/Bodies/Reading/ReadDirectMut.py)
[ResolvedFeatures handoff](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/src/convert/adapters/solidworks/Archive/Resolved/ReadResolvedMut.py)
[MatesList handoff](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/src/convert/adapters/solidworks/Archive/Mates/ReadMatesMut.py)

The [inherited-link process cases](../../../tests/Convert/Solidworks/ArchiveValues/InheritedTests.py)
read an independently framed primary into a fresh seed in each write
and read process. The linked record uses inherited class slot 3
and object slot 4, and opens only slot 5. Its decoded class and link
are the same objects as the corresponding primary entries. A sparse
control removes slot 4 at the same base and requires read and write
refusal before a result is published.

## Rules and native evidence

The native references use SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`
and the ordinary archive version-19000 profile. The
[scalar census](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/LinkedGraphScalarConstruction2026.md)
binds scalar representations and linked context. The
[configuration field operations](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/ConfigBodyGrammar2026.md#field-operations)
identify distinct shadow-write fields and their declared source aliases.
The [lightweight manager header evidence](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/ConfigurationManagerHeader2026.md)
binds the native scalar and CString fields and the embedded object list
that will use these primitive handlers.

The wide CString store in `swccu.dll`, `[0x31a34590,0x31a346e8)`,
establishes the three canonical count-prefix widths. They are one
byte for up to 254 units, three bytes for 255 through 65,533 units
and seven bytes from 65,534 units. The native length reader,
`[0x31a37e00,0x31a37e64)`, accepts longer representations.
A body field validates the width through that shared length grammar
before the cursor advances. Canonical ANSI has a typed source-frame
representation, with fresh text supplied as Unicode.
[Native function hashes, marker grammar and mode limits](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/CStringArchive2026.md)
[Body text gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Strings/BodyTextRequiresCanonicalLengths.md)

Native object store allocates a class slot and a new object slot before
its body fields. Null and object references consume no slots. At Kit's
128-body cap the body writer checks whether a concrete node would open
another body. It accepts a mapped backreference or a null and restores
the open-body count when a callback returns or raises. The graph uses
the compact structural-tag encoding and retains the shared tag codec's
documented normalization of alternative widths.
[Native tag ownership](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/ArchiveTagGrammar2026.md)
[Open body depth](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/ArchiveDepthCountsOpenBodies.md)
[Nonempty class names](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/EmptyArchiveClassNames.md)

## Process verification

The [worker](../../tooling/sw2026/CheckBodyValues.py) uses the production
node, value and counted-row handlers. The independently framed
[synthetic records](../../../tests/Convert/Solidworks/ArchiveValues/BodyValueTests.py)
cover a signed scalar supplied through a declared source field alias,
an astral wide string, the 255-unit length
boundary, an ANSI source frame, a counted object array, shared
object identity, a backlink and null. The reader requires complete
consumption.

The [depth and descriptor cases](../../../tests/Convert/Solidworks/ArchiveValues/ValueDepthTests.py)
compare the 128-body output, including the terminal null and
root-reference tags, to independently framed wire bytes. A
[second depth case](../../../tests/Convert/Solidworks/ArchiveValues/CountDepthTests.py)
puts both links in real counted rows at every level and checks all
128 successive object indices in the fresh reader. The 129th body is
refused for both an existing class and a new class. The 129th body
in counted rows is also refused when it would register a new class.
An empty descriptor leaves the new output and archive map untouched. The
[text refusal cases](../../../tests/Convert/Solidworks/ArchiveValues/ValueRejectTests.py)
check rollback for overlong Unicode and ANSI count prefixes. These
cases are declared for remote CI. Native document load, rebuild
and editable behavior require separate oracle evidence.

## Counted callback stack

The two counted probe paths keep seven Python frames per open node
while descending to another node.

| Path | Live frames at the row's node field |
| --- | --- |
| Write | `WriteNodeMut`, `WriteObjectMut`, body callback, body field loop, `WriteArrayMut`, row field loop, `WriteValueMut` |
| Read | `ReadNodeMut`, `ReadObjectMut`, `ReadNodeBodyMut`, body callback, `ReadArrayMut`, row field loop, `ReadValueMut` |

At 128 bodies this is 896 live frames, plus the three outer calls in
the standalone process. The terminal reference and null paths add
at most six Python frames for tag and map operations. Other framing
helpers return before descending into another body. The write wrapper
counts only a concrete unmapped node as open, with its earlier depth
restored after both success and failure. The read body callback enters
its one known array directly.

Adding the outer body field loop on the counted read path costs one
frame per body. Eight frames per body require 1,024 frames at depth
128 before transient and caller frames. The full recursive dispatcher
therefore needs its own compatible stack strategy before it can claim
the same depth. The probe uses the default process stack and the stated
callbacks.
[Counted body stack gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Graph/CountedBodiesAddStackFrames.md)

Scoped Black, Ruff, Mypy, Pyright and steering checks passed. The
archive import walk found no cycles across 53 modules. The donor scan
found no recorded payloads across 3,269 production sources.
