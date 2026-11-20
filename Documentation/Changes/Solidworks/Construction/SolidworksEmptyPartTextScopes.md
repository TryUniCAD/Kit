# Preserve explicit empty SOLIDWORKS part text scopes

The shared version-19000 part constructor can emit an empty text property
scope when the neutral model declares it. Set `PartTextInput.EmptyScopes`
to the present empty scopes among `summary`, `document` and `configuration`.
An ordinary empty map with no presence flag continues to omit its stream.

The serializer builds the XML root, sections and reserved records using
the existing text rules. The public SDK reports the declared empty scopes
and their configuration owner. Native testing and the binary manager
boundary are recorded separately.
[Format and verification record](../../../../re/solidworks/records/ImportedEmptyPartText2026.md)
