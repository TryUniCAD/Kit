# Fusion-saved graphics bounds can lag a cuboid edit

## Expectation

A graphics scene saved with a constrained cuboid has the same bounds as the current solid.

## Actual behavior

Fusion 2706.1.17 kept the preceding height in the aggregate solid display box for eight edited or restored saves. One file had a 28.3 mm solid in its BRep history and snapshot, with a 13.8 mm graphics Z bound. Its restored file had a 13.8 mm solid and a 28.3 mm graphics Z bound. Both saved graphs resolved their typed display references. The individual face and edge bounds matched the current solid in all eight saves.

## Workaround

Read current dimensions from the validated history, snapshot, driving parameters and solid geometry. Preserve each source's typed graphics state and validate its entity references. An independent writer needs its own measured rule for graphics regeneration after an edit.

See the [saved cuboid comparison](../../../../../re/Fusion/SavedCuboidRoundTrip/Findings.md#display-bounds-can-retain-the-previous-height).
