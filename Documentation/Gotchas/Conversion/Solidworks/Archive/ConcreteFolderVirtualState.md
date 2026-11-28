# A concrete folder can share fields and differ in virtual state

The SOLIDWORKS 2026 SP04.1 plain `moFtrFolder_c` and its Notes counterpart share serializer RVA `0x10e1860`. The concrete callback at vtable slot `0xa40` differs. The plain class returns false at RVA `0x13cc10` and the Notes class returns true at RVA `0x13e180`.

Applying the Notes result to the plain folder advances the cursor into a false pointer at byte 1790 of the cover witness. Resolve the four concept virtuals on the actual class and retain the concrete false result for the plain folder. Both disclosed legacy tutorials reproduce the complete folder payload and map with that dispatch. [Pinned loader and replay evidence](../../../../../re/solidworks/records/SheetMetalLegacyLinked2026.md)
