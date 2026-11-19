# Plain drawing note position ownership

PR #121 records the exact registered ordinary-note placement route. Both `IAnnotation.GetPosition` and `INote.GetTextPoint2` resolve the actual display point through its cached attachment, frame, direction and distance. The separately stored text `f38` point is retained and is not substituted for that getter.

The [source ledger](../../../../../../re/solidworks/records/DrawingPlainNotePositionOwners2026.md) maps the selected `SetPosition2` translation route and actual norm-to-`f630` store. Its [receipt](../../../../../../re/solidworks/measurements/2026/DrawingPlainNotePositionSource01.json) binds two original modules, 22 complete functions, 14 decoded instruction ranges and four disclosed typed source comparisons. It preserves both generated wrong-position diagnostics with healthy controls as failures.

This is source knowledge only: no SDK behavior or public admission changes, and no new native or held-out qualification. General attached, stacked, mirrored and annotation-view branches remain outside this selected construction. See the [cache ownership gotcha](../../../../../Gotchas/Conversion/Solidworks/Archive/Drawings/Notes/NoteApiPositionUsesDisplayCache.md).
