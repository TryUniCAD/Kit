# SOLIDWORKS 2026 assembly archive codec

The research archive codec now registers typed 2026 assembly, configuration, component reference, component history/favorite, live-section folder, mate, browser-cache, and mass-cache records. Assembly sections reuse the existing model serializer and class map. Counted records retain their order and object links; section lengths and collection lengths derive from the typed graph.

Use `re/tooling/sw2026/serial/RoundTrip.py` with an assembly glob and explicit stream names in remote CI. `tests/convert/solidworks/research/AssemblyRoundTests.py` invokes that command as a subprocess and requires identical output with no unread tail for 14 streams across the two committed assembly parser controls.

The [field and evidence finding](../../../re/solidworks/records/AssemblyArchive2026.md) records native module hashes, serializer addresses, field order, variable record boundaries, and unresolved branches. [Decompiler type ownership](../../Gotchas/Conversion/Solidworks/AssemblyDecompilerTypes.md) explains why inferred parameter types cannot identify the registered class by themselves.

[Condition-bit mutations](../../Gotchas/Conversion/Solidworks/AssemblyConditionBits.md) records the native add/remove sequence used by a config-object list; it clears the named bit rather than restoring a previous mask.

[Configuration child lists](../../Gotchas/Conversion/Solidworks/Archive/ConfigurationConceptChildList.md) records the constructor predicate behind a fieldless resolved dispatch. The second remote run passed 12 of 14 streams, including exact CMgr reproduction for both controls. Resolved features now reach a missing component-history record; its native node-base and pointer grammar is recovered, with a read-only archive context guard.

[History component read context](../../Gotchas/Conversion/Solidworks/Archive/HistoryComponentReadContext.md) explains why the history pointer changes archive state during reading without adding a flag to the wire or mutating the writer context.

The fourth remote run passes the entire 14-stream process check, including resolved features after the component-history and live-section folder repairs. The folder schema includes its constructor-proven concept child list and an i32 normalization witness for a native byte flag. The same whole smoke job remains red for two unrelated signature-table checks that expected a removed licensed binary; the clean-main dependency repair is included in the next revision.

This is a source-document research codec. It supplies no fresh assembly builder, no donor defaults, and no target-application acceptance claim. It rejects unsupported versions, unregistered classes, and identified unknown branches. Local checks were limited to static AST, formatting, and rationale validation. Queue acceptance and vendor load/rebuild/mate-edit measurements remain unproven.
