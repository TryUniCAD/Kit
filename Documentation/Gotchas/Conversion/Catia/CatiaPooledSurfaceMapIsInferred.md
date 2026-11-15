# CATIA pooled surface map is inferred, not decoded

## Expectation

A CATIA V5 part stores one surface per face, so the surface list in `SurfacicReps` can be zipped
with the face list in `MainDataStream`.

## Actual behavior

Five corpus parts (`4784`, `4876`, `4876_1`, `Pedal_Body`, `Reservoir`) have fewer surfaces than
faces: 270/416, 714/870, 714/870, 314/338, and 56/71. The surfaces are pooled, and several faces
share one surface. The face-to-surface reference is not in the face record, the body record, the
trim chain, the face-outer-bound run, the `42 ff` block, the `60`/`54` tail, or any of the twelve
`MainDataStream` regions. It is carried by the edge's `CATPCurveEquation`, whose Stream writes the
surface as its first object, but the PCurve record is not located in `MainDataStream` or
`SurfacicReps`, and the concrete function class is caller-supplied, so the record has no fixed
signature.

The reader therefore infers the map from the `00 33 37` edge records: a plane face is matched to the
plane surface with the same offset along the trim normal as the edge circle centers, a cylinder face
is matched to the cylinder surface with the edge circle radius, and the remaining faces take the
least-used surface whose kind is compatible with the trim kind. The inferred map is total, so all 27
corpus parts decode, but it is not the stored map.

A plain index table is ruled out: every stream of `Reservoir` was scanned for a run of exactly
`FaceCount` 8-bit or 16-bit little-endian values below the pool size that covers at least 85% of the
pool, and no such run exists, so the reference is not an array of surface indices. A permutation
table is ruled out too: every exact part was scanned for a run of `n` 8-, 16-, or 32-bit
little-endian values that is a permutation of `0..n-1` (the shape the identity map would take), and
only the two six-face washers hit, at a relative offset of `-245`, which is a vertex-index run. A
table of `SurfacicReps` record offsets is ruled out as well: the first surface record starts at
offset `17`, and no stream contains that value followed by the offsets of the next records.

The per-face record cannot carry the choice either. `30 04 04 ff ff` appears exactly `FaceCount`
times in every part and is followed by the same three bytes `e1 e1 e1` in every one of the 71
`Reservoir` faces. A constant payload cannot encode a 56-way choice, so the surface is not named
there. The only per-face-looking record left is `30 04 04 fd ff`, which appears exactly three times
in every part regardless of face count.

A contiguous tag array is ruled out for the same reason the index table is: no offset in
`MainDataStream` decodes, through `TagDifference.ReadTags`, to `0..n-1` for `n = 6`, `12`, `56`, or
`71`.

The linked-object list itself is now pinned. `CATCGMStreamImpl::ReadListOfLinkedObjects`
(`CATGeometricObjects.dll` `0x1800717f0`) gates on the stream version (`0x0d`, or `0x0c` with
version `0x14`) and then reads two named stream fields: `#NBLinkObjs` (the count) and `^LinkObj`
(the array), with four bytes per entry. `CATCXFace::UnStream` (`CATTopologicalObjects.dll`
`0x18054eef0`) takes the object at list index `1` as the surface and adds entries from index `2` on
to `CATCXOrientedFaces`. A face therefore needs a header of at least `1 + 2 * 4 = 9` bytes, which
rules the eight-byte `30 04 04 ff ff e1 e1 e1` record out as the face header.

Recorded searches for that header all failed on `Reservoir`: no run of 71 records with a
count-then-four-byte-entry shape exists at a fixed stride `9`, `13`, `17`, `21`, or `25`, and no
`03 00 00 00` followed by three entries below the pool size exists anywhere in `MainDataStream`.

`CATCXFace::Stream` (`0x18054eba0`) shows the list is not written by the face at all. The face
writes its domain count (domain count plus one when the owner pointer is present), then one named
record per domain obtained from `GetDomain`, then a `u16` field. There is no
`WriteListOfLinkedObjects` call in that function, so the face's linked-object list is emitted by
`CATCXBody::Stream` (`0x180541d60`), which writes the element groups and passes each list to
`CATCXFace::UnStream` on the read side. That is why every face-local scan misses.

Both candidate face layouts were probed over the corpus. A count followed by `count` ULONG entries
reaches at most 18 records in `Reservoir`; the `count + 1` entries plus a `u16` layout that
`CATCXFace::Stream` implies reaches no run at 90% of the face count for `4784`, `Pedal_Body`, or
`Reservoir`. `re/catia/tooling/ProbeLinks.py` prints both.

The field framing is now pinned too. The count goes through
`CATMathStreamImpl::WriteULong(value, "#NBLinkObjs")` (`CATMathStream.dll` `0x1800b7bb0`), which
builds a prefix byte: bit `0x10` is set when byte 1 is non-zero, `0x20` for byte 2, and `0x40` for
byte 3, and the low bit is never set. The prefix is followed by one to four little-endian bytes. The
array is read with `ReadULong(uint*, count, "^LinkObj")`, so every element uses the same
prefix-plus-bytes form. Decoding `MainDataStream` with that rule and looking for runs of
`count`-then-`count`-entries records reaches only 18 records at offset `29353` in `Reservoir`, not the
71 faces, so the list is either outside `MainDataStream` or interleaved with other named fields.

`RefineMap` sharpens the inferred map without changing its status. It places the handles without the
tessellation snap, then re-picks each plane face's pooled plane by the summed distance of the face's
handles from the plane through the surface center along the stored trim normal, and each cylinder
face's pooled cylinder by the summed radial distance. One probe handle rejects a surface farther
than `0.5`, and refinement runs two rounds only for pooled parts with at most 400 faces, because a
round costs a full corner placement and the two largest parts gain under 3%. That drops the
unsatisfied handles from 209 to 181 of 1431 on `Reservoir` and from 1923 to 792 of 2666 on
`Pedal_Body`. The map is still inferred.

## The out-of-range keys are ids, not names

Twelve `7c 07` blocks in the parametric samples carry keys `0xef..0xfd` (`239..253`) while the local
symbol table has `234` entries for `ISO_2338_PARALLEL_PIN` and `238` for the washer. Those keys are
not compact integers: `CATBmxStream::ReadInt` only covers `0x80` (escape), `0x81..0xd0`, and
`0xd1..0xe4`, and every one of these keys is above `0xe4`, so the compact-int reading suggested for
the attribute key is refuted for these blocks. A constant index shift does not explain them either:
the best overlap with names already used in the same part is `11/12` at a shift of `38` for the pin
and `12/13` at a shift of `19` for the washer, i.e. part-specific and indistinguishable from
coincidence.

The consistent reading is that these are early attributes, which CATIA stores by numeric id before
the names are known; `CATObjectSpecsModeler.dll` exposes separate readers for that form
(`ReadEarlyAttribute` `0x1800d93c0`, `ReadEarlySpecAttr` `0x1800d96e0`). They carry only an escaped
`u32` and references, never a double, so they do not hold the parameter values and they are not the
cause of the `Mass` misparse.

## The topology streamers carry no surface

`CATCXEdge::Stream` (`0x1805471e0`) writes an edge count of `4`, or `5` when bit `0x200` is set on
the object, then the vertices and points-on-edge-curve records, then named records. `CATCXLoop::Stream`
is a jump to `CATCXEdgeDomain::Stream` (`0x180548090`), which writes the domain location, an edge
count, and per-edge records. Neither writes a surface or a PCurve reference, so the surface named in
the PCurve equation is not in the topology streamers.

One more oracle was tried and failed. For `Reservoir` the correct map must decode 71 entries with
exactly 56 distinct values below 56. Scanning both streams at every offset with
`TagDifference.ReadTags` for `Current` in `0, 56, 71`, requiring `max(tags) < 56` and exactly 56
distinct values, returns no hit. That rules out a tag-difference array of face-to-surface references
in `MainDataStream` and `SurfacicReps` as well.

## The circle records pin only a few faces

The `00 33 37` records do carry a face pair: every circle in `Reservoir` (78), `4784` (210), and
`Pedal_Body` (391) has both index bytes below the face count. A circle whose partner is a plane face
`p` gives a non-circular constraint on a cylinder face: a pooled cylinder must have radius equal to
the circle radius and its axis must pass through the circle center. Counting faces that this pins
uniquely gives `7` of the `55` faces that have any candidate cylinder in `Reservoir`, `0` of `79` in
`4784`, and `5` of `208` in `Pedal_Body`. Most cylinders share a radius or an axis, so the
constraint almost never resolves to one surface, and it cannot close the map.

## The per-object framing chain, from decompilation

Hopper decompilation through `npx rea-agents decompile --provider hopper` now works on the smaller
CATIA modules, and it names the chain that owns the linked-object list:

```
CATCGMStreamCGMImpl::Unserialize_Object        0x180052220
  -> CATCGMStreamCGMImpl::CreateObjectUnStream
       -> CATMathStreamImpl::ReadHeaderObjectAt 0x1800a56a0
            version <  0x3ef      -> ReadHeaderObjectAt_V5R5      0x1800a8300
            flags & 0x10001       -> ReadHeaderObjectAt_SmallHeader 0x1800a7310
            otherwise             -> inline header read
       -> ReadListOfLinkedObjects  (the "#NBLinkObjs"/"^LinkObj" pair)
       -> object->UnStream(stream, list)
```

`ReadHeaderObjectAt_SmallHeader` reads one byte, requires `(byte & 0xe0) == 0xa0`, takes
`byte & 0x0f` as a type index, and resolves it through `CATCGMTypeByteIndexToShortValue` using two
following bytes. So a compact object header begins with `0xa0..0xaf`, and the linked-object list
follows the header, not the object payload.

Scanning `Reservoir` for that layout — a `0xa0..0xaf` byte, a three-byte header, then a count and
`count` ULong entries, repeated for at least twenty records — returns no run. The corpus therefore
does not use the small-header path at these offsets, and the header size for the other two paths
depends on the stream version, which is the next thing to read.

## The V5R5 header layout, and why it does not chain here

`ReadHeaderObjectAt_V5R5` (`CATMathStream.dll` `0x1800a8300`) consumes exactly `0x15` bytes and
requires the byte at header `+6` (or `+7` when the stream flag `0x20000` swaps byte order) to equal
`0xb3`. It then reads three 16-bit fields — at `+4`, `+8`, and `+0xc` — and computes two boundaries:
`pos + field8` and `pos + field8 + field12`. `pos + 0x15` is where the object's own data starts, so
the header declares the object length and a second trailing length.

Walking `Reservoir` with that rule finds no chain longer than one record. Tested combinations: marker
at `+6` and `+7`, little- and big-endian 16-bit fields, and length pairs at `(+8, +0xc)`,
`(+8, +0xa)`, `(+4, +8)`, and `(+0xb, +0xd)`. No combination chains past the first header, so
`MainDataStream` is not a run of V5R5 object headers either — the file is on a newer header path
where the length fields move.

## The writer does not reproduce the vendor stream skeleton

Comparing the writer's box output with three vendor parts by parsed structure — not by raw byte counts,
which is what an earlier version of this note used and got wrong:

| file | `MainDataStream` | `SurfacicReps` | vertex tables | vertex rows | roster rows | `fd` records |
| --- | --- | --- | --- | --- | --- | --- |
| `Washer_8` (vendor) | 2202 | 666 | 1 | 8 | 8 | 3 |
| `Nut_M6` (vendor) | 6121 | 3057 | 4 | 40 | 40 | 3 |
| `Banjo` (vendor) | 8977 | 3795 | 3 | 50 | 50 | 3 |
| writer `box` | 444 | 631 | 1 | 8 | 8 | 0 |

The vertex table, the vertex rows, and the roster agree with the vendor convention (one roster row per
vertex). The one known structural gap is that the writer emits none of the three `30 04 04 fd ff`
records, whose layout and one derivable field are in
[the fd record gotcha](CatiaFdRecordsCarryStreamLength.md). A raw `0x54` byte count is not a roster
count — the roster row is `54 <u32> 00 00 00`, so the byte appears inside unrelated records too.

## A pooled plane's orientation cannot be recovered from its record alone

`MakePlane` uses the stored trim vector when the face carries one. On a pooled part the inferred map
can pair a cylinder-kind trim with a plane record, so `VectorValue` is `None` and the fallback
`BoundsNormal` runs. That fallback returns `+X`, `+Y`, or `-Z` by picking the axis of the smallest
bounding-box half-extent, so it can only produce an axis-aligned normal. A tilted plane's bounding box
carries no normal information at all, which is why the pooled plane deviations reach `36` to `96` on
parts whose exact-map peers sit at `0.0000`. The fix is not in the record: it needs the map to know
which faces really are planes. Measured, not assumed: `BoundsNormal` output is one of six axis
vectors for every plane record in the corpus.

## A normal part save writes no linked-object list at all

Decompiling the whole object path settles the question the earlier section could not:
`CATCGMStreamCGMImpl::Unserialize_Object` (`0x180052220`) calls `CreateObjectUnStream`
(`0x1800519e0`), which reads the 21-byte header, builds the object, and then consumes the header
flags (`r14[0]`, `r14[0x18]`, `r14[0x19]`) into object state. It never calls
`ReadListOfLinkedObjects`, and the only callers of `WriteListOfLinkedObjects` in the DLL are
`CATCGMStream::WriteListOfLinkedObjects` (`0x18006ed10`, a public API for features) and
`CATCGMJournalItem::Stream` (`0x180198375`).

So `CATCXFace::UnStream` receives an empty list on a normal part save, and the `#NBLinkObjs`/
`^LinkObj` mechanism is not where a face's surface comes from. The surface reference must therefore
be in the geometry stream itself, which is named `SurfacicReps` — "surface representations". Every
scan so far treated that stream as a table of `00 33 <kind>` surface records; the PCurve records that
name a surface per edge have to live in the same stream, and the region between the surface records
is where to look next.

## The gaps between surface records carry float frames, not references

`SurfacicReps` is not a dense table: `Reservoir` has `7` nonzero gaps (`47, 94, 141, 235` bytes,
658 bytes total) and `4784` has `6` (`47`, `3337`), measured between consecutive surface records.
Decoding a 47-byte gap as little-endian `f32` after a four-byte prefix gives two frames of the form
`(x, y, z, a, b, c)` with a shared point, for example

```
prefix 00 00 00 58
(-20.9, -0.75, 44.75, 0.1047, 0.25, 1.0123)
(-20.89, -0.75, 44.75, 0.3689, ...)
```

and the same values recur in separate gaps (`4f 8c a7 41` appears in three of them), so these are
geometry samples of the neighbouring surface rather than per-face references. They do not contain a
face index, and with only `7` gaps they cannot carry a map for `71` faces.

## The corpus carries no CGM object headers at all

The three header forms `CATMathStreamImpl` knows each have a marker byte: `0xb3` in the V5R5 form,
`0xa0..0xaf` in the small-header form, and `0xe5` in the inline form
(`CATMathStreamImpl_ObjectHead.cpp`, `0x1800a5722`). Counting those markers in the streams:

```
Reservoir      main 0xb3/0xaX chains 0     main 0xe5 47    surf 0xe5 4
4784           -                           main 0xe5 253   surf 0xe5 36
Copper_Washer  -                           main 0xe5 0     surf 0xe5 0
```

`Copper_Washer` has **no** `0xe5` byte anywhere, and a fifty-face part cannot serialize without
object headers if it used that form, so the corpus does not write CGM object headers into
`MainDataStream` or `SurfacicReps` at all. The B-rep is stored in a compact final form with no object
table, which is why the surface reference is not reachable through any header path.

## A dimension carries an attribute id, and its value lives in the owning object

With the compact-int decoder in place, the `d_dia` attribute parses as
`('int', 1088), ('ref4', 'd4170437')` and `('int', 1089), ('ref3', 'c41737')` — an attribute id
(`0x440`, `0x441`) plus a reference that is identical in every block, so it names a type rather than a
value. `ISO_2338_PARALLEL_PIN` holds only eight doubles in the whole object graph, and the `8.0` sits
inside object `10` together with `200.0` and `15.0`, not in a separate parameter object. A dimension
therefore points at an attribute id, and the value is stored in the object that owns the dimension,
so the name-to-value edge needs an attribute-id table, not an object lookup.

## The pool order is not correlated with the face order

The natural streaming encoding would be "surfaces appear in first-use order", so the sequence of pool
indices over the faces would be non-decreasing and would advance by at most one. That is testable as
a reachability problem: `p[0] = 0`, `p[last] = m - 1`, `p[j+1]` is `p[j]` or `p[j] + 1`, and every
face's surface kind is one its trim kind allows. It is infeasible on all four large pooled parts:

```
Reservoir   faces  71 pool  56   monotone-first-use feasible False
Pedal_Body  faces 338 pool 314   monotone-first-use feasible False
4784        faces 416 pool 270   monotone-first-use feasible False
4876        faces 870 pool 714   monotone-first-use feasible False
```

The weaker form — surfaces grouped by kind, and first-use order only inside each kind — is infeasible
too, on every part and every kind that has more than one determinate face:

```
Reservoir   0x32 faces 13 pool 13 True    0x34 faces  5 pool  9 False
Pedal_Body  0x32 faces 54 pool 66 False   0x34 faces  9 pool 22 False
4784        0x32 faces 83 pool 91 False   0x34 faces 14 pool 26 False
4876        0x32 faces 335 pool 359 False 0x34 faces 18 pool 68 False
```

`Reservoir`'s one `True` is the degenerate case where face count equals pool count, which forces the
identity order and therefore carries no information. So the pool order is unrelated to the face order
in both forms, and an order-based decode is ruled out along with the index, permutation, and offset
table forms.

Fitting a plane through a face's own placed handles does not rescue the plane faces either: on
`Reservoir` 10 of the 13 plane faces have exactly coplanar handles, but the residuals for the rest
(`2.84`, `0.49`, `0.47`) show that the handles themselves are placed off their surface whenever the
map is wrong, so the plane orientation and the handle placement are circularly dependent and geometry
alone cannot break the loop.

## Workaround

Treat the five pooled parts as approximate. The reader emits
`catia.brep.native_surface_map_heuristic` for them. Do not use their decoded geometry as a
ground-truth control, and do not claim lossless conversion for them. The exact map needs the PCurve
record or a controlled corpus generated through the vendor API.

## Evidence

- `src/convert/adapters/catia/NativeBrep.py` `AssignSurfaces` and `ParseEdgeCircles`.
- `re/catia/Brep.md` sections on the `60`/`54` tail, the `42 ff` block, the staircase negative
  result, and the PCurve Stream.
- `Documentation/Changes/Catia/CatiaNativeBrep.md` limits and verification.
