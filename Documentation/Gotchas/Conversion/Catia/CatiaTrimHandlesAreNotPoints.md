# CATIA trim handles are not tessellation point indices

## Expectation

A trim record's handles are indices into the tessellation point table, so `points[handle]` gives the
vertex position and the face boundary can be built directly.

## Observed behavior

The handle space is larger than the B-rep vertex table in every part, and the ratio is not constant.

| Part | Handles | B-rep vertices |
| --- | ---: | ---: |
| `Reservoir` | 1431 | 88 |
| `Copper_Washer` | 76 | 8 |
| `Washer_5` | 58 | 8 |

`Copper_Washer` shows the structure. Face 0 is a triangle strip whose handles alternate between the
two halves of the handle space: `0, 38, 2, 40, 4, 42, 7, 45, ...`. The offset is 38, the point
count, so the handle space is two parallel loops and the strip joins them.

The handles are corners, not points. Counting the faces that use each handle gives 4 handles used by
3 faces (the vertices), 68 used by 2 faces (edge interiors), and 4 used by 1 face. So a handle is a
corner on an edge, and the same geometric point can carry several handles.

A direct `points[handle]` mapping is therefore wrong. It produces a structurally valid model, which
passes referential validation, but the geometry is not the file's geometry. A planar face's points
are not coplanar under that mapping: `Copper_Washer` face 2 has a maximum plane deviation of 1.0
units against a trim vector of `(-1, 0, 0)`.

## Workaround

Do not treat the decoded vertex positions as the file's geometry. The reader places each handle by
the corner structure: arity-2 handles get distinct vertex-table points by a bipartite match, 2-face
handles are spread at equal angles along the intersection arc of their two faces (plane-cylinder, and
plane-cone when the plane is perpendicular to the cone axis), and 1-face handles take the nearest
satisfying vertex. That makes the planar faces coplanar for the simple parts (deviation drops from
1.0-34.5 to 0.0-0.0015), puts all 76 `Copper_Washer` vertices on the washer's circles, and leaves all
4682 handles across the 22 decoded parts satisfying every surface of the faces that use them. The
angular positions are still assumed equal-spaced, not the stored tessellation. Recovering the real
positions needs the per-face loop split and the record markers in the point
table.

## Evidence

- `re/catia/Brep.md`
- `re/catia/Tessellation.md`
- `src/convert/adapters/catia/NativeBrep.py`
