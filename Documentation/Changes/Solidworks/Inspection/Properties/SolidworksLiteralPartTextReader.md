# Read compatible SOLIDWORKS part text

The normal `open_document` part reader exposes authored summary text in
`metadata["document_summary"]`, file-level custom text in
`metadata["custom_properties"]`, and configuration custom text in the
active configuration's `attributes["custom_properties"]`.

This profile covers ordinary version-19000 parts. The configuration
property stream must identify the active, unparented configuration in the
saved directory. The reader checks for its corresponding physical part
streams. Full validation of the physical configuration body remains open.
The supported binary property manager is absent or empty. Name dictionaries, raw and
evaluated text and reserved section fields must agree. Unsupported or
malformed scopes withhold all property bags and provide an information
diagnostic. The ordinary model read remains available. A strict SDK
conversion to a different format refuses this diagnostic result before
publishing output.

The version-18000 compatibility path verifies absence of authored text
through the complete supported binary property owner and all recognized
text scopes. Empty scopes allow strict conversion without adding text
metadata. Authored text or an unsupported owner still produces the
strict conversion refusal.

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
· [Legacy empty manager](../../../../Gotchas/Conversion/Solidworks/Archive/Properties/LegacyEmptyTextManagers.md)
