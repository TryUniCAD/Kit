# Typed SOLIDWORKS archive wire primitives

The internal archive layer has memory-only codecs for vendor and MFC counts,
structural tags, CString text and fixed-width numbers. Each encoder derives
its bytes from an explicit value. Each reader reports the next byte offset.
The bounded cursor supports sequential count, text and scalar reads.
Scalar offsets are absolute. A rejected collection count leaves the cursor
at the count field.

Choose the count dialect at the calling field. Structural tags carry a
reference index or a null or new-class marker. Object resolution belongs to
the archive that owns the reference. CString values retain their source
encoding and new text uses UTF-16LE. The encoders choose canonical widths.

The [process integration](../../../tests/Convert/Solidworks/Archive/ArchiveWireTests.py)
encodes a synthetic nested record, compares its canonical bytes and reads it
back in a separate process. The long string case crosses into the u32
length form at 65,534 UTF-16 units. The
[ANSI process integration](../../../tests/Convert/Solidworks/Archive/AnsiWireTests.py)
checks byte identity in source replay and the Unicode requirement for
fresh output. Malformed framing fails before output is published.
Current-revision results are pending remote CI.
[Exact build, source attribution and evidence](../../../re/solidworks/records/ArchiveWirePrimitiveSlice2026.md)
