# CATIA trim handles are not tessellation point indices

## Expectation

A trim record's handles are indices into the tessellation point table, so `points[handle]` gives the
vertex position and the face boundary can be built directly.

## Observed behavior

The handle space is larger than the point table in every part, and the ratio is not constant.

| Part | Handles | Points |
| --- | ---: | ---: |
| `Reservoir` | 1431 | 1000 |
| `Copper_Washer` | 76 | 38 |
| `Washer_5` | 58 | 58 |

`Copper_Washer` shows the structure. Face 0 is a triangle strip whose handles alternate between the
two halves of the handle space: `0, 38, 2, 40, 4, 42, 7, 45, ...`. The offset is 38, the point
count, so the handle space is two parallel loops and the strip joins them.

The point table is also not a plain triple array. `Copper_Washer` has a 116-float run at `226`, a
2-byte gap, then a 74-float run at `692`. `Reservoir` has twelve float runs between `569` and
`12377` separated by 4- and 8-byte gaps. The gaps are record markers, and the second loop of a face
is stored separately from the first.

A direct `points[handle]` mapping is therefore wrong. It produces a structurally valid model, which
passes referential validation, but the geometry is not the file's geometry. A planar face's points
are not coplanar under that mapping: `Copper_Washer` face 2 has a maximum plane deviation of 9.5
units against a trim vector of `(-1, 0, 0)`.

## Workaround

Do not treat the decoded vertex positions as the file's geometry. The current reader uses a
placeholder handle-to-vertex rule and documents the result as a structural approximation. Recovering
the real positions needs the per-face loop split and the record markers in the point table.

## Evidence

- `re/catia/Brep.md`
- `re/catia/Tessellation.md`
- `src/convert/adapters/catia/NativeBrep.py`
