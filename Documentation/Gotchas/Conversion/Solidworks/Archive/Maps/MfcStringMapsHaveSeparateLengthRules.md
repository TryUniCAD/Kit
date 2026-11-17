# Framework string maps have separate string-length rules

## Expectation

Every native SOLIDWORKS CString reaches the vendor's shared string-length reader.

## Actual behavior

The ordinary `su_CMapStringToString` wrapper delegates to MFC ordinal 12804.
That body uses the framework string reader and writer. Its reader accepts a
u64 length after the byte, word and double-word escape markers. After a Unicode
indicator, an inner word `0xfffe` is interpreted as length 65534. The vendor
reader instead treats that word as its repeated Unicode sentinel.

The framework's canonical wide writer reads a signed-32-bit CString length and
emits the same Unicode framing used by the shared ordinary codec. Valid lengths
at least 65534 use the double-word form. The current native discovery maps are
empty, so those source rows alone would not identify this distinction.

## Workaround

Bind the actual map count and string helpers for the selected runtime. Use the
framework count grammar and the existing canonical CString profile within its
declared unit bound. Retain explicit rejection of extended or noncanonical
length aliases until their raw framing and allocation behavior are modeled.
Keep DB-mode flags distinct from the research archive condition word.

[Pinned bodies and mapped-byte proof](../../../../../../re/solidworks/records/ContextAndStringMapArchive2026.md)
