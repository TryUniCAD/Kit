# Read compatible SOLIDWORKS part text

The normal `open_document` part reader exposes authored summary text in
`metadata["document_summary"]`, file-level custom text in
`metadata["custom_properties"]`, and configuration custom text in the
active configuration's `attributes["custom_properties"]`.

This profile covers ordinary version-19000 parts. The configuration
property stream must identify the active, unparented configuration in the
saved directory. Before exposing any literal properties, the reader
binds the native ModelHeader and consumes the complete ordinary Config-0
archive, including both typed sections and their owner references.
The supported binary property manager is absent or empty. A manager is
checked even when it is the sole property owner. Name dictionaries, raw
and evaluated text and reserved section fields must agree. Unsupported
or malformed scopes withhold all property bags and provide an information
diagnostic. The ordinary model read remains available. The registry
refuses new native projections and direct writes when the root or an
owned component document has this status. The error retains the first
unavailable property's original cause. The registered interchange JSON
reader and writer can preserve an eligible neutral snapshot and its native
inspection status when configuration and geometry filtering are disabled.
The ordinary model portability checks also apply to snapshot copies.

The version-18000 compatibility path verifies absence of authored text
through the complete supported binary property owner and all recognized
text scopes. Empty scopes add no property-specific restriction.
Authored text or an unsupported owner produces the same property
write refusal. Strict inspection preserves the model. The legacy
wheel control still encounters its separate sketch support refusal
when it crosses the export boundary.

Check `metadata["solidworks.part_text_properties"]["status"]` for
`complete` before relying on the text. The reader leaves files without
these property streams on their previous path. It preserves separate
file and configuration values even when they share a name.

Three disclosed native files match the independently observed property
values through the public reader. The advanced property control keeps
its B-rep and native feature tree while withholding all property scopes.
Two generated files retain their existing modeling refusals and pass
separate typed property checks.
The physical configuration case checks a one-byte stream, a missing
tail, appended data and a different mapped owner. Each keeps the model
readable, withholds all text and refuses conversion and direct writing
before changing the destination. The summary-only truncation control
applies the same rule without scoped custom XML. A distinct neutral
snapshot with an authored prism proves exact JSON copies through both
SDK entry points. The circular native control retains its full inspection
document in JSON and still encounters the native-only feature gate on
direct export.

[SDK evidence](../../../../../re/solidworks/records/LiteralPartTextReaderSlice2026.md)
· [Saved directory ownership](../../../../Gotchas/Conversion/Solidworks/Archive/Properties/SavedDirectoryOwnsPartText.md)
· [Legacy empty manager](../../../../Gotchas/Conversion/Solidworks/Archive/Properties/LegacyEmptyTextManagers.md)
· [Binary-only manager](../../../../Gotchas/Conversion/Solidworks/Archive/Properties/PropertyManagerCanStandAlone.md)
· [Neutral snapshot provenance](../../../../Gotchas/Conversion/Solidworks/Archive/Properties/JsonRetainsPropertyStatus.md)
