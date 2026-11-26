# Allocated operations can be absent from live geometry

## Expectation

Every operation ID in a feature's reciprocal operation maps appears in the current body progenitor map and side-face tags.

## Actual behavior

The independently authored reverse cylinder in `re/Fusion/Reconstruction/CircularSpans/Controls/HeldOut/DiscFlip.f3d` assigns two operation IDs to the extrusion. Its current body progenitor map and side tag use one. The symmetric and two-sided controls use both IDs on the side face. Treating all allocated IDs as active geometry rejects the valid held-out reverse file.

## Workaround

Verify the complete forward/reverse allocation maps, then derive active geometry operations from the body progenitor occurrences. Require every active operation to belong to the owning feature and validate the physical face tags against that active sequence. Do not require unused allocations to appear on current geometry.

The [measured controls and confidence record](../../../../../re/Fusion/Reconstruction/CircularSpans/Findings.md) distinguish observed facts from remaining generalization limits.
