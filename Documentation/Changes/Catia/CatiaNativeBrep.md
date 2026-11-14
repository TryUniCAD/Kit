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
makes the planar faces coplanar for the simple parts. It is still a structural approximation, not
the native B-rep topology or geometry, because the angular positions are assumed equal-spaced, not
the stored tessellation.

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
The reader still requires the two counts to match, because the face-to-surface reference is not
decoded and planarity does not determine it.

The adapter also writes a native `V5_CFV2` CATPart from a neutral `BrepModel` when
`WriteOptions(values={"native_brep": True})` is set.
The writer supports plane faces with one loop per face.
It computes every count, length, offset, and directory entry from the neutral model.

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

- The reader decodes 22 of 27 corpus parts. Five parts use a shared surface pool or an unsupported layout.
- Surface records in `SurfacicReps` are interleaved with curve records. The reader scans for the
  `00 33 <kind>` marker and validates each record instead of parsing contiguously, so the full
  surface pool is recovered for every part. The five failing parts still fail because they have
  fewer surfaces than faces and the face-to-surface reuse map is not decoded.
- The handle-to-point map is not decoded. The reader's vertex positions are a structural
  approximation, so the decoded geometry is not the file's geometry even for the 22 parts that pass
  validation. The handle count exceeds the B-rep vertex count (`Reservoir` 1431 handles and 88
  vertices, `Copper_Washer` 76 handles and 8 vertices), so the handles are not vertex indices. The
  reader now places each handle by the corner structure: arity-2 handles get distinct vertex-table
  points by a bipartite match, 2-face handles are spread at equal angles along the intersection arc
  of their two faces (plane-cylinder, and plane-cone when the plane is perpendicular to the cone
  axis), and 1-face handles take the nearest satisfying vertex. That makes the planar faces coplanar
  for the simple parts (deviation drops from 1.0-34.5 to 0.0-0.0015) and puts all 76 `Copper_Washer`
  vertices on the washer's circles, and all 4682 handles across the 22 decoded parts satisfy every
  surface of the faces that use them. The angular positions are still assumed equal-spaced, not the
  stored tessellation. The coordinate region is a sequence of float runs
  separated by 1- to 8-byte record headers. The `Reservoir` five-float group is `(x, y1, z, y2, z)`
  with `z1 == z2`, but the `Copper_Washer` region does not follow that layout, and no run of plain
  three-float triples at the washer's radii exists anywhere in the stream, so the tessellation
  compression is not decoded. The 363-byte block before the first large run is a sparse bit array,
  not a compactor stream: the compactor decodes it
  to denormals and then `1e297`.
- The reader reconstructs plane and cylinder geometry from bounds and trim vectors.
- The reader does not decode feature records, sketches, dimensions,
  constraints, or relations.
- The writer supports plane faces with one loop per face.
- The writer does not emit feature history, sketches, dimensions, or constraints.
- The writer reports `vendor_loadable=False` and `application_usable=False`.
- CATIA acceptance is not measured because the local CATIA install has no license.

## Verification

- `re/catia/tooling/ParseBrep.py` decodes 22 of 27 parts.
- `re/catia/tooling/BuildModel.py` validates every decoded model with zero errors.
- The marker scan returns exactly the face count for all 22 passing parts and the full surface pool
  for the five failing parts: 270, 714, 714, 314, and 56 records for `4784`, `4876`, `4876_1`,
  `Pedal_Body`, and `Reservoir`.
- A six-face box emitted by the writer reads back as six faces, twelve edges, and eight vertices
  with zero validation errors.
- `tests/convert/catia/CatiaNativeTests.py` covers the corpus reader and the writer round trip.

## Related information

- [CATIA adapter](../Reference/Adapters/Catia.md)
- [CATIA B-rep findings](../../re/catia/Brep.md)
- [CATIA tessellation findings](../../re/catia/Tessellation.md)
- [CATIA measurements](../../re/catia/Measurements.md)
