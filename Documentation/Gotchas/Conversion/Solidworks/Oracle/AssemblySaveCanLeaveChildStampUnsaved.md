# A parent save can leave the loaded child update stamp unsaved

A successful parent save can preserve references to a child's updated state
in memory while the child file still contains its earlier state. This can
return warning 32 on fresh assembly open even when the resolved child's own
rebuild flag is clear.

In the [controlled comparison](../../../../../re/solidworks/measurements/2026/AssemblyChildSaveProbe01.json),
both native assemblies had the same child geometry and in-memory update stamp
134. A parent-only save left the child file untouched; it reopened at stamp
120 and the assembly required a rebuild. Explicitly saving the isolated
child before its parent preserved stamp 134 and the assembly reopened without
a warning. Both controls passed. Save only explicitly owned child copies in
oracle experiments. This establishes the intervention for the measured case,
not a complete native warning predicate or a writer field formula.
