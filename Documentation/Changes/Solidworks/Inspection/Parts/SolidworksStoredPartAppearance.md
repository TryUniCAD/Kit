# Stored SOLIDWORKS part appearance

Use `convert.open_document(part, include_native_appearance=True)` to inspect the
stored appearance of a SOLIDWORKS format-4, version-19000 part. For the supported
active configuration 0, the SDK attaches the physically owned visual record to
`document.metadata["solidworks.part_visual"]`. The option is off by default.

The evidence separates model and hidden-line RGB, legacy optical values,
classic renderer color and roughness, and the basic PBR albedo, metallic and
roughness. The classic locator is retained as saved text. Inspection does not
open a file at that path. A primary texture retains its nineteen typed wire
fields. Their resource and mapping meanings remain unqualified.

A visual label such as "Steel" does not establish density, physical assignment,
or an effective body or face color. The SDK must not add a material or a body
link from this record. Strict reads remain available if the visual record is
outside the bounded decoder. Explicit inspection records an unsupported
status and diagnostic while preserving the regular part model.

Neutral model JSON can retain this evidence. Native publication through the
registry or the direct SOLIDWORKS writer refuses a document carrying the
evidence before it writes to the destination. Physical, portable appearance and
native round-trip acceptance remain separate.

All seven material visual integration cases passed on Windows with Python 3.14.6.
The cases cover the pinned L1 native part with and without B-rep, JSON
persistence, unsupported inspection on a separate native source, unchanged
direct and registry write destinations, the bounded
archive refusal, and exact replay of the authored primary texture.
See the [visual codec evidence](../../Archive/Configuration/SolidworksPartMaterialVisual.md)
and [appearance-domain gotcha](../../../../Gotchas/Conversion/Solidworks/Readers/StoredMaterialVisualDomains.md).

The native reopen exposed separate part, body and face appearances on a
two-solid contrast. The part RGB matched the bounded stored record. The
public SDK projected one body and withheld the face texture. See the
[measured face texture contrast](../../../../Gotchas/Conversion/Solidworks/Readers/FaceTextureChangesLegacyOptics.md).
