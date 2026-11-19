# Strict reads retain source-owned state

A strict FreeCAD read can return a valid document with a complete editable sketch and boss while retaining additional source features, parameters, metadata and payloads. The current public SOLIDWORKS writer refuses these intact source envelopes. It also checks their actual model owners independently.

For admission measurements, keep the original path and the full returned model. Record the public write outcome separately from lower owner diagnostics. Source-aware translation must bind the retained semantics before qualifying a native write.

[Public census evidence](../../../../re/solidworks/records/PublicFcstdWriterCensus2026.md)
