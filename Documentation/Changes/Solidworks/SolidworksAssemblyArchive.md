# SOLIDWORKS 2026 assembly archive codec

The research archive codec now registers typed 2026 assembly, configuration, component reference, mate, browser-cache, and mass-cache records. Assembly sections reuse the existing model serializer and class map. Counted records retain their order and object links; section lengths and collection lengths derive from the typed graph.

Use `re/tooling/sw2026/serial/RoundTrip.py` with an assembly glob and explicit stream names in remote CI. `tests/convert/solidworks/research/AssemblyRoundTests.py` invokes that command as a subprocess and requires identical output with no unread tail for 14 streams across the two committed assembly parser controls.

The [field and evidence finding](../../../re/solidworks/records/AssemblyArchive2026.md) records native module hashes, serializer addresses, field order, variable record boundaries, and unresolved branches. [Decompiler type ownership](../../Gotchas/Conversion/Solidworks/AssemblyDecompilerTypes.md) explains why inferred parameter types cannot identify the registered class by themselves.

[Condition-bit mutations](../../Gotchas/Conversion/Solidworks/AssemblyConditionBits.md) records the native add/remove sequence used by a config-object list; it clears the named bit rather than restoring a previous mask.

[Configuration child lists](../../Gotchas/Conversion/Solidworks/Archive/ConfigurationConceptChildList.md) records the constructor predicate behind a fieldless resolved dispatch. The first remote run passed 10 of 14 streams; both CMgr failures blocked their resolved-feature context reads. The predicate correction awaits current-head CI.

This is a source-document research codec. It supplies no fresh assembly builder, no donor defaults, and no target-application acceptance claim. It rejects unsupported versions, unregistered classes, and identified unknown branches. Remote byte-identity verification is pending; only AST parsing and formatting checks were performed locally. Queue acceptance and vendor load/rebuild/mate-edit measurements remain unproven.
