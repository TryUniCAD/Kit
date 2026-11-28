# Assembly manager child lists set a temporary condition

The SOLIDWORKS 2026 SP05.2 `moConfigObject_c.fd0` owner writes a list inside the temporary archive condition `0x200`. The condition is set for that owner and cleared afterward. A branch that only checks whether the incoming condition is already set omitted two bytes for each empty list in the disclosed assemblies.

Use the ordered `Context` set, list emission and `Context` clear. Configuration and ResolvedFeatures byte identity did not detect the omitted lists. Compare the independently rooted CMgr stream and the complete file as well. [Exact public route evidence](../../../../../../re/solidworks/records/NestedAssemblyDelivery2026.md)
