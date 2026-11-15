# Decoded curves are per-edge tessellation approximations, not the B-rep curve table

## Expectation

The reader recovers each edge's curve, so the writer can re-emit the vendor's curve records and a
decoded part transcodes back to nearly the same bytes.

## Actual behavior

The surface records do transcode 1:1 by count, and the curve records do not. Comparing a vendor part
with the writer's output for the same decoded model:

```
Copper_Washer  faces 6  edges 180 | main 1680 -> 2773 | surf 720  -> 2919
  vendor records  {50: 2, 51: 4, 54: 4,   55: 8}
  written records {50: 2, 51: 4, 54: 180, 55: 0}

Washer_8       faces 6  edges 188 | main 2202 -> 3090 | surf 666  -> 3133
  vendor records  {50: 2, 51: 4, 54: 4,   55: 5}
  written records {50: 2, 51: 4, 54: 188, 55: 0}

Nut_M6         faces 27 edges 451 | main 6121 -> 7915 | surf 3057 -> 8338
  vendor records  {50: 11, 51: 8, 52: 6, 54: 20,  55: 25,  56: 2}
  written records {50: 11, 51: 8, 52: 6, 54: 451, 55: 0, 56: 2}
```

`50`, `51`, `52`, and `56` (plane, cylinder, cone, torus carriers) match exactly. The divergence is
entirely `54` and `55`: the writer emits one curve record per decoded edge and no circle record at
all, while the vendor emits a small `54` table plus a `55` circle table.

Deduplicating by geometry does not close the gap either. Counting distinct curve keys in the decoded
model against the vendor's record counts:

```
part           distinct lines   vendor 54   distinct circles   vendor 55
Copper_Washer        80             4              3              8
Washer_8             67             4              4              5
Nut_M6              219            20              9             25
```

so the decoded curves are one-per-edge tessellation approximations of the loop polylines, not the
structural curves the vendor stores. `Model.curves` has exactly one entry per edge (`180` curves for
`180` edges on the washer), which is the flat-edge table the reader builds from the polyline rows,
and `re/catia/tooling/Transcode.py` prints the comparison.

## Workaround

Do not try to recover the vendor curve table by deduplicating the decoded one, and do not read the
`surf` size growth as a bug in `PackSurf`: the surface records are already correct by count. The
curve table is a real, separate gap, and closing it needs the stored per-edge curve records, which
are the same `PCurve` records the pooled surface map needs.

## Evidence

- `re/catia/tooling/Transcode.py`
- `Documentation/Gotchas/Conversion/Catia/CatiaPooledSurfaceMapIsInferred.md`
- `Documentation/Changes/Catia/CatiaNativeBrep.md`
