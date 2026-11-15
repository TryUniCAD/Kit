# Assembly archive condition bits are explicit mutations

A context-manager implementation can save an archive flag mask, add a bit for a nested record, and restore the previous mask afterward. That does not reproduce the native config-object serializer's flag operations.

In SOLIDWORKS 2026 `sldmodu.dll!0x4c21dfc0`, the final embedded list at member `+0xd0` is serialized between `addCondition(0x200)` and `removeCondition(0x200)`. The latter clears the bit; the caller does not save and restore a prior mask. Other condition changes made by nested serializers must also remain visible.

Follow the actual add/remove dataflow: OR the named bit before the nested record and clear that bit afterward. Do not substitute general stack semantics for the recovered operations. The [assembly grammar finding](../../../../re/solidworks/records/AssemblyArchive2026.md) binds this evidence to the exact binary hash. This is static native evidence, not a recorded execution trace.
