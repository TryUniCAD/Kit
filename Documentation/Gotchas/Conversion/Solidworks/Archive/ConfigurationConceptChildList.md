# Configuration concept serializers can have no list payload

An inherited serializer entry does not imply that its record always contains the inherited payload. In SOLIDWORKS 2026, the configuration vtable points to `moConcept_c::SerializeResolvedData`, but this method serializes its child list only when native member `+0x60` is nonnull.

The default configuration constructor at `sldmodu.dll!0x4b8c4c00` calls base constructor `0x4bdbdd40`, then feature constructor `0x4bb38350` with child-list argument 0. Concept constructor `0x4bda5770` clears `+0x60` at `0x4bda579f` and skips allocation through the zero-argument branch at `0x4bda57bf`. The serializer reads the pointer at `0x4c17b5a1` and skips the null store case at `0x4c17b5b0`; its reader also checks the pointer.

Adding an unconditional inherited list to the configuration grammar caused both training CMgr streams to fail at byte 297, and blocked resolved-feature parsing through their CMgr context dependency. Use a configuration handler with no resolved-list bytes while retaining the actual model and feature list handlers. Follow constructor operands and serializer predicates together. The [assembly finding](../../../../../re/solidworks/records/AssemblyArchive2026.md) records the module hash and exact remote failure. The correction still requires current-head remote verification.
