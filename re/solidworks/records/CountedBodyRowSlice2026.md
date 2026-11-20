# Counted archive body rows for SOLIDWORKS 2026

| Delivery item | Scope |
| --- | --- |
| Task | `B03-SW2026-BODY-ROWS` |
| Owner | PR #121 takeover team |
| Delivery | [PR #176](https://github.com/TryUniCAD/Kit/pull/176) from `codex/solidworks-counted-body-rows` |
| Prerequisite | [Accepted object and map archive layer](https://github.com/TryUniCAD/Kit/commit/77d2f7c4380355e40d65376a00151d82812759dc), including the shared count and scalar codecs |
| Exit | Fresh-process counted-row generation and reading, the malformed input cases, and current-revision CI and review |

## Source and scope

The 13-file source closure of `ReadArrayMut` and `WriteArrayMut` comes
from [PR #121's pinned aggregate](https://github.com/TryUniCAD/Kit/commit/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f).
The package includes the field, scope, frame and body context types, the
ordered row traversal and the count read and write operations. Its prior
dependencies are `Counts/{EncodeCount,ReadCount}`, `Maps/ArchiveMaps`,
`Objects/ArchiveNode`, `Reading/{GraphReader,ReadNativeScalar}` and
`Scalars/EncodeScalar`.

The original 13-file production source manifest SHA-256 is
`02a2356fcc8a6c6e92dd4c68b048e91f3c7fa7e626920004638b3cc8719720d0`.
The revised 18-file production manifest is
`a11542d0ab8aa59fa031c70553228660080cd802a5d51c1878a9ca9de3e3eb31`.
Ten pinned files are unchanged. The revision updates `NormalizeCount`,
`ReadCountMut` and `WriteCountMut` and adds `ApplyCountMode`,
`ReadSplitMut`, `EncodeCountForm`, `SelectCountWord` and `WriteSplitMut`.
Each manifest hashes the concatenation of sorted repository-relative paths,
each followed by a NUL, the lowercase file SHA-256 and a newline.

The archive grammar evidence applies to SOLIDWORKS 2026 SP05.2
`34.5.2.0604` and its ordinary version-19000 profile. The lightweight
manager header's `f08` owns an embedded `suObList`. The manager
and child stores at `sldarchiveu.dll!0x319f7270` and `0x319f6d90`
bound its counted object list and child field order.
[Configuration manager header construction](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/ConfigurationManagerHeader2026.md)

Vendor and framework count escapes have independently traced owners.
Both use the unsigned short marker `0xffff` before a 32-bit word. The
framework accepts a further 64-bit word after the 32-bit marker
`0xffffffff`. The vendor reads that 32-bit word as the value. The
archive body scope records an integer `#width` suffix on the count key
only when a decoded prefix differs from the canonical store width.
An inline count uses the rule name with `#count` as its count key.
Equivalent rows preserve the accepted width using the documented
markers. Physically valid retained widths are ignored when a changed
row length requires a fresh count. A width with a missing, incompatible
or unrepresentable word fails closed. After encoding, the write scope
exposes the actual prefix width while the source mapping retains its
input width.
[Count owners and framing](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/MfcCountArchive2026.md)
[Width gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/CountWidthsRetainWireIdentity.md)

Split counts store high then low unsigned words. The mate-group
`f4e8` rule exposes a combined count. A separate `Unsigned` rule can
ignore a nonzero high word for row traversal and still retain both
words for an equivalent write. If retained words no longer describe
the rows, the writer computes the count and updates the field scope
overlay. The SDK limits normalized repetition to ten million and
commits the count cursor and fields only after successful validation.
The complete body dispatcher and native class layouts have separate
acceptance requirements.
[Modeled field rules](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/ConfigBodyGrammar2026.md#field-operations)
[Resolved assembly field owners](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/ResolvedBodyGrammar2026.md)

## Process evidence

The [probe](../../tooling/sw2026/CheckCountedRows.py) writes a synthetic
scalar-row record from a JSON input. A second process reads the generated
wire and publishes decoded fields. Both paths check row indexes, parent
scopes and mapping identity. The writer checks that the computed count is
visible through the scope and that the authored mapping retains its stale
count. The reader requires complete consumption.

The [authored case](../../../tests/Convert/Solidworks/ArchiveRows/CountedRowTests.py)
compares the 40 bytes against independent little-endian framing.
It replaces implausible vendor and framework counts, preserves the
signed minus-seven count for an empty array and checks combined and
separate split fields. The
[escaped-width case](../../../tests/Convert/Solidworks/ArchiveRows/CountWidthTests.py)
starts from independently framed vendor and framework prefixes and
checks exact replay and changed lengths in fresh write processes. It
also checks the emitted widths through scope lookup in each process.
The [malformed reads](../../../tests/Convert/Solidworks/ArchiveRows/RejectRowTests.py)
require the original cursor, unchanged scope and no decoded result.
The [malformed writes](../../../tests/Convert/Solidworks/ArchiveRows/RejectWidthTests.py)
cover incompatible or missing width fields and an invalid count mode.
Current process results await remote CI. Native configuration-manager
header replay, Config and ResolvedFeatures grammar and native document
acceptance have separate exits.

Scoped Black, Ruff, Mypy, Pyright and steering checks passed. The static
import walk found no cycles across 32 reachable archive modules. The
donor scan found no recorded payloads across 3,261 production sources.
