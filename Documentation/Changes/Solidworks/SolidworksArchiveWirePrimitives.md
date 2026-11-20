# Typed SOLIDWORKS archive wire primitives

The internal archive layer has memory-only codecs for vendor and MFC counts,
structural tags, CString text and fixed-width numbers. Each encoder derives
its bytes from an explicit value. Each reader reports the next byte offset.
The bounded cursor supports sequential count, text and scalar reads.

Choose the count dialect at the calling field. Structural tags carry a
reference index or a null or new-class marker. Object resolution belongs to
the archive that owns the reference. CString values retain their source
encoding and new text uses UTF-16LE. The encoders choose canonical widths.

The [process integration](../../../tests/Convert/Solidworks/Archive/ArchiveWireTests.py)
encodes a synthetic nested record, compares its canonical bytes and reads it
back in a separate process. Malformed counts, tags, strings, scalars and
trailing data must fail before output is published. Current-revision results
are pending remote CI.
[Exact build, source attribution and evidence](../../../re/solidworks/records/ArchiveWirePrimitiveSlice2026.md)
