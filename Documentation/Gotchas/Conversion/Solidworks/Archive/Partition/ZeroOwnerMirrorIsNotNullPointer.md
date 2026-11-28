# Owner mirror zero can name an indexed file

The small-array `FACE_ID_2001` builder writes a zero mirror for a null runtime owner. A nonnull owner can also write zero when its allocated external-reference index is zero. The load-time helper uses the actual index and can fall back to the local owner when lookup misses.

Derive file ownership from the real external-reference table and configuration. Load-time repair supplies absent pointers before the ordinary face getter consumes them. [Pointer and mirror source](../../../../../../re/solidworks/records/DownstreamRuntimeOwnerPointers2026.md) · [Ordinary reload](../../../../../../re/solidworks/records/DownstreamPartOwnerReload2026.md)
