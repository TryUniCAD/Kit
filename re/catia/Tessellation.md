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

## Missing-point search

The ~224 points that separate the coordinate table (about 1206 points) from the handle range
(1431) are not in the vertex table or `SurfacicReps`.

The vertex table starts at 29773 and holds 88 vertices. The first vertices are
`(-1.199, -2.194, 0.0)`, `(1.199, 2.194, -0.0)`, `(-10.308, -18.868, 50.0)`,
`(6.233, 11.409, 15.0)`, and `(-6.233, -11.409, 15.0)`. They sit at `z=0`, `z=15`, `z=21`, and
`z=50`, which are the B-rep vertex planes, not the tessellation points. Adding 88 vertices to
1206 points gives 1294, still short of 1431.

`SurfacicReps` has no large coordinate table. Its float runs are all 10 or 11 floats (surface
carrier parameters and curve data), 605 floats in total.

The region after the coordinate table (12376..18807) is not a float table. It is a sequence of
`ff <tag:u24le>` records and offset-like values such as `9b fe`, `80 a5 04 ff`, `7d 26`, and
`dc d6`, not coordinates.

## Region 12376..18807 and mixed table format

The region 12376..18807 is not a `CATFloatCompactor` stream and not a `u16`/`u32` offset table.
Decompressing it with the compactor at references 47.2, 30.0, and 0.0 returns values close to the
reference (47.2, 47.2, 47.2, ...), not coordinates. Its `u16` values are mostly above 1431
(65346, 65179, 42368, 65284, 55004, 43439, 43596, 58089), and its `u32` values are mostly above
31156, so they are not point or byte offsets.

The coordinate table at 569..12376 is not a uniform five-float group. The first 18 groups are
`(x, y1, z, y2, z)` with `z1 == z2`, for example `(-35.5, -0.5, 37.418, 0.5, 37.418)`. The
alignment breaks at group 18 (offset 929), where the data becomes a mix of three-float triples and
five-float groups. A heuristic parser that reads a five-float group when `z1 == z2` and a
three-float triple otherwise yields 999 points, still short of the 1431 handles.

## Surface trailer is not a curve-row pointer

The three-byte surface trailer was tested as a pointer into the curve-row region and as a face
index. Both are false.

`Copper_Washer.CATPart` has six surface records with trailers 445, 449, 476, 495, 499 (the sixth
record's last three bytes are the first curve row, not a trailer). The curve rows start at 404,
431, 458, 485, 512, 539, 566, 593. No trailer equals a curve-row start, and `trailer / 8 + 404`
does not land on a curve-row start either. The trailers modulo 6 are 1, 5, 2, 3, 1, which is not
a permutation of the six face indices.

The trailer differences are 4, 27, 19, 4. The 27 matches the curve-row length, but 4 and 19 do
not, so the trailer is not a simple stride into the curve rows.

## Roster offsets are not curve-row starts

The 88-entry roster at `SurfacicReps` 7371..7987 was tested as a pointer table into the curve
rows. It is not.

`Copper_Washer.CATPart` has eight roster entries with offsets 410, 419, 429, 439, 455, 466, 482,
489. The curve rows start at 404, 431, 458, 485, 512, 539, 566, 593. Every roster offset falls
inside a curve row, not at its start, and the deltas are 6, 15, 25, 8, 24, 8, 24, 4. The deltas
are not constant and do not match any field boundary in the 27-byte curve row.

The roster is the vertex roster (eight entries for eight vertices), so its offsets should point
into the vertex table in `MainDataStream`, not into `SurfacicReps`. The vertex table for
`Copper_Washer` starts at 1500, so the roster offsets 410..489 do not address it either.

## The float-run gaps are record headers

The coordinate region is not one contiguous float array. It is a sequence of float runs separated
by 1- to 8-byte headers. The headers carry a repeating shape.

`Reservoir` runs and the header before each:

| Run offset | Floats | Header |
| ---: | ---: | --- |
| 1941 | 128 | `00 00 20 a8` |
| 2461 | 46 | `00 00 00 a8 00 00 38 42` |
| 2653 | 908 | `00 00 00 27 00 00 3c 42` |
| 6445 | 9 | `00 70 07 2c 00 00 c0 3f` |
| 6489 | 124 | `00 98 07 2c 00 00 c0 3f` |
| 6993 | 16 | `00 88 07 2c 00 00 c0 3f` |
| 7065 | 126 | `00 c0 07 2c 00 00 c0 3f` |
| 8253 | 121 | `00 ec 0c 2d 00 00 c0 3f` |

The 8-byte headers end in a float: `00 00 c0 3f` is 1.5, `00 00 38 42` is 46.0, `00 00 3c 42` is
47.0. The 4-byte prefix is not a count: it does not correlate with the run length, and its high byte
is `0x2c` or `0x2d` in most headers.

The header before the first large run is 386 bytes and carries the counts directly:

```
2c 10 00 00  4140   body 3 count
ff ff 02 00 01
ff 97 05 00 00  1431   handle count
ff 97 05 00 00  1431   handle count
00 00 00 00     0
```

The remaining 363 bytes start at 206 with `34 d3 34 33 33 d3 34 33 33 cd d4 45 ...`. Decoding
them with the ported double compactor produces 400 values without a read error, but the values are
garbage: the first three are denormals that print as `0.0`, then the sequence jumps to `1e297` and
stays there. The same happens for reference `1.0`, `46.0`, and `47.0`: the first three values are
the reference plus a small delta, then the stream collapses to `0.0`. So the block is not a
compactor stream at offset 0.

The nibble histogram of the block is heavily skewed: `0` appears 290 times, `1` 91, `8` 66, `4` 59,
`2` 56, `6` 47, `3` 19, `9` 18, `7` 16, `13` 28, and the rest under 10. A 40 percent zero rate with
single-bit nibbles is the signature of a sparse bit array, not of a float stream.

The block is exactly 363 bytes, which is 2904 bits, which is exactly 1452 two-bit values, which is
exactly `4 * 363`. So the block is a whole number of two-bit values with no remainder, and the count
is close to the 1431-value handle space (1452 versus 1431, a difference of 21). That is suggestive
but not conclusive: the two-bit value distribution is `0:866, 1:289, 2:198, 3:78`, which is far too
skewed for a per-quad corner index (a permutation of `0..3` per group of four would be uniform), and
the values do not correlate with the trim structure. So the block is a two-bit array of about the
handle count, but its meaning is not recovered.

The 4-byte prefix in the run headers is not a count. It does not correlate with the run length
(`0x2c077000` precedes a 9-float run and `0x2c079800` precedes a 124-float run), and its high byte
is `0x2c` or `0x2d` in most headers. It is not a file offset either: `0x2c077000` is 738 million,
far beyond the 31 KB stream.

## The tessellation is a CATMathPolyBuffers structure with plain floats

`CATMathStream.dll` exports the `CATMathPolyBuffers` class with getters for every tessellation
buffer: `GetVertexCoordinatesBuffer` and `GetVertexCoordinatesBufferDouble`, `GetVertexUVBuffer` and
`GetVertexUVBufferFloat`, `GetVertexWBuffer` and `GetVertexWBufferFloat`, `GetVertexVectorBuffer` and
`GetVertexVectorBufferDouble`, `GetStripIndicesBuffer`, `GetFanIndicesBuffer`,
`GetVertexLineIndicesBuffer`, `GetEdgeVertexLineIndicesBuffer`, `GetEdgeVertexLineParamsBuffer`,
`GetIsolatedTriangleBuffer`, and the per-primitive count buffers.

`CATMathPolyBuffersStreamer::Unstream` at `0x18009cf50` reads them in a fixed order. The call
sequence is:

```
ReadUShort          version
ReadCATUuid         uuid
ReadUChar           flag
ReadLong            count
ReadBoolean + ReadFloat/ReadDouble   vertex coordinates, count * 3
ReadBoolean + ReadFloat/ReadDouble   vertex UV,          count * 2
ReadBoolean + ReadFloat/ReadDouble   vertex W,           count
ReadBoolean + ReadFloat/ReadDouble   vertex vectors,     count * 3
ReadLong x 5        scalars
ReadLong[] x 5      arrays
ReadShort
ReadLong x 2
ReadLong[] x 2
ReadLong
ReadBoolean
ReadULong
ReadLong
ReadLong[]
```

The coordinate read is explicit. At `0x18009d076` the code computes `leal (%rcx,%rcx,2), %r8d`,
which is `count * 3`, and passes it as the element count to `ReadFloat`. So the vertex coordinates
are `count * 3` plain floats (or doubles), not a compressed stream.

This changes the model. The tessellation is not a bit-packed or compactor-coded stream: it is a
plain float array of `count * 3` values, preceded by a 23-byte header (UShort, 16-byte UUID, UChar,
Long count) and a presence Boolean. The earlier search for a compactor code table was looking for
the wrong thing.

The remaining problem is locating the header. The `Copper_Washer` region before the coordinates is
27 bytes at `199..226`, and the coordinates start at `226` with `-7.6084`. A 23-byte header at `199`
gives a count of `30075`, which is far too large for 76 handles, so the header is not at `199` or the
count field is not a plain `Long` at that offset. The header offset is not yet pinned down.

## The two-bit block boundaries do not transfer between parts

`Reservoir` has a 363-byte block at `206..569` whose two-bit decode is zero-dominated
(`{0:866, 1:289, 2:198, 3:78}`). The analogous region in `Copper_Washer` is the 27 bytes at
`199..226`, between the last body record and the coordinate region at `226`. It does not decode the
same way.

Every 19-byte window in `199..226` (the length that gives exactly 76 two-bit values, one per handle)
is dominated by 2 and 3, not by 0:

```
start 199: {0:1, 1:7, 2:27, 3:41}
start 203: {0:15, 1:8, 2:21, 3:32}
start 207: {0:21, 1:10, 2:18, 3:27}
start 211: {0:26, 1:12, 2:13, 3:25}
```

So either the block boundaries differ per part or the block is not the same encoding. A sliding
scan of the whole `Copper_Washer` stream for zero-dominated 19-byte windows finds only zero-padding
regions (75 of 76 zeros at `750`, `898`, `1647`), not a block with the `Reservoir` profile.

The float compactor does not decode the region either. On `199..226` with reference 8.0 it returns
`7.9456, 7.8843, 7.8229, 7.8229, ...`, which decreases by a constant and then sticks, and with
reference 1.0 it returns `0.9932, -0.9855, -0.9779, ...`. On `226..988` with reference 8.0 it
returns `8.2648, 8.2648, 8.2648, 8.2648, 8.2658, 6.5643, ...`. None of these is the washer's
coordinate set, so the compactor is not the decoder for this region.

The coordinate region itself does not hold the washer's tessellation in the global frame. The
washer's circles are at `x = 0` and `x = 1` with radius 8 and 5, so a stored tessellation would have
many floats equal to 0.0 and 1.0. The region has only about 15 zeros and one 1.0, far short of the
~38 + ~38 needed for 76 points. So the region is not the tessellation in the global frame, and the
angular positions of the edge handles are not recoverable from it.

## The shell face-reference loop is not a plain index array

The shell record is supposed to carry a face-reference loop of one entry per face. For `Reservoir`
that would be 71 entries. No such loop exists as a plain index array:

- no run of 71 consecutive `u32` values all below 71 exists in `MainDataStream`;
- no run of 71 consecutive `u16` values all below 71 exists either;
- no run of 71 records of the shape `u32 zero + odd byte` (a `ReadObject` table index of 0 followed
  by a one-byte scalable tag difference) exists at stride 5;
- no run of 71 `u32` zeros exists at stride 4.

The same holds for `Pedal_Body` (338 faces) and for `Copper_Washer` (6 faces). So the face-reference
loop is not a contiguous array of indices or of `index + tag-difference` pairs. It is either
interleaved with other fields or encoded differently, and it is not recoverable by a stride scan.

## The coordinate table holds 1003 points, not 1431

Parsing the region `569..12401` with the five-float group `(x, y1, z, y2, z)` and the three-float
triple `(x, y, z)` yields 1003 points: 51 five-float groups and 901 triples, with no skipped bytes.
The first points are `(-35.5, -0.5, 37.418)`, `(-35.5, 0.5, 37.418)`, `(-35.353, -0.854, 37.42)`,
which are symmetric pairs on a plane at `z = 37.418`.

The handle space is 1431 values, so the handles are not indices into this 1003-point table. The
table cannot hold 1431 three-float points in 11832 bytes: that would be 8.27 bytes per point, below
the 12-byte minimum.

## The handle-to-point map is not a plain index into any point table

`Copper_Washer` is the cleanest case because it is small. It has 6 faces, 8 B-rep vertices, 8 roster
entries, 12 edges, and 76 distinct handles spanning `0..75`. So the handles are not vertex indices:
there are 8 vertices and 76 handles.

The edge table is not a list of two-handle edges. It is a list of polylines with arity 9 to 11:

```
0: (37, 35, 33, 29, 23, 18, 13, 7, 4, 2, 0)
1: (75, 73, 71, 67, 61, 56, 51, 45, 42, 40, 38)
2: (0, 1, 3, 6, 12, 17, 22, 28, 32, 34, 37)
3: (38, 39, 41, 44, 50, 55, 60, 66, 70, 72, 75)
4: (5, 8, 10, 14, 16, 20, 24, 26, 31)
5: (30, 27, 25, 21, 19, 15, 11, 9, 5)
6: (43, 46, 48, 52, 54, 58, 62, 64, 69)
7: (68, 65, 63, 59, 57, 53, 49, 47, 43)
8: (36, 74)
9: (0, 38)
10: (31, 69)
11: (5, 43)
```

Edges 0 and 2 are the same closed loop in opposite directions, as are 1 and 3, 4 and 5, and 6 and 7.
So the tessellation has four closed loops (11, 11, 17, and 17 handles) joined by four connectors
`(36,74)`, `(0,38)`, `(31,69)`, `(5,43)`. The loops are the washer's four boundary circles.

The coordinate region `226..988` holds 190 floats, of which 180 are nonzero, so it is real data and
not padding. `190 / 76 = 2.5` floats per handle, so it cannot be a plain three-float point array for
76 handles (that needs 228 floats).

The five-float grouping is arithmetically exact: `190 = 38 * 5`, and two points per group gives 76
points, exactly the handle count. But the resulting points do not form the washer's circles. The
washer's vertices are at radius 8 and 5 from its axis, and under the five-float reading only 21 of
the 76 points land at radius 8 or 5; the rest are at 0, 3.5, 6.53, and other radii. So the grouping
is not confirmed.

The `Reservoir` five-float group is `(x, y1, z, y2, z)` with `z1 == z2`, for example
`(-35.5, -0.5, 37.418, 0.5, 37.418)`. The `Copper_Washer` region does not follow that layout: its
first group is `(-7.6085, -2.4721, 2.4721, -6.4721, -4.7023)`, where the third and fifth floats
differ. So the two parts do not share one five-float layout, and the `Copper_Washer` layout is not
recovered.

A direct search for the tessellation as plain triples also fails: no run of 10 or more consecutive
three-float triples at radius 5 or 8 exists anywhere in the stream, for any axis. So the tessellation
is compressed, and the compression is not the five-float group as read.

## The `42 ff` region is not connectivity

`Reservoir` has one `42 ff` record at 12376: a `u32` count of 2850 followed by 2850 `u16` values.
The values are not point indices. They span `0..65535` with 943 distinct values, and the first
values are `0, 65179, 0, 65179, 0, 65179, 42368, 65284, ...`, a delta-like pattern rather than a
triangle index list. Only 832 of 2850 values are at most 1002, the point count.

## Open work

1. Locate the shared tessellation vertex table and its coordinate encoding.
2. Decode the tessellation-to-B-rep edge linkage.
3. Decode the face-to-surface reference for shared surface pools.
4. Resolve the surface record trailer rule.
5. Decode the 4-byte prefix in the run headers and the 364-byte high-entropy block.

## Evidence

- `re/catia/tooling/ParseBrep.py`
- `src/convert/adapters/catia/NativeTopology.py`
- `src/convert/adapters/catia/NativeBrep.py`
