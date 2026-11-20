# Read compatible SOLIDWORKS part text

The normal `open_document` part reader exposes authored summary text in
`metadata["document_summary"]`, file-level custom text in
`metadata["custom_properties"]`, and configuration custom text in the
active configuration's `attributes["custom_properties"]`.

This profile covers ordinary version-19000 parts. The configuration
property stream must identify the active, unparented configuration in the
saved directory. The reader checks for its corresponding physical part
streams. Full validation of the physical configuration body remains open.
The supported binary property manager is absent or empty. A manager is
checked even when it is the sole property owner. Name dictionaries, raw
and evaluated text and reserved section fields must agree. Unsupported
or malformed scopes withhold all property bags and provide an information
diagnostic. The ordinary model read remains available. The registry
refuses new native projections and direct writes when the root or an
owned component document has this status. The error retains the first
unavailable property's original cause. The registered interchange JSON
reader and writer can preserve an existing snapshot and its native
inspection status when configuration and geometry filtering are disabled.

The version-18000 compatibility path verifies absence of authored text
through the complete supported binary property owner and all recognized
text scopes. Empty scopes allow strict conversion without adding text
metadata. Authored text or an unsupported owner produces the same
write refusal. A relaxed read remains available for inspection.

Check `metadata["solidworks.part_text_properties"]["status"]` for
`complete` before relying on the text. The reader leaves files without
these property streams on their previous path. It preserves separate
file and configuration values even when they share a name.

Three disclosed native files match the independently observed property
values through the public reader. The advanced property control keeps
its B-rep and native feature tree while withholding all property scopes.
Two generated files retain their existing modeling refusals and pass
separate typed property checks.
The queued direct-write case reads back all three qualified text bags,
their configuration owner and original source provenance through JSON.
The queue also checks an actual unavailable part wrapped in an assembly
and a copy of a portable neutral CLI document with and without filtering.

[SDK evidence](../../../../../re/solidworks/records/LiteralPartTextReaderSlice2026.md)
· [Saved directory ownership](../../../../Gotchas/Conversion/Solidworks/Archive/Properties/SavedDirectoryOwnsPartText.md)
· [Legacy empty manager](../../../../Gotchas/Conversion/Solidworks/Archive/Properties/LegacyEmptyTextManagers.md)
· [Binary-only manager](../../../../Gotchas/Conversion/Solidworks/Archive/Properties/PropertyManagerCanStandAlone.md)
· [Neutral snapshot provenance](../../../../Gotchas/Conversion/Solidworks/Archive/Properties/JsonRetainsPropertyStatus.md)
