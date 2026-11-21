# Preserve explicit empty SOLIDWORKS part text scopes

The shared version-19000 part constructor can emit an empty text property
scope when the neutral model declares it. Set `PartTextInput.EmptyScopes`
to the present empty scopes among `summary`, `document` and `configuration`.
An ordinary empty map with no presence flag continues to omit its stream.

The serializer builds the XML root, sections and reserved records using
the existing text rules. The public SDK reports the declared empty scopes
and their configuration owner. Three disclosed imported parts passed clean
native open, rebuild, save and fresh reopen, retaining nine empty text
scopes across the three parts. The binary manager remains a separate owner.
[Format and verification record](../../../../re/solidworks/records/ImportedEmptyPartText2026.md)
