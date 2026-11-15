# BRep live topology is resolved through the journal boards

## Problem

A BRep journal is a history, not a snapshot. Counting every entity in it overcounts, because the
journal keeps the topology from before a feature as well as after it.

`shell_both.f3d` carries 3 `DeltaState` records and 266 entities for an `ActiveCount` of 195. A count
over every entity reports 17 faces, 36 edges and 24 vertices, while Fusion reports 11 faces, 24 edges
and 16 vertices for the same file.

## Change

`ResolveLive` walks the journal states in order and applies each bulletin change:

| Change        | Effect                    |
| ------------- | ------------------------- |
| `OldRef != -1` | remove that entity       |
| `NewRef != -1` | add that entity          |
| `NewRef == -1` | the entity is deleted    |

The result is the set of live entity indices, which is what Fusion reports.

## Behavior

| File | Resolved | Fusion | Match |
| ---- | -------- | ------ | ----- |
| `mirror_xy.f3d` | 12 face, 24 edge, 16 vertex, 2 body | 2 bodies of 6, 12, 8 | yes |
| `analytic.f3d` | 4 face, 2 edge, 2 vertex, 3 body | sphere 1/0/0, torus 1/0/0, cone 2/2/2 | yes |
| `shell_both.f3d` | 11 face, 24 edge, 16 vertex, 1 body | 1 body of 11, 24, 16 | yes |

`shell_both` resolves to 222 live entities, which is the 195 `ActiveCount` plus the entities the
boards create after it.

## Verification

The three files were opened in local Fusion 2706.1.17 with `ProbeBrep.py`, which imports the F3D and
reports each body's face, edge and vertex counts. The resolved counts match all three.

Across the corpus, 500 designs resolve through the boards and 39 do not, because their body history is
a `PrismHistory` wrapping a `HistoryState` rather than a journal. That is a different representation
and this change does not cover it.

## Limits

`ResolveLive` returns the live entity indices. It does not rebuild the topology graph, so a caller
still has to read the entity records to know what each index is.

The 39 prism-history designs are not resolved. A caller that needs their topology has to read the
prism model instead.
