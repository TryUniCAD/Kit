# Embedded body layouts need explicit linkage

Reusing a field tuple containing an embedded-body reference does not import the separately keyed body layout into a sparse codec profile. The original drawing probes reached the admitted user environment, then failed with `unsupported SOLIDWORKS body schema uiSplitterInfo_c.Serialize` because that internal method key was absent.

This is a missing field-layout dependency, not a missing runtime class schema. The native environment calls the already constructed secondary splitter's serializer directly; it emits no object/class tag at that boundary.

Link the independently verified existing embedded method explicitly and retain its transform dependencies and context guards. Do not invent a runtime schema, silently use an empty body, broaden the entire shared mapping, or treat the earlier incomplete decode as a pass.

The [exact splitter evidence](../../../../../../../re/solidworks/records/DrawingSplitterBodyArchive2026.md) binds the real call context, current native body, one-entry linkage, and retained failing source reports.
