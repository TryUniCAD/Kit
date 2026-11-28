# Edge primary fin can change before reference creation

## Expectation

An ordinary edge reference always takes its left/right/start/end roles from the serialized `EDGE.halfedge`.

## Actual behavior

The no-argument native `gcEdge_w::coEdge` obtains the first live fin, then can replace it with its next-of-edge mate before the reference constructor assigns roles. For an ordinary normal curved edge it calls `PK_FIN_is_positive`, which compares `HALFEDGE.sense` with `+`. A negative first fin selects the mate. Neither curve class 30 versus 31 nor downstream/portable indices are tested by this branch.

The kernel field registration binds `EDGE.halfedge` to runtime `+0x50`, `HALFEDGE.other` to `+0x30` and `HALFEDGE.sense` to `+0x60`. Backend topology type 1 is laminar and skips the direction test. Missing curves, mixed categories, wire/nonmanifold and special representation branches remain separate.

## Workaround

For the proved classic normal profile with exactly two live loop-owned opposite-sense fins and a nonnull actual curve, select the unique `+` fin and derive roles from it. Admit line/circle classes only when those actual topology/curve predicates hold. Reject unsupported branches rather than match numeric indices or assume the primary is already positive.

[The construction record](../../../../../../re/solidworks/records/DownstreamFreshReferenceAssignments2026.md) and [source-only verification](../../../../../../re/solidworks/measurements/2026/DownstreamFreshReferenceSource01.json) bind the backend choice at `0x32f92579/0x32f92585`, exact kernel predicate at `0x18031836d`, and field registration. Native orientation and acceptance measurement remain open.
