# Measured SOLIDWORKS parts need an empty stream

Staging a part into an empty internal buffer can establish the measured
archive hash even when the caller's destination has a prefix or a stale
tail. The completed caller stream must contain exactly the measured
archive for whole-output acceptance.

Use a writable, seekable binary stream with zero length and a cursor at
position zero. The direct writer and registry verify the actual destination
using seek and tell. A refused destination keeps its existing bytes and
position. Other writers retain their normal stream semantics.

[Measured publication](../../../Changes/Solidworks/Construction/SolidworksMeasuredPartPublication.md)
