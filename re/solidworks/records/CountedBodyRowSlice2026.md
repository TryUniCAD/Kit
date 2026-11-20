# Counted archive body rows for SOLIDWORKS 2026

| Delivery item | Scope |
| --- | --- |
| Task | `B03-SW2026-BODY-ROWS` |
| Owner | PR #121 takeover team |
| Delivery | Separate main-target PR from `codex/solidworks-counted-body-rows` |
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

The pinned and delivered production source manifest SHA-256 is
`02a2356fcc8a6c6e92dd4c68b048e91f3c7fa7e626920004638b3cc8719720d0`.
The manifest concatenates sorted repository-relative paths, each followed
by a NUL, the lowercase file SHA-256 and a newline.

The archive grammar evidence applies to SOLIDWORKS 2026 SP05.2
`34.5.2.0604` and its ordinary version-19000 profile. The lightweight
manager header's `f08` owns an embedded `suObList`. The manager
and child stores at `sldarchiveu.dll!0x319f7270` and `0x319f6d90`
bound its counted object list and child field order.
[Configuration manager header construction](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/ConfigurationManagerHeader2026.md)

Vendor and framework count escapes have independently traced owners.
The typed configuration field rules preserve raw count words when their
interpretation matches the modeled row count. Otherwise the writer
computes the count and makes it available through the field scope overlay.
The SDK limits normalized repetition to ten million. The complete body
dispatcher and native class layouts have separate acceptance requirements.
[Count owners](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/MfcCountArchive2026.md)
[Modeled field rules](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/ConfigBodyGrammar2026.md#field-operations)

## Process evidence

The [probe](../../tooling/sw2026/CheckCountedRows.py) writes a synthetic
scalar-row record from a JSON input. A second process reads the generated
wire and publishes decoded fields. Both paths check row indexes, parent
scopes and mapping identity. The writer checks that the computed count is
visible through the scope and that the authored mapping retains its stale
count. The reader requires complete consumption.

The [authored case](../../../tests/Convert/Solidworks/ArchiveRows/CountedRowTests.py)
compares the 16 bytes against independent little-endian framing. The two
authored rows determine the vendor count and an empty framework array
gets a zero count. The signed count word of minus seven represents an
empty array under the positive-count rule. The
[malformed cases](../../../tests/Convert/Solidworks/ArchiveRows/RejectRowTests.py)
require a diagnostic and no decoded result. Process results are pending
remote CI. Native configuration-manager header replay, Config and
ResolvedFeatures grammar and native document acceptance have separate
exits.

Scoped Black, Ruff, Mypy, Pyright and steering checks passed. The
static import walk found no cycles across the 27 reachable archive
modules. The donor scan found no recorded payloads across 3,238
production sources.
