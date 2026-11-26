# SOLIDWORKS 2026 archive wire primitive extraction

Task `B03-SW2026-ARCHIVE-CORE` takes the primitive implementations and bounded
read cursor from [PR #121's aggregate revision](https://github.com/TryUniCAD/Kit/commit/a93bb38bb3e51529c57872028f606588a5c54c61).
Its main baseline is [c34686b1](https://github.com/TryUniCAD/Kit/commit/c34686b1b448485ae78e00ceff89ee9536094473).
The source directories are `Archive/Counts`, `Archive/Tags`, `Archive/Strings`
and `Archive/Scalars`. The cursor and three scalar, text and count readers in
`Archive/Reading` use these operations. See the
[existing exact-build record](Solidworks2026ArchiveCompatibility.md) for
SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`.

The [initial extraction](https://github.com/TryUniCAD/Kit/commit/94fbd6044a63ec314e5466a38b8fee1d67ced1bc)
matched the aggregate across all 20 production files, with source manifest
SHA-256 `ed2bf7a57252ba3e2a72643634bfc8100238491c5fec29700b20abd7fe0b6cdd`.
Eighteen files still match byte for byte. The two review fixes are
`Archive/Scalars/ReadScalar.py`, which rejects negative offsets with the
existing `struct.error` exception type, and `Archive/Reading/ReadNativeCount.py`,
which validates capacity before advancing the cursor. Valid frames retain
their bytes and decoded positions. The revised source manifest SHA-256 is
`17db25ccab94d02d2387ef8d343868359756cc05c3a8821b95bc652fbe758330`.
The manifest concatenates sorted repository-relative paths, each followed
by a NUL, the lowercase file SHA-256 and a newline.
[Absolute scalar positions](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/ScalarOffsetsAreAbsolute.md)
[Count cursor validation](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/CountValidationPrecedesCursorAdvance.md)

## Wire ownership

| Primitive | Rule | Pinned owner evidence |
| --- | --- | --- |
| Count | The vendor archive uses u16 or `0xffff` plus u32. The MFC owner also uses u64 after both markers. Vendor u32 `0xffffffff` is a count. | [Complete vendor and MFC read and write bodies](https://github.com/TryUniCAD/Kit/blob/a93bb38bb3e51529c57872028f606588a5c54c61/re/solidworks/records/MfcCountArchive2026.md) |
| Tag | A u16 gives null, new class or a short reference. Escape `0x7fff` introduces a u32 reference with a class sign bit. Class index zero is invalid. | [Complete native structural functions](https://github.com/TryUniCAD/Kit/blob/a93bb38bb3e51529c57872028f606588a5c54c61/re/solidworks/records/ArchiveTagGrammar2026.md) |
| CString | The ordinary wide writer prefixes `ff fe ff` then counts UTF-16LE units. Single-byte lengths end at 254 and the marked u16 lengths end at 65533. The typed decoder also retains ANSI framing through Latin-1 byte identity. | [Exact operators and length helper](https://github.com/TryUniCAD/Kit/blob/a93bb38bb3e51529c57872028f606588a5c54c61/re/solidworks/records/CStringArchive2026.md) |
| Fixed-width scalar | Little-endian signed and unsigned integers have widths 8, 16, 32 and 64 bits. Floating fields use binary32 or binary64. | [Linked graph scalar census and usage](https://github.com/TryUniCAD/Kit/blob/a93bb38bb3e51529c57872028f606588a5c54c61/re/solidworks/records/LinkedGraphScalarConstruction2026.md) |

## Verification boundary

The earlier [archive CLI receipt](https://github.com/TryUniCAD/Kit/blob/a93bb38bb3e51529c57872028f606588a5c54c61/re/solidworks/measurements/2026/CurveCountAdmissionFeb8.json)
records 234 identical stream comparisons and zero unread tails for source
`feb8e11db40f0c50f13c9e673cdad87fa9dbc452`. The
[remote run](https://github.com/TryUniCAD/Kit/actions/runs/43816632345/job/133130055908)
reports 181 passing process cases, 158 fixture-dependent skips and zero
failures. Those results belong to the earlier linked archive path.

The [aggregate string integration](https://github.com/TryUniCAD/Kit/blob/a93bb38bb3e51529c57872028f606588a5c54c61/tests/Convert/Solidworks/Research/Curve/Strings/StringArchiveTests.py)
requires its full typed graph and saved control. The
[focused process integration](../../../tests/Convert/Solidworks/Archive/ArchiveWireTests.py)
uses the same separate-interpreter write and read pattern on authored
synthetic data. Its independent byte expectation covers both count
dialects, short and escaped references, Unicode unit and length boundaries,
and neighboring signed and floating fields. Remote CI will exercise the
new process cases on the delivery revision. The signed position in the
synthetic header exercises the absolute scalar reader. A count that
exceeds remaining capacity must report the original count offset. The
long Unicode record uses 65,534 UTF-16 units with a final surrogate pair.
The separate [ANSI source case](../../../tests/Convert/Solidworks/Archive/AnsiWireTests.py)
decodes independently authored bytes, replays them byte for byte and
checks that fresh output rejects the ANSI label.

Scoped Black, Ruff, Mypy, Pyright and steering checks passed. The production
donor scan found no recorded payloads across 3,154 files.

Class descriptors, map allocation and identity handoff, schema ownership,
and complete linked stream codecs are further slices. File construction
and native model acceptance require their own evidence.
