# FreeCAD local sketch expression links

The native reader links a saved Pad length expression to the existing driving dimension of its actual profile sketch. The supported form divides a named sketch constraint by a positive integer. The reader checks the actual object name, unique active constraint, persisted values and matching physical quantity before publishing the link. It keeps the original expression text, parameter IDs, cached values and units.

Use the normal strict FCStd read. References with unsupported syntax, ambiguous ownership or stale caches remain unresolved with source data retained. The same binding runs before the native replay digest.

Six guarded original-path reads compare three disclosed FCStd files before and after the change. Each source remains immutable and gains the one verified dependency. [Method and scope](../../../re/solidworks/records/FreecadLocalSketchExpr2026.md) · [Process receipt](../../../re/solidworks/measurements/2026/FreecadLocalSketchExpr01.json)
