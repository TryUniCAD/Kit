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

`Washer_8.CATPart` `MainDataStream` has a coordinate run at offset 223. The clean values are
washer geometry: `-7.5, 1.6, -7.133, -2.318, 1.6, 2.318, 1.6, -6.068, -4.408, 1.6, 4.408, 1.6,
-4.408, -6.068, 1.6, 6.068, 1.6, -4.2`. The bounding box is `-7.5..7.5`, matching the outer
radius, and `1.6` is the washer thickness.

The run is exactly 204 floats, `0..203`, and ends at index 203. Index 204 is `2.63e-43`, the
first value of a different denormal structure. `204 / 3 = 68`, so the run is 68 triples.

The triples are not a plain `(x, y, z)` array with a fixed z lane. Every triple contains at least
one value that is `0` or `1.6`, but the special value appears in position 0 for 16 triples, in
position 1 for 10 triples, and in position 2 for 13 triples. A stride-3 scan over all start
offsets finds no lane that is more than 52 percent special. The record is therefore not a
fixed-stride point array.

Treating the special value as z and the other two as x, y puts most points on the outer
`r = 7.5` or inner `r = 4.2` circle, but five triples are off both circles: `(2.06, -3.17)`,
`(-3.51, 3.51)`, `(-4.16, 4.16)`, `(2.76, 3.66)`, `(-1.93, 1.93)`. Swapping x and y does not
move them onto a circle. The record is therefore not a simple point list with a per-triple z.

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

The five rejected parts are exactly the parts whose surface count differs from the face count:

| Part | Surface records | Face rows |
| --- | ---: | ---: |
| `4784` | 4 | 416 |
| `4876` | 1 | 870 |
| `4876_1` | 1 | 870 |
| `Pedal_Body` | 24 | 338 |
| `Reservoir` | 56 | 71 |

The other 22 parts have one surface record per face row.

`ParseSurfaces` stops early on pooled parts because the surface records are interleaved with
three-dimensional curve records. `Reservoir` has 56 surface markers at 17, 66, 350, 423, 500,
667, 740, 789, 979, 1052, 1129, 1249, 1322, 1371, 1444, 1521, 1598, 1647, 1724, 1801, and so on
through 4418. The first two records are contiguous (17 + 49 = 66, 66 + 49 = 115), but the third
record starts at 350, so the walk from offset 17 stops after two records. The gap 115..350 holds
`ff <tag:u24le> 00 00 <floats>` records, not surface records.

The two-dimensional curve rows start at 4539 and use `60 <tag:u24le> 00 12 00 33 37`. They are
variable length (27 to 225 bytes) and end with a two-byte face-reference pair. `Reservoir` has 78
such rows. Six faces (2, 3, 4, 10, 11, 21) have no curve row; the other 65 have at least one.

The face-to-surface mapping is not identity. Checking whether surface `i` bounds contain the
centres of face `i`'s curves matches only 4 of 65 faces. Checking whether a surface contains all
of a face's curves gives either zero candidates or several, so the curve geometry alone does not
identify the surface.

`MainDataStream` has two big-endian `u16` runs of values below 56 at 19348 (48 values) and 19924
(55 values). Both have a linked-list shape: the second value of a pair often reappears as the
first value of a later pair. Neither run is a 71-entry face-to-surface table, and the values
include face indices (67, 69, 70, 71) mixed with larger indices (81, 82, 84, 87, 90, 93), so the
runs are not a pure surface-index array.

## Surface record length

The record length is not constant per kind. Two cylinder records with identical five-byte
headers in `Washer_8.CATPart` measure 73 and 70 bytes. The three-byte difference is an
unresolved trailer rule.

## Pooled mapping hypothesis test

Two hypotheses were tested against `Reservoir.CATPart` and both are false.

The two big-endian `u16` runs at 19348 and 19924 are not loop-to-face links. They are the
handle arrays of trim packets. The run at 19350 starts inside the handle region of the trim
packet at 19333 (`kind 0x42`, counts `(0, 9, 0)`, total 51). The run at 19939 starts inside the
handle region of the trim packet at 19923 (`kind 0x42`, counts `(0, 8, 0)`, total 48). The
values are tessellation handles, not face indices.

The face-outer-bound run is not per-loop. All 71 rows of `Reservoir.CATPart` are byte-identical
(`30 04 04 ff ff e1 e1 e1`), so the run carries no per-row tag and cannot distinguish faces from
loops. The run is a count, not a table.

The surface record trailer is not a record offset. The 56 trailers are monotonically increasing
(3047, 3132, 3196, ... 4543), but the bytes at those offsets in `SurfacicReps` and
`MainDataStream` are float data, not record headers. The trailer is therefore not a pointer to a
curve row, a surface record, or a face table.

The trim packets do not group into 56 faces by signature. Eleven adjacent pairs share a
signature (25/26, 28/29, 30/31, 33/34, 35/36, 38/39, 40/41, 42/43, 52/53, 54/55, 58/59), but
their handle sets differ, so the pairs are distinct loops, not the outer and inner loops of one
face. Pairing them gives 60 groups, not 56.

The corpus reader still decodes 22 of 27 parts. The five pooled parts (`4784`, `4876`,
`4876_1`, `Pedal_Body`, `Reservoir`) still fail at the surface-count check.

## Coordinate table format

The coordinate data in `MainDataStream` is a plain little-endian `f32` table, not a
`CATFloatCompactor` stream. It starts at 569 in `Reservoir.CATPart` and runs to 12376. The table
uses a five-float group:

```text
x, y1, z, y2, z
```

Each group encodes two symmetric points `(x, y1, z)` and `(x, y2, z)`. The first group is
`(-35.5, -0.5, 37.418, 0.5, 37.418)`, giving `(-35.5, -0.5, 37.418)` and
`(-35.5, 0.5, 37.418)`. The `x` values decrease from -35.5 to 60, the `y` values are small
(`±0.5`, `±0.854`, `±1.0`), and the `z` values span 33 to 60. The table has 2951 floats, or 590
groups, or 1180 points.

The table is not a single contiguous run. Denormal values such as `0xa8000000` break the run into
segments at 569 (342 floats), 1941 (128), 2649 (909), 6485 (125), 7061 (127), 7661 (128), 8249
(122), and 8953 (856). The denormals are effectively zero and do not change the group format.

The handle-to-point mapping is not identity. The trim and edge handles go up to 1430 with 1431
distinct values, but the table has only 1180 points. Mapping handle `i` to point `i` gives
scattered points for face 0 (for example handle 836 maps to `(2.461, -1.345, 12.531)` and handle
971 to `(16.674, 9.267, -17.724)`), not points on the face-0 plane at `z=0`. The table is
therefore either incomplete or indexed by a different ordering.

## Per-body and strip hypothesis test

Two more hypotheses were tested against `Reservoir.CATPart` and both are false.

The coordinate table is not per-body with the body-header tags as group indices. The three body
headers at 54, 101, and 153 carry counts 3, 19, and 4140 and tags 1/259 (bodies 1 and 2) and
767/1431/1431 (body 3). Interpreting the tags as group indices from the table start at 569 gives
a coherent group only for tag 1 (offset 589, `(-35.353, -0.854, 37.42, 0.854, 37.42)`). Tag 259
(offset 5749) is misaligned (`(16.231, -4.653, 15.858, 16.146, -4.636)`, `z1 != z2`), and tags 767
and 1431 land on denormals. Interpreting the tags as float offsets or byte offsets also fails.

The five-float groups are not strips with implicit interior points. Each group is exactly two
points `(x, y1, z)` and `(x, y2, z)`, and the `z` values are equal within a group. The table has
about 1206 points across all float runs, but the trim and edge handles go to 1430 with 1431
distinct values, so about 224 points are missing.

The coordinate data is split across many float runs, not one table: 569 (342 floats), 1941 (128),
2457 (47), 2649 (909), 6289 (37), 6441 (10), 6485 (125), 6989 (17), 7061 (127), 7573 (21), 7661
(128), 8177 (17), 8249 (122), 8741 (13), 8797 (38), 8953 (856), plus smaller runs after 12586.
The total is 3016 floats.

## Open work

1. Locate the shared tessellation vertex table and its coordinate encoding.
2. Decode the tessellation-to-B-rep edge linkage.
3. Decode the face-to-surface reference for shared surface pools.
4. Resolve the surface record trailer rule.

## Evidence

- `re/catia/tooling/ParseBrep.py`
- `src/convert/adapters/catia/NativeTopology.py`
- `src/convert/adapters/catia/NativeBrep.py`
