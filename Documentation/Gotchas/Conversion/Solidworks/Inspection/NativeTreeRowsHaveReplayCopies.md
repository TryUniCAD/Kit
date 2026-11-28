# Native tree rows carry redundant replay copies

A strict cold SOLIDWORKS distance chamfer read keeps auxiliary native
tree rows. Each `NativeFeature.object_data.record_data` value contains
the row's original archive bytes. Removing the top-level
`solidworks_source_bytes` key alone leaves those copies in JSON and
triggers the recursive retained-data guard.

The qualified chamfer snapshot first regenerates and strictly decodes
the entire source. It retains the source SHA-256, every row, native
type ID, archive span and owner provenance. It omits the complete
replay envelope and those per-row `record_data` copies. The original
typed self locator and epoch let the exact cold writer repeat the
complete comparison on reload. A stale or arbitrary native source
continues to refuse conversion.

[Measured distance chamfer change](../../../../Changes/Solidworks/Construction/SolidworksMeasuredDistanceChamfers.md)
