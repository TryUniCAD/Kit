# CATIA trim handles are tessellation indices

## Finding

The handles inside a `MainDataStream` trim packet are not B-rep vertex identifiers.
They are dense indices into a shared tessellation vertex table.

Evidence from the corpus:

| Part | B-rep vertices | Trim handles | Dense `0..N-1` |
| --- | ---: | ---: | --- |
| `Washer_8.CATPart` | 8 | 94 | yes |
| `Bolt_M5x40.CATPart` | 28 | 174 | yes |
| `Pedal_Body.CATPart` | 424 | 2666 | yes |

A washer with eight B-rep vertices has ninety-four distinct trim handles.
The handle set is exactly `0..93`, so the handles index a table of ninety-four entries.
That table is not the `01 06` vertex table, which has eight rows.

## Consequence

The trim packet is an indexed triangle mesh that tessellates the face.
Its boundary cycles approximate the B-rep loops but are not the B-rep loops.
Mapping a tessellation boundary to a native B-rep edge requires a linkage that is not yet decoded.

The current reader derives loops from the tessellation boundary and maps handles modulo the
B-rep vertex count. That produces a valid neutral model for simple parts, but it is a derived
approximation, not the native topology.

## Edge rows are polylines

The edge table rows are not two-endpoint edges. Each row is `02 <arity> <handle[arity]>`, and
`arity` is the number of tessellation points along the edge. `Washer_8.CATPart` has arities
`11, 11, 11, 11, 14, 14, 9, 14` and a handle sum of 103.

Edge handles and trim handles share one global point-id space but are not identical sets:

| Part | Edge handles | Trim handles | Same set |
| --- | ---: | ---: | --- |
| `Washer_8.CATPart` | 93 | 94 | no |
| `Bolt_M5x40.CATPart` | 130 | 174 | no |
| `Pedal_Body.CATPart` | 1698 | 2666 | no |

The trim mesh adds interior points that no edge polyline uses. The coordinate table for this
shared point-id space is not yet located.

## Washer coordinate run

`Washer_8.CATPart` `MainDataStream` has a 318-float run at offset 223. The clean values are
washer geometry: `-7.5, 1.6, -7.133, -2.318, 1.6, 2.318, 1.6, -6.068, -4.408, 1.6, 4.408, 1.6,
-4.408, -6.068, 1.6, 6.068, 1.6, -4.2`. The bounding box is `-7.5..7.5`, matching the outer
radius, and `1.6` is the washer thickness.

Only 148 of the 318 floats are clean; the rest are denormals (`1.7e-15`, `2.8e-14`, `-1.5e-9`).
The clean values sit at offsets with gaps of 4, 8, 12, and 16 bytes, so the record is not a plain
`(x, y, z)` float array. `318 / 3 = 106` is an integer, which is suggestive but contradicted by
the denormals.

The same pattern holds for `Bolt_M5x40.CATPart` (390 floats at 243, `390 / 3 = 130`) and
`Reservoir.CATPart` (2959 floats at 565, not divisible by 3).

## Coordinate run in the head

`Pedal_Body.CATPart` `MainDataStream` contains a long run of plausible little-endian `f32`
values starting at offset 874. The run is 4193 floats and ends at 17646. The first values are
`0, -9, -10, 0, 173, -2.121, 173, -1.8614, 171.9831, ...`, which are clearly 3D coordinates.

Immediately before the run, at offset 874, is a little-endian `u64` count of `4186`. The count
does not divide evenly into three, so the record is not a plain `(x, y, z)` triple array of that
length. The run also spans all three axes over the same range (`-10` to `202.56`), which is
unusual for a flat part.

The run is therefore a real coordinate block, but its record structure (point count, stride, and
whether it is a mesh, a curve, or a parameter array) is unresolved.

## Coordinate table search

The `MainDataStream` head region before the trim chain (bytes `0..1472` in `Washer_8.CATPart`) is
not a plain `f32` coordinate table. The longest run of plausible `f32` values is 106 floats at
offset 1036, and those values are almost all zero. The `30 04 04 fd ff` record appears only three
times, so it is not a repeated point table.

The `SurfacicReps` tail after the curve rows is 56 bytes, too small for 94 points. The coordinate
table is therefore compressed or stored in a stream that is not yet identified. This is the same
`CATFloatCompactor` blocker recorded in `FloatCompactor.md`.

## Face-to-surface reference search

The face-to-surface reference is not in the face-outer-bound run. The `30 04 04 ff ff` record
count equals the face count (washer 6, bolt 22, pedal 338, reservoir 71), and its payload is
constant. The `30 04 04 fd ff` record appears exactly three times in every part, so it is not a
per-face table.

The trim packet carries no surface index: its fields are the kind mask, counts, total, optional
vector, lengths, and handles. The edge rows carry only arity and handles. The reference is
therefore in a table that is not yet identified.

## Surface pool

Surfaces are also shared. `Pedal_Body.CATPart` has 24 surface records and 338 faces.
The face-to-surface reference is not decoded, so the reader rejects parts whose surface count
does not equal the face count instead of returning a partial solid.

## Surface record length

The record length is not constant per kind. Two cylinder records with identical five-byte
headers in `Washer_8.CATPart` measure 73 and 70 bytes. The three-byte difference is an
unresolved trailer rule.

## Open work

1. Locate the shared tessellation vertex table and its coordinate encoding.
2. Decode the tessellation-to-B-rep edge linkage.
3. Decode the face-to-surface reference for shared surface pools.
4. Resolve the surface record trailer rule.

## Evidence

- `re/catia/tooling/ParseBrep.py`
- `src/convert/adapters/catia/NativeTopology.py`
- `src/convert/adapters/catia/NativeBrep.py`
