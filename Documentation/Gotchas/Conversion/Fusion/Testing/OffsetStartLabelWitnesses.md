# Offset-start caps do not necessarily coincide with sketch sheets

A label corruption fixture for a profile-plane extrusion can select a solid cap and sketch sheet at the same station.
That assumption fails for the offset-start control: its sketch is at zero while the solid caps are at -22 and 24 millimeters.
The original helper therefore rejected the fixture before the public reader was exercised.

Select an untagged sketch sheet and a separately tagged solid face without requiring coincident stations.
Move the attribute and its reciprocal owner links together, then emit the archive and require the public reader to refuse it.
The task-local `MakeOffsetLabel` fixture does this without changing shared reader or worker behavior.

The [qualification package](../../../../../re/Fusion/OffsetAdmission20261127/README.md) retains the initial failed integration attempt and repaired checks.
