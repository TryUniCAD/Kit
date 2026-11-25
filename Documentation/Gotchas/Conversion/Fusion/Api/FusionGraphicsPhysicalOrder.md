# Fusion graphics order matches saved BRep record order

## Expectation

A native archive with an equal decoded BRep and scene model also preserves the relationship between stored graphics node order and body record order.

## Actual behavior

Eight Fusion-saved cuboids enumerate graphics edges and faces in the same order as their physical geometry records. Kit's canonical history serializer rearranges those records while the stored graphics order stays the same. All eight re-read as equal typed models. The runtime significance of that physical association remains unmeasured.

## Workaround

Compare graphic bounds and body references by geometric role. Isolate a history rewrite from snapshot and material rewrites in the native experiment. Check viewport picking and appearance before rebuild, when the application can still be using the saved display state. See the [display association evidence](../../../../../re/Fusion/SavedCuboidWriter/DisplayHeightEvidence.md).
