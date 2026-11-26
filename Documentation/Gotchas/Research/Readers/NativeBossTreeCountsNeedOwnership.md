# Native boss tree views need explicit ownership

## Expectation

A top-level native feature count can appear directly comparable with the SDK timeline count.

## Observed behavior

The c4 discovery controls have 19 API top-level rows and 26 SDK rows.
The recursive Discovery01 observations have 26 occurrences but 25 distinct native IDs.
Sketch1 appears both at top level and beneath its boss.
The recursive view identifies two Notes children and four Lights and Cameras children.
The SDK's Exploded Views row remains absent from that view.

## Workaround

Compare presence, native IDs, types and parent edges separately.
Preserve repeated traversal occurrences.
Do not infer a missing feature, a safe row deletion or a native type alias from counts or names alone.
Keep unresolved ownership as an admission gap.

See the [hash-bound comparison evidence](../../../../re/solidworks/NativeBossProof/Findings.md).
