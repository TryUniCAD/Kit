# Derive ordinary reference stamps from a child model and header

The [native reference trace](../../../../../re/solidworks/records/AssemblyConstruction2026.md#reference-update-state-after-insertion)
binds the ordinary part-target reference fields to their child owners. The
[clean archive readback](../../../../../re/solidworks/measurements/2026/AssemblySyncReadbackProcesses9c0.json)
matches the update counter, timestamp and geometry-change counter for each
of three references against its actual saved child.

The research helper computes those fields from typed child model and header
objects. It requires explicit placement assignment, uses the documented
part-target literals, and refuses unsupported child kinds or invalid scalar
domains. It opens no component file. This is a logical reference-state
helper pending complete occurrence construction and measured writer output.
