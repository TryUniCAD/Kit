# Share the SOLIDWORKS 2026 header graph

The SDK archive layer reads and writes the typed graph in `Header2` and
`Contents/Config-0-ModelHeader` for ordinary SOLIDWORKS 2026 version 19000.
Both directions use the same field order and retain shared object identity,
file references, bounds, revision logs and the source string encoding.
The opt-in drawing reader continues to project its self file and external
file table from these records.

The planar assembly research generators now build both standalone streams
through this SDK codec. The graph comes from the authored document and
assignment rules. Four guarded bundles reproduced their earlier eight
file hashes with zero runtime input reads.

The exact round-trip audit checked 31 logical streams across 17 disclosed
part, assembly and drawing files. The synchronized assembly process checks
another ten header streams at the application boundary. The codec rejects
other archive versions, unknown classes and a nonnull header configuration
object. The public adapter remains read-only.

[Header graph and verification procedure](../../../../re/solidworks/records/SharedSdkHeaderGraph2026.md) · [Disclosed sample receipt](../../../../re/solidworks/measurements/2026/SharedSdkHeaderGraph01.json)
