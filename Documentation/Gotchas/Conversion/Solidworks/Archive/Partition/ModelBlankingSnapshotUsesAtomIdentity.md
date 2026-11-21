# Model blanking snapshots use atom identity

The persisted snapshot can be initialized even when its entry count is
zero. Four ordinary SOLIDWORKS 2026 part saves use this state. Two
synchronized assembly children retain a row for their visible solid.
That row has a false blanking value and points to the same archive atom
as the part's atom manager.

When the modeled operation captures the blanking state, resolve each live
body's existing atom first. Reuse that object as the map key and obtain
the value through its local visibility state. The ordinary null-context
accessor reads `moAtom.f170`. Keep initialization and entry count separate.

[Snapshot constructor and archive evidence](../../../../../../re/solidworks/records/GeneratedRectanglePartition2026.md#standalone-archive-attachment)
