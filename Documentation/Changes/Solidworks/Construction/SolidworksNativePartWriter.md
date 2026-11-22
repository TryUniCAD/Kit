# Native SOLIDWORKS writer for an ordinary line-loop boss

Kit can write a native `.SLDPRT` from a neutral millimetre document with one
closed line loop on Front Plane, one forward blind boss, one driving depth
`D1`, one active configuration and one resulting solid. The complete
ten-stream file is generated from the model and the pinned SOLIDWORKS 2026
SP05.2 rules.

Use `write_document` with a `.SLDPRT` path whose basename matches the
document name. For a binary stream, select `solidworks.sldprt` and give
`values["final_destination"]` an absolute part path. The staged write
preserves the final filename. Unsupported features, material overrides,
extra document state and unqualified assembly and drawing destinations fail
before publication.

The three original native polygon cases pass controlled native depth edits
and fresh reopen with source geometry and tree parity. Two further parts use
the default recipe and pass all 240 numeric checks across six fresh
processes. Four guarded processes reproduce all ten streams with zero
runtime input-file reads. The public process checks cover staged paths,
binary streams, strict polygon readback and rejected writes. Four guarded
calls through `write_document` reproduce the exact native-tested input
hashes.
[Original polygon evidence](../../../../re/solidworks/measurements/2026/SdkOriginalPolygonNative01.json) ·
[Default recipe evidence](../../../../re/solidworks/measurements/2026/SdkDefaultPartNative01.json) ·
[Public API evidence](../../../../re/solidworks/measurements/2026/SdkPublicPartWriter01.json) ·
[Stream owners](../../../../re/solidworks/records/PlainPartWriter2026.md) ·
[Usage and limits](../../../Reference/Adapters/Solidworks.md#writing)
