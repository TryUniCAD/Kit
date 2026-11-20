# Read compatible SOLIDWORKS part text

The normal `open_document` part reader exposes authored summary text in
`metadata["document_summary"]`, file-level custom text in
`metadata["custom_properties"]`, and configuration custom text in the
active configuration's `attributes["custom_properties"]`.

This profile covers ordinary version-19000 parts. The configuration
property stream must identify the actual active, unparented configuration
in the saved directory and its physical part streams. The supported
binary property manager is absent or empty. Name dictionaries, raw and
evaluated text and reserved section fields must agree. Unsupported or
malformed scopes withhold all property bags and provide an information
diagnostic. The ordinary model read remains available.

Check `metadata["solidworks.part_text_properties"]["status"]` for
`complete` before relying on the text. The reader leaves files without
these property streams on their previous path. It preserves separate
file and configuration values even when they share a name.

Three disclosed native files match the independently observed property
values through the public reader. The advanced property control keeps
its B-rep and native feature tree while withholding all property scopes.
Two generated files retain their existing modeling refusals and pass
separate typed property checks.

[SDK evidence](../../../../../re/solidworks/records/LiteralPartTextReaderSlice2026.md)
· [Saved directory ownership](../../../../Gotchas/Conversion/Solidworks/Archive/Properties/SavedDirectoryOwnsPartText.md)
