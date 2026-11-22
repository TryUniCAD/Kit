# SOLIDWORKS History and Biography stream codec

Use `ReadHistMut` and `WriteHistGraph` for the standalone
version-19000 History and Biography streams. Each stream uses
its own archive map. Biography preserves ordered embedded
telemetry. Version-history entries use the existing header stamp
layout and link to their date-code history object. The writer returns an
independent graph read from the emitted buffer so its offsets describe
the returned bytes.

Fresh construction supplies an empty Biography and one version
state with a nonempty date-code history. Supply the creation event,
comment, build, license and language provenance through
`HistoryInput`. Wrong owners, missing states, unsupported versions
and unfinished stream data raise errors.

Two disclosed SOLIDWORKS 2026 saves and a generated part with
native lifecycle evidence supply six exact stream comparisons.
Two authored history inputs and a shared-date case match separate
wire constructions, with twelve refusals observed. An independently
framed Unicode comment edit shifts the emitted root and date-code
spans while keeping the source coordinates. Deleting an earlier state
reassigns the surviving date-code object in the emitted map. Both
pre-writer locked SOLIDWORKS originals reproduce their four History and
Biography streams with zero runtime input reads. This internal codec
is a prerequisite for complete part writing. The current queue run remains
pending. [Held-out stream comparison](../../../../../re/solidworks/measurements/2026/HistoryStreamHeldout01.json)
[Source and process evidence](../../../../../re/solidworks/records/HistoryStreamSlice2026.md)
· [History count gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Metadata/HistoryNeedsFinalStates.md)
· [History output offsets](../../../../Gotchas/Conversion/Solidworks/Archive/Metadata/HistoryWriteUsesOutputOffsets.md)
