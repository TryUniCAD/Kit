# Inspect a SOLIDWORKS sketch with a conflicting plane reference

The strict SOLIDWORKS reader rejects a principal-plane reference whose
stored basis or axis kind disagrees with the referenced plane. Use
`open_document(path, include_brep=False, strict=False)` to inspect a part
with this conflict. The reader retains the sketch as unresolved and
reports the rejected plane ID and framed fallback. The fallback carries
no typed support-reference provenance.

Two disclosed circular and rectangular controls exercise the strict
refusal and permissive inspection. Five unchanged circular inputs retain
their editable sketch and JSON round trip. [Reader evidence](../../../../../re/solidworks/records/AggregateReaderRepairs2026.md)
