# Ordinary SOLIDWORKS assembly Definition codec

The SDK archive codec reads and emits the version-19000 assembly Definition.
Call `ReadModelDef(data, 19000, Assembly=True)` to inspect the complete stream.
Use `MakeAssemblyDef(settings, preferences)` and
`WriteModelDef(graph, Assembly=True)` to construct a stream from explicit
presentation settings and all ten native save-as-part preferences. The part
codec remains the default selection.

Eight hash-pinned disclosed assemblies replay three distinct Definition
streams exactly. Two fresh, guarded construction cases reproduce the
independent reference encoding, including both bounds of the native threshold
clamp. The guarded process proof also exercises an authored saved-style
empty renderer and refuses the alternate renderer words. Sixteen invalid
input and stream cases refuse. This change supplies
the internal Definition stream. Public assembly writing and native
qualification of whole generated documents have separate exits.
[Evidence and rerun commands](../../../../../re/solidworks/records/OrdinaryAssemblyDefinition2026.md)
