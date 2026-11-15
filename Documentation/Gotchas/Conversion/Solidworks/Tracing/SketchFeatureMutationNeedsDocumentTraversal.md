# Sketch feature mutation needs document traversal

## Expectation

Querying an active sketch for `IFeature` could appear sufficient to rename and select its owning history feature.

## Observed behavior

Both 2026 source controls accepted the explicit `IFeature` query.
Their subsequent name assignment failed with `Unable to write read-only property`.
The line and arc interface operations had already passed those earlier binding boundaries.
The interface query alone did not establish a mutable history-feature dispatch object.

## Workaround

Traverse the new part's features with `FirstFeature` and `GetNextFeature`.
The curve authoring tool requires exactly one `ProfileFeature` in its otherwise empty new part.
It requires that feature to return a nonnull specific sketch interface.
Then name and select the history feature directly.
Do not assume a fixed feature position.

This restriction belongs to the controlled new-part authoring sequence.
It does not establish a lookup policy for arbitrary existing documents or templates containing additional sketches.
Native verification of the corrected lookup remains pending.
