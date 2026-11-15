# CATIA native B-rep reader and writer

## Behavior

The `catia.v5` adapter now decodes the standard nested CATIA V5 B-rep spine.
It reads the face-outer-bound run, trim packets, edge table, vertex table, surface records, curve
rows, and vertex roster from `MainDataStream` and `SurfacicReps`.
It maps the result to a neutral `BrepModel` with faces, loops, coedges, edges, vertices, and
analytic plane, cylinder, cone, sphere, and torus surfaces.

The trim handles are dense indices into a shared tessellation table, not B-rep vertex identifiers.
The handle-to-point map is not decoded. The handle count exceeds the B-rep vertex count in every
part (`Reservoir` has 1431 handles and 88 vertices, `Copper_Washer` has 76 handles and 8 vertices),
and the coordinate region is a sequence of float runs separated by record markers. The reader places
each handle by the corner structure. The arity-2 handles are assigned distinct vertex-table points
by a bipartite match over the plane and cylinder constraints. The 2-face handles are placed on the
intersection curve of their two faces: for a plane-cylinder pair that is a circle, and for a
plane-cone pair whose plane is perpendicular to the cone axis that is also a circle, and the handles
are spread at equal angles along the arc between the two endpoint vertices. The 1-face handles take
the nearest satisfying vertex. That replaces the earlier `handle % len(vertices)` placeholder and
makes the planar faces coplanar for the simple parts. The equal-spacing placement is then snapped
onto the stored tessellation points in the part's local frame, so the final positions are the
file's points where the tessellation is decoded.

The stored tessellation angles are now measured, and they are not the assumed ones. The 116-float
run at `226..690` in `Copper_Washer` `MainDataStream` contains only values from `8 * cos(18k)`,
`8 * sin(18k)`, `5 * cos(22.5k)`, `5 * sin(22.5k)`, and `1.0`, with zero of 116 values outside that
table. So the stored tessellation has 20 points on the outer circle at 18-degree steps and 16 on the
inner at 22.5-degree steps. The reader places 11 handles over a semicircle at 15-degree steps, so
only 26 of the 76 placed vertices land on the stored grid. The angular positions are therefore a
uniform refinement, not the stored tessellation, and the change entry keeps the geometry classified
as a structural approximation.

The tessellation points themselves are now decoded and exposed. `DecodeTessellation` finds the
longest run of plausible floats in `MainDataStream`, skips the two-float header, and walks the
`(y, z, abs(z))` records, keeping the pairs whose radius matches a cylinder radius from the surface
records. For `Copper_Washer` that returns 41 points, all 41 on the 18-degree and 22.5-degree grid,
with radii exactly 5 and 8.

The handles are then snapped onto those points in the part's local frame. The frame is derived from
the dominant cylinder carrier axis, so a part whose cylinders run along `z` or `y` uses the matching
perpendicular pair rather than the global `(y, z)`. Snapping in the global frame broke `Washer_5`,
`Washer_8`, and `Brake_bias_90_degree_coupler` (planar deviation 0.0 to 2.65, 2.32, and 4.05)
because their axes are `z`, `z`, and `z`/`y`. Snapping in the derived frame keeps every part at its
previous deviation and puts all 76 `Copper_Washer` vertices on the stored grid, up from 26.

Every placed handle satisfies all the surfaces of the faces that use it. Across the 22 decoded parts
that is 4682 of 4682 handles on-surface, with zero exceptions. The plane-cone case covers 423 of the
555 plane-cone handles; the other 132 are oblique sections (ellipse, parabola, hyperbola) and are
left on the vertex-table fallback rather than being forced onto a circle.

An edge whose two endpoints both lie on one of those intersection circles gets a `CircleCurve`
instead of a chord. Across the corpus that is 1661 circular-arc edges, and the worst endpoint radius
error is 1.8e-6. For `Copper_Washer` the inner circle at `x = 0` sums to exactly its circumference
(31.416 against `2 * pi * 5`), and the outer circles sum to 48.209 against 50.265 because the seam
gap and the seven straight edges are not arcs. Edges that are not on a circle stay `LineCurve`.

One partial map is recovered: the handles that appear in arity-2 edges are the B-rep vertices. This
is exact for the simple parts (`Copper_Washer`, the washers, `Banjo`, the nuts, and
`Brake_bias_90_degree_coupler`, where the arity-2 handle count equals the vertex count) and a strict
superset for the complex parts (`Reservoir` 109 versus 88, `4784` 830 versus 772). It covers only the
corner handles, not the tessellation points.

For `Copper_Washer` the face-to-loop structure is complete: the four edge loops are the four
boundary circles (outer and inner at `x = 0` and `x = 1`), and the six faces are the two annular
planes and the four cylinder halves. Placing the loop handles on their circles at equal angular
spacing makes both planar faces coplanar with their trim vectors at zero deviation.

The trim handles are corners, not points. Counting the faces that use each handle gives 4 handles
used by 3 faces (the vertices), 68 used by 2 faces (edge interiors), and 4 used by 1 face. Grouping
the 2-face handles by face pair gives the eight face-to-face edges, and each of the four circles is
split into two edges (outer 10 + 9 handles, inner 7 + 8). So the planar faces are bounded entirely
by the circles, and the handles that looked like interior points are the 2-face handles of the
`(0, 2)` edge on the outer circle at `x = 0`.

The corner structure is enough to rebuild the whole `Copper_Washer` B-rep: the eight arity-2 handles
are the vertices, the eight 2-face handle groups are the edges, and each edge is a circular arc on
the intersection of its two faces. Placing the edge handles at equal angular spacing places 74 of
the 76 handles and makes both planar faces coplanar with their trim vectors at zero deviation
(56/56 and 50/50 points). The arc lengths match semicircles of the expected radii. The angular
positions are assumed equal-spaced, not decoded, so this is a reconstruction from the topology, not
a decode of the stored tessellation.

The two-bit block does not supply the angular positions. `Reservoir`'s block at `206..569` is
zero-dominated, but every 19-byte window in `Copper_Washer`'s candidate region `199..226` is
dominated by 2 and 3, and a sliding scan finds only zero-padding regions, not a block with the
`Reservoir` profile. The float compactor does not decode the region either. The coordinate region
also does not hold the tessellation in the global frame: it has only about 15 zeros and one 1.0,
far short of the ~38 + ~38 needed for 76 points on the `x = 0` and `x = 1` circles.

The tessellation is not compressed at all. `CATMathStream.dll` exports `CATMathPolyBuffers` with
getters for vertex coordinates, UV, W, vectors, strip/fan/line indices, and isolated triangles, and
`CATMathPolyBuffersStreamer::Unstream` at `0x18009cf50` reads them in a fixed order. The coordinate
read computes `count * 3` and passes it to `ReadFloat`, so the vertex coordinates are `count * 3`
plain floats, preceded by a 23-byte header (UShort, 16-byte UUID, UChar, Long count) and a presence
Boolean. The remaining problem is locating that header: a 23-byte header at `199` gives a count of
`30075`, far too large for 76 handles. The call site does not resolve it either: there is no direct
`callq` to `0x18009cf50` and no 8-byte VMA reference, only a 4-byte RVA in a dispatch table at file
offset `0x13fbac`, so the streamer is reached through an indirect dispatch. A whole-stream search for
float and double triples on the washer's circles finds nothing, so the stored coordinates are in a
local frame or a different ordering.

The surface records are ordered by face only when the two counts match. For all 22 parts where the
surface count equals the face count, the surface planarity sequence is identical to the face
planarity sequence. For the five parts with fewer surfaces than faces, the surface planarity
sequence is only a subsequence of the face planarity sequence, and that is not enough to order the
list: a monotone surjection from faces to surfaces exists for `Reservoir` and `Pedal_Body` but is
non-unique (12600 and 1.3e20 solutions), and does not exist at all for `4784`, `4876`, and `4876_1`.

The reader now decodes those five parts with an inferred map instead of rejecting them. The map is
built from the `00 33 37` edge records, which carry a face pair and the edge circle. A plane face is
matched to the plane surface whose center has the same offset along the face's trim normal as the
edge circle centers. A cylinder face is matched to the cylinder surface whose radius equals the edge
circle radius. The remaining faces are matched to the least-used surface whose kind is compatible
with the trim kind. The result is a total map, so all 27 corpus parts decode, but the map is
inferred, not decoded: 17 of 71 `Reservoir` faces, 143 of 338 `Pedal_Body` faces, 336 of 416 `4784`
faces, and 722 of 870 `4876` faces fall through to the least-used fallback. The reader emits a
`catia.brep.native_surface_map_heuristic` warning for those parts, and their geometry is approximate.

After the first pass, `RefineMap` re-picks each face's surface: it places the handles without the
tessellation snap, then for every plane face chooses the pooled plane that minimizes the summed
distance of the face's own handles from the plane through the surface center along the face's stored
trim normal, and for every cylinder face the pooled cylinder that minimizes the summed radial
distance. One probe handle rejects a surface farther than `0.5` from the face before the full sum,
and refinement runs two rounds for a pooled part with at most 400 faces and none for a larger one,
because each round costs a full corner placement and the two largest pooled parts gain under 3%.
Refinement drops the unsatisfied handles from 209 to 181 of 1431 on `Reservoir` and from 1923 to 792
of 2666 on `Pedal_Body`; the map is still inferred, and the warning stays.

The warning now carries a measured confidence instead of a bare claim: `MapConfidence` counts, per
face, how many surfaces of the same kind pass within `0.5` of the face's first placed handle, and the
diagnostic reports the faces with exactly one candidate. That number is `25/416` for `4784`,
`29/870` for `4876` and `4876_1`, `57/338` for `Pedal_Body`, and `45/71` for `Reservoir`. It is the
honest measure of how much of each pooled map is actually determined by geometry, and it is the
target the controlled corpus has to lift to `FaceCount`.

The correct map is the composition face -> loop -> edge -> PCurve -> surface. `CATCXFace::Stream`
(`0x18054eba0`) writes only the loop count, the loops, `SurfaceOrientation`, and `IsInfinite`, and
`CATCXBody::Stream` (`0x180542210`) writes three element groups with no face-to-surface array. The
surface is named by the edge's `CATPCurveEquation`, whose Stream (`0x1800bf2b0` in
`CATGeometricObjectsCGM.dll`) writes the linked-object count, the surface, four doubles, and two
`CATMathFunctionGeneral` streams. The PCurve record is not located in `MainDataStream` or
`SurfacicReps`: a scan for four doubles followed by a function domain byte and type gives no hits,
and the concrete function class is caller-supplied, so the record has no fixed signature.

Four more negative results narrow the reference. A `SurfacicReps` offset table does not exist: the
first surface record starts at offset `17` and no stream continues that value with the next record
offsets. The per-face `30 04 04 ff ff` record cannot carry the choice, because it appears exactly
`FaceCount` times and its three-byte payload is constant (`e1 e1 e1`) in all 71 `Reservoir` faces, so
it cannot encode a 56-way selection. The other per-face-looking record, `30 04 04 fd ff`, appears
exactly three times in every part regardless of face count. And no offset in `MainDataStream`
decodes through `TagDifference.ReadTags` to `0..n-1` for `n = 6`, `12`, `56`, or `71`, so the
linked-object list is per object with one surface entry rather than a body-wide array.

The linked-object list is pinned: `CATCGMStreamImpl::ReadListOfLinkedObjects`
(`CATGeometricObjects.dll` `0x1800717f0`) reads the named fields `#NBLinkObjs` and `^LinkObj` with
four bytes per entry, and `CATCXFace::UnStream` (`0x18054eef0`) takes entry `1` as the surface. A
face header is therefore at least nine bytes, which rules the eight-byte
`30 04 04 ff ff e1 e1 e1` record out as a face header. No 71-record fixed-stride run of that shape
exists in `Reservoir` at stride `9`, `13`, `17`, `21`, or `25`, and no `03 00 00 00` followed by
three entries below the pool size exists anywhere in its `MainDataStream`.

The link field framing is pinned: the count is written by
`CATMathStreamImpl::WriteULong(value, "#NBLinkObjs")` (`CATMathStream.dll` `0x1800b7bb0`), whose
prefix byte sets bit `0x10` for byte 1, `0x20` for byte 2, and `0x40` for byte 3 and is followed by
one to four little-endian bytes, and the array is read by `ReadULong(uint*, count, "^LinkObj")` with
the same element form. Decoding `MainDataStream` with that rule gives at most 18 consecutive records
in `Reservoir` (offset `29353`), not 71, so the face list is not a contiguous run in that stream.

`CATCXFace::Stream` (`0x18054eba0`) writes only the domain count, one named record per domain from
`GetDomain`, and a `u16`, so the face never writes its own linked-object list: the list is emitted by
`CATCXBody::Stream` with the element groups and handed to `CATCXFace::UnStream`. Probing both
face-local layouts over the corpus finds no run reaching 90% of the face count for `4784`,
`Pedal_Body`, or `Reservoir`; `re/catia/tooling/ProbeLinks.py` prints the candidates.

The circle records do carry a face pair, and the pair can constrain a pooled surface without
circularity: a circle whose partner is a plane face requires a cylinder face to have the circle's
radius and an axis through the circle center. Measuring that constraint gives only `7` uniquely
pinned faces of `55` candidates in `Reservoir`, `0` of `79` in `4784`, and `5` of `208` in
`Pedal_Body`, so it sharpens the map without closing it.

An order-based decode is ruled out as well. If surfaces were written in first-use order, the pool
index over the faces would be non-decreasing and advance by at most one; that reachability problem is
infeasible on all four large pooled parts (`71/56`, `338/314`, `416/270`, `870/714`), and the weaker
kind-grouped form is infeasible on every kind with more than one determinate face (`0x32` and `0x34`
on all four). Fitting a plane through each face's own handles is only partially usable: `Reservoir`
has 10 of 13 plane faces exactly coplanar, but the remaining residuals (`2.84`, `0.49`, `0.47`) are
the handles being placed off-surface, so orientation and placement are circularly dependent.

Neither topology streamer writes a surface: `CATCXEdge::Stream` (`0x1805471e0`) writes an edge count
of `4` or `5`, the vertex records, then named records, and `CATCXLoop::Stream` jumps to
`CATCXEdgeDomain::Stream` (`0x180548090`), which writes the location, an edge count, and per-edge
records. A final oracle also failed: no offset in `MainDataStream` or `SurfacicReps` decodes, through
`TagDifference.ReadTags`, to 71 entries with exactly 56 distinct values below 56, which is the shape
`Reservoir`'s map must have.

The linked-object mechanism is ruled out for normal parts: `CATCGMStreamCGMImpl::CreateObjectUnStream`
(`0x1800519e0`) reads the 21-byte header, builds the object, and consumes the header flags, never
calling `ReadListOfLinkedObjects`; the only writers of `#NBLinkObjs`/`^LinkObj` are a public feature API
and the journal item stream. A face therefore receives an empty list on a normal save, and the surface
reference has to be in `SurfacicReps`, whose name means "surface representations".

The per-object framing chain is decompiled: `CATCGMStreamCGMImpl::Unserialize_Object` calls
`CreateObjectUnStream`, which reads a header with `CATMathStreamImpl::ReadHeaderObjectAt`
(`0x1800a56a0`, dispatching to `ReadHeaderObjectAt_V5R5` below version `0x3ef` or
`ReadHeaderObjectAt_SmallHeader` when flags `0x10001` are set), then reads the linked-object list,
then calls the object's `UnStream`. The small-header form starts with `0xa0..0xaf` and resolves a
type index through `CATCGMTypeByteIndexToShortValue`; no such anchored run exists in `Reservoir`.

The V5R5 header layout is decompiled: `ReadHeaderObjectAt_V5R5` consumes `0x15` bytes, requires
`0xb3` at header `+6` (or `+7` under the `0x20000` byte-order flag), and reads three 16-bit fields at
`+4`, `+8`, and `+0xc` that declare the object length and a trailing length. No combination of marker
offset, byte order, and length pair chains more than one header in `Reservoir`, so the corpus is on a
newer header path than V5R5.

The reference encoding is now recovered from the binaries, though the header offset is not. A face
takes its surface from the first entry of the linked-object list that the generic object header
passes in, and `CATCXFace::UnStream` then calls `SkipRemainingLinkedObjectsToRead`. The list is read
by `CATCGMStreamImpl::ReadListOfLinkedObjects`, which decodes a tag array with
`ReadRelativeTag` (`out[i] = base_tag - stored[i]`) and resolves each tag through the container's
virtual method at vtable offset `0xc0`. The container is `0x2b0(stream)` and the object table is
`0x2b8(stream)`. The tag difference itself is one byte: bit 0 selects an inline 6-bit difference or a
1-to-8-byte little-endian difference, and bit 1 selects `current - diff - 1` or `current + diff`.
`re/catia/tooling/TagDifference.py` implements and self-tests that decoder.

The adapter also writes a native `V5_CFV2` CATPart from a neutral `BrepModel` when
`WriteOptions(values={"native_brep": True})` is set.
The writer supports plane, cylinder, cone, sphere, and torus faces, and any number of loops per face.
It computes every count, length, offset, and directory entry from the neutral model.
A cylinder face is written as a 73-byte `0x33` surface record with the six-float carrier
(origin, axis, radius) in big-endian `f32`, and its trim record carries no vector because the
vector is a plane normal only. A cone is a 73-byte `0x34` record with the same six-float carrier
where the last value is the half angle, a sphere is a 65-byte `0x35` record with a four-float
carrier (center, radius), and a torus is a 77-byte `0x38` record with a seven-float carrier
(center, axis, major radius, minor radius).

A face with several loops is written as one trim record whose `counts[2]` is the loop count and
whose length array holds one length per loop, with the handles concatenated in loop order. The
reader's `Boundary` reconstructs one cycle per strip, so a two-loop face reads back as two loops.

## Usage

Read a native part:

```python
from convert import open_document

document = open_document("part.CATPart")
model = document.brep
```

Write a native B-rep part:

```python
from convert.adapters import WriteOptions
from convert.adapters.catia.Adapter import CatiaAdapter

result = CatiaAdapter().write(
    document,
    "part.CATPart",
    WriteOptions(values={"native_brep": True}),
)
```

## Limits

- The reader decodes 27 of 27 corpus parts. Five parts use a shared surface pool, and their
  face-to-surface map is inferred rather than decoded, so their geometry is approximate and they
  carry a `catia.brep.native_surface_map_heuristic` warning.
- Surface records in `SurfacicReps` are interleaved with curve records. The reader scans for the
  `00 33 <kind>` marker and validates each record instead of parsing contiguously, so the full
  surface pool is recovered for every part. The five pooled parts have fewer surfaces than faces,
  and the face-to-surface reuse map is not decoded. The pooling is entirely among non-planar faces:
  the planar face count equals the plane-surface count exactly in every pooled part (13/13, 66/66,
  91/91, 359/359, 359/359), and the deficit equals the non-planar face count minus the non-planar
  surface count. Planes are never shared; cylinders, cones, spheres, and tori are. The stream
  preambles carry payload lengths, not an object-header table, so the object table is built at load
  time.
- The handle-to-point map is not decoded. The reader's vertex positions are a structural
  approximation, so the decoded geometry is not the file's geometry even for the 22 parts that pass
  validation. The handle count exceeds the B-rep vertex count (`Reservoir` 1431 handles and 88
  vertices, `Copper_Washer` 76 handles and 8 vertices), so the handles are not vertex indices. The
  reader now places each handle by the corner structure: arity-2 handles get distinct vertex-table
  points by an augmenting-path match (a greedy match left `MC_Inlet` with 62 of 63 corners), 2-face
  handles are spread at equal angles along the intersection arc
  of their two faces (plane-cylinder, and plane-cone when the plane is perpendicular to the cone
  axis), and 1-face handles take the nearest satisfying vertex, falling back to the least violating
  vertex instead of the first vertex. The 2-face handles follow the stored
  edge order: `ArcOrder` finds the edge record whose handles contain the pair and reorders the arc
  handles to that order, so a clockwise arc no longer places its handles in handle-index order.
  That makes the planar faces coplanar
  for the simple parts (deviation drops from 1.0-34.5 to 0.0-0.0015) and puts all 76 `Copper_Washer`
  vertices on the washer's circles. The tessellation snap now uses the dominant cylinder's carrier
  origin, completes a partial decoded ring with `TessRing`, and refuses a snap that raises the
  surface violation by more than `1e-6`. That keeps all 76 `Copper_Washer` vertices on the 18°/22.5°
  grid and removes the `12.75`, `0.136`, and `1.5` plane deviations on `BRK_PRS_Sensor`, `Nut_M5`,
  and `Sensor_Connection`. The least violating fallback lowers the pooled-part plane
  deviation from 67.1/150.4/85.1/58.5 to 55.4/64.1/58.9/36.0 for `4784`, `4876`, `Pedal_Body`, and
  `Reservoir`. The angular positions are still assumed equal-spaced, not the
  stored tessellation. The coordinate region is a sequence of float runs
  separated by 1- to 8-byte record headers. The `Reservoir` five-float group is `(x, y1, z, y2, z)`
  with `z1 == z2`, but the `Copper_Washer` region does not follow that layout, and no run of plain
  three-float triples at the washer's radii exists anywhere in the stream, so the tessellation
  compression is not decoded. The 363-byte block before the first large run is a sparse bit array,
  not a compactor stream: the compactor decodes it
  to denormals and then `1e297`.
- The reader reconstructs plane and cylinder geometry from bounds and trim vectors.
- The reader does not decode feature records, sketches, dimensions,
  constraints, or relations. The corpus cannot validate such a decoder: all 27 parts carry the
  `FromCATPart` symbol and no part has a `Sketch`, `Pad`, `Pocket`, `Constraint`, `Dimension`,
  `Revolution`, `Groove`, `Chamfer`, `Fillet`, `Shaft`, `Hole`, `Pattern`, `Mirror`, `Extrude`, or
  `Revolve` symbol, so every part is an imported dumb solid with no parametric history to decode.
- The writer supports plane, cylinder, cone, sphere, and torus faces, and any number of loops per
  face. A cylinder or cone face needs a seam edge traversed in both directions to close its single
  loop, so the writer emits two distinct seam edges between the same vertex pair. The reader now
  reconstructs the stored loop directly from the trim length list when the trim has no triangle
  records and the lengths sum to the handle count, so a cylinder seam loop of ten handles round
  trips as one loop of ten coedges instead of collapsing to a four-coedge circle. The cylinder and
  cone writer round trips now produce nine edges and one ten-coedge seam loop, and both still
  validate with zero errors.
- The writer does not emit feature history, sketches, dimensions, or constraints.
- A pooled plane whose trim carries no vector falls back to `BoundsNormal`, which can only return an
  axis-aligned normal (`+X`, `+Y`, or `+Z`). A tilted plane's bounding box carries no normal
  information, so the pooled plane deviations of `36` to `96` cannot be reduced from the record
  alone: it needs the decoded map to know which faces are planes.
- Writer output is not byte-idempotent, and the difference is explained: a neutral model may declare
  more edges than the decoded form keeps (the box fixture declares 24, the reader returns 12), and
  `BuildSurf` writes one 11-byte curve record per edge, so a second write is 132 bytes smaller on the
  box (`SurfacicReps` `631` -> `499`) and 11 bytes smaller on the cylinder. `MainDataStream` is
  byte-identical at `444` for the box. The geometry and the validation result are unchanged; only the
  edge count differs, because the reader normalises coedge pairs to one edge.
- The three `30 04 04 fd ff` records are now measured instead of assumed constant. `r0` (span 47) and
  `r1` (span 52) share a layout: `00 00 00 01`, one zero byte, five `f32`, a `u32` kind that is `3`
  and `19` respectively in all 27 parts, and a constant 13-byte tail; `r1` adds `95 ff <u16> 00 00 00`.
  The `u16` equals `(MainDataStream length - 199) mod 65536` for 26 of 27 parts (`Pedal_Body` is off by
  `340`). The five floats vary per part and match no model metric (only `Reservoir` and `Washer_8`
  happen to have the z half-extent as the fifth float). `re/catia/tooling/FdRecords.py` dumps and
  checks them, so a vendor-saved comparison is one command away.
- The writer's `MainDataStream` is not structurally identical to a vendor stream, and the difference is
  now measured by parsed structure rather than raw byte counts: the writer's box emits one vertex table
  with eight rows and eight roster rows, matching the vendor convention of one roster row per vertex
  (`Washer_8` 8/8, `Nut_M6` 40/40, `Banjo` 50/50), and its per-face `30 04 04 ff ff` blocks match. The
  remaining known gap is that it emits none of the three `30 04 04 fd ff` records. An earlier version
  of this note claimed the writer also emitted no roster rows; that was a raw `0x54` byte count, not a
  roster count, and it was wrong.
- The writer reports `vendor_loadable=False` and `application_usable=False`.
- No alternative vendor checker exists either. SOLIDWORKS is installed
  (`C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe`, plus eDrawings, Composer, and Flow
  Simulation), but `SLDWORKS.exe` exits like `CNEXT.exe` and `SldWorks.Application` is not registered
  in COM (`HKCR\SldWorks.Application\CLSID` is absent), so SolidWorks 3D Interconnect cannot be used to
  open the writer's CATPart as an independent check.
- The vendor blocker is a missing licence configuration, verified in the Parallels VM: CATIA
  V5-6R2022 is installed (`CNEXT.exe` and
  `C:\ProgramData\DassaultSystemes\CATEnv\CATIA_P3.V5-6R2022.B32.txt` are present), but there is no
  `DSLicSrv.txt` next to `CNEXT.exe`, no `C:\ProgramData\Dassault Systemes\Licenses` directory, and no
  licence line in the environment file, and launching `CNEXT.exe -direnv ...` leaves no process
  running. Supplying a `DSLicSrv.txt` with the licence server, or setting `DSLICENSESERV`, is the
  single prerequisite for the vendor checks.
- CATIA acceptance is not measured because the local CATIA install has no license.

## Verification

- `re/catia/tooling/ParseBrep.py` decodes 22 of 27 parts with the exact map and 27 of 27 with the
  inferred map.
- `re/catia/tooling/BuildModel.py` validates every decoded model with zero errors.
- The marker scan returns exactly the face count for all 22 exact parts and the full surface pool
  for the five pooled parts: 270, 714, 714, 314, and 56 records for `4784`, `4876`, `4876_1`,
  `Pedal_Body`, and `Reservoir`.
- The inferred map decodes all five pooled parts: 71, 338, 416, 870, and 870 faces, each with a
  matching surface list and zero validation errors. The heuristic warning is present on exactly
  those five parts.
- `re/catia/tooling/Scorecard.py` measures every part against its own geometry: the worst distance
  from a face's vertices to that face's surface, and how many faces exceed `1e-3`. All 22 exact parts
  report `0` bad faces with a worst distance of `0.0000` (`0.0009` for the two `Nut_ISO_7040-M6`
  files). The five inferred parts report bad faces `227/416` and worst `66.04` for `4784`,
  `529/870` and `93.45` for `4876`/`4876_1`, `186/338` and `96.34` for `Pedal_Body`, and `22/71` and
  `36.00` for `Reservoir`. The scorecard also prints `V - E + F`, which is negative for every part
  because the decoded edges are tessellation polylines rather than B-rep edges.
- The map refinement lowers the unsatisfied handles from 209/1431 to 181/1431 on `Reservoir` and
  from 1923/2666 to 792/2666 on `Pedal_Body`. `4784`, `4876`, and `4876_1` keep the single-pass
  map because refinement is skipped above 400 faces.
- A plain surface index table is ruled out: every stream of `Reservoir` was scanned for a run of
  `FaceCount` 8-bit or 16-bit little-endian values below the pool size covering at least 85% of the
  pool, and none exists.
- A six-face box emitted by the writer reads back as six faces, twelve edges, and eight vertices
  with zero validation errors.
- A three-face cylinder (two planes and one cylinder) emitted by the writer reads back as three
  faces, eight edges, and eight vertices, with one `CylinderSurface` of radius 2.5 and axis `+z`,
  and zero validation errors.
- A three-face truncated cone (two planes and one cone) emitted by the writer reads back as three
  faces, eight edges, and eight vertices, with one `ConeSurface` of half angle `atan(1.0)`, and zero
  validation errors.
- A one-face two-loop model emitted by the writer reads back as one face with two loops, six edges,
  and six vertices, and zero validation errors.
- A three-face model whose curved surface is a torus emitted by the writer reads back with one
  `TorusSurface` of major radius 3.0, minor radius 0.75, and axis `+z`, with zero validation errors.
- A three-face model whose curved surface is a sphere emitted by the writer reads back with one
  `SphereSurface` of radius 2.5, with zero validation errors.
- `TestHeldOut` decodes the five vendor parametric samples in `re/catia/examples/parametric/` — files
  that were never used to build the B-rep reader — and asserts zero validation errors plus no face
  vertex more than `1e-3` off its plane or cylinder. All five pass with a worst distance of `0.0000`
  and zero bad faces: `23` faces (`ISO_10642`), `21` (`ISO_1207`), `22` (`ISO_2010`, inferred map),
  `8` (`ISO_2338`), and `8` (`ISO_7089`). That is held-out generalisation evidence for the reader,
  and it also shows that the inferred map can be geometrically consistent even when it is not the
  stored map (`ISO_2010` has zero bad faces and still carries the warning).
- `TestScore` runs the scorecard over all 27 corpus parts inside the suite: every exact part must have
  zero faces whose vertices are more than `1e-3` off the face surface, and every inferred part must
  have at least one. That pins the 22 exact parts against regression in CI.
- `tests/convert/catia/CatiaNativeTests.py` covers the corpus reader, the box writer round trip, the
  cylinder writer round trip, the cone writer round trip, the torus writer round trip, the sphere
  writer round trip, and the two-loop writer round trip.
- The OSMX reader accepts a symbol table section that ends before the stream does, which is what a
  `CATProduct` product-structure stream looks like (`OSMX` at offset `176` of `3976` bytes in
  `Tilton_Set.CATProduct`, `280` of `31384` in `Brake_Pedal_Assembly - Backup 1.CATProduct`). Before
  the change all three product files raised `OSMX symbol table length is inconsistent`; after it they
  parse `42`, `104`, and `41` symbols including `ASMPRODUCT`, `_PartNumber`, `_Component`, `_Source`,
  and `_RepresentedBy`, and the 27 `CATPart` files still decode unchanged with the same five warnings.
  The assembly instance list itself is not extracted yet: those attributes do not appear in the
  product stream's `7c 07` blocks, so the tree is encoded in the `CATProdCont` payload.
- The roster is one row per B-rep vertex, measured on all 27 corpus parts (`ParseRoster` row count
  equals `ParseBrep(...).vertices` length). The writer honours the same rule, so its box output has
  eight vertex rows and eight roster rows. `TestRoster` asserts the invariant over the corpus.
- A new `src/convert/adapters/catia/Parametric.py` reads the parametric side of a `CATPart`: it walks
  the OSMX `7c` record tree, decodes each `7c 07` attribute block with the compact-int table, and
  exposes `RelationNames` (the `#In` inputs of every relation formula) and `AttributeValues` (every
  attribute with its decoded values). Measured: all five vendor parametric samples declare exactly one
  relation input, `LENGTH`; `ISO_1207` names `d_dia`, `dk_nom_head_dia`, and `n_nom_Slot_Width`, and
  the attribute blocks carry an integer id plus a reference and never a double, while the doubles live
  in separate `MAvalue` objects. The washer's symbol table has no `d_dia`, `d1`, `d2`, or `h`, so the
  ISO 7089 name-to-value map cannot be built from the file itself. `TestParamName` asserts all of this
  over the five samples.
- The OSMX symbol table reader now handles the extended length form (a zero length byte followed by
  a little-endian u32 length) and allows `\t`, `\n`, and `\r` in symbol values. The 27 corpus parts
  still decode with zero symbol-table failures, and the five parametric sample parts in
  `re/catia/examples/parametric/` decode 234 to 328 symbols each.
- `re/catia/tooling/Parametric.py` classifies 27 corpus parts as `dumb` and the five sample parts as
  `parametric`, and reports the feature vocabulary (`2DLine`, `2DCircle`, `2DPoint`, `Constraints`,
  `ConstraintDYS`, `EdgeFillet`, `Chamfer`, `CircPattern`, and their parameter names).
- `re/catia/tooling/OsmGraph.py` walks the OSMX `7c` record tree and parses the `7c 07` attribute
  blocks. It recovers 292 to 1410 attributes with 130 to 137 distinct names from the five parametric
  sample parts (`Pocket`, `Shaft`, `EndLimit`, `StartLimit`, `Profile`, `Direction`, `FirstAngle`,
  `SecondAngle`, `d_dia`, `p_pitch`, `n_nom_Slot_Width`, `ConstraintDYS`, `SketchSupport`,
  `AbsoluteAxis`), and 69 attributes with 33 distinct part-property names from the 27 corpus parts.
  `Pedal_Body` recovers attributes with 72 distinct names because it carries GSM point features.
- The literal parameter values are `0xe6` doubles (eight little-endian bytes). The extractor recovers
  `0.8`, `2.5`, `5.0`, `8.0`, `15.0`, `50.0` from `ISO_2338_PARALLEL_PIN` (the pin diameter, length,
  and chamfer), `4.2`, `5.0`, `8.4`, `16.0`, `19.0`, `37.5` from the washer, and `360.0`, `90.0`,
  `20.0` from the screws. The value extraction is exact; the attribute-name association is not yet
  exact because the `7c 07` key byte and the `7c 06` header key list do not line up one-to-one.
- The non-double attribute values are compact integers decoded from `CATBmxStream::ReadInt`
  (`CATOmx.dll` `0x1800016e0`): `0x80` escapes to a four-byte `i32`, `0x81..0xd0` is a one-byte
  value `byte - 0x81`, and `0xd1..0xe4` is a two-byte value `(byte - 0xd1) << 8 | next`. The callers
  pass `Min = 0x80`, `Max = 0x51`, and `Extra = 0x14`. Re-decoding the parametric parts with this
  table classifies 463 ints, 218 three-byte references, 140 four-byte references, and 3 doubles per
  part, leaving 116 unrecognised bytes out of about 900 values.
- Values are grouped by owning object: the `ea <u32>` field of the child `7c 06` header gives the
  object id, so `ISO_7089` objects `22`, `23`, and `24` hold `8.4`, `16.0`, and `1.6`, and
  `ISO_2338` object `52` holds `50.0` and object `75` holds `0.8`. The objects that carry a value
  also carry an attribute named `MAvalue`.
- The twelve out-of-range blocks are early attributes, not a key-encoding problem: their keys
  `0xef..0xfd` sit above every compact-int range (`0x80` escape, `0x81..0xd0`, `0xd1..0xe4`), so the
  compact reading is refuted for them, and no constant index shift fits better than coincidence
  (`11/12` at shift `38`, `12/13` at shift `19`, both part-specific).
- The attribute key is a single symbol byte: walking the blocks with that rule closes 1011 of 1023
  blocks across the five parametric parts with every key inside the local symbol table
  (362/362, 243/243, 246/246, 80/88, 80/84). The 12 exceptions are a distinct id-keyed variant
  whose keys are consecutive integers `239..253` and whose entries carry only an int and a
  reference, no double.

## Related information

- [CATIA adapter](../Reference/Adapters/Catia.md)
- [CATIA B-rep findings](../../re/catia/Brep.md)
- [CATIA feature graph findings](../../re/catia/FeatureGraph.md)
- [CATIA tessellation findings](../../re/catia/Tessellation.md)
- [CATIA measurements](../../re/catia/Measurements.md)
