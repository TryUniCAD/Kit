# CATIA V5 native B-rep

## Scope

This page describes the standard nested B-rep layout used by 22 of the 27 parts in
`re/catia/examples/.CATPart`. The two `4876` parts use a different layout and are recorded as
unsupported.

## `MainDataStream` spine

The spine is the largest contiguous run of 8-byte rows:

```text
30 04 04 ff ff e1 e1 e1
```

`b0` replaces `30` in the form flag. The run length is the face count. The four payload bytes are
constant in the corpus and carry no per-face tag.

After the run:

```text
count_header := 01 <kind> <count:u8> | 01 <kind> ff <count:u32le>
edge_row     := 02 <arity:u8> <handle[arity]>
delimiter    := 10 24 04 ff ff 00 00 00
vertex_table := 01 06 <count> (05 08 01 <x:f32le> <y:f32le> <z:f32le>){count}
```

The edge handle width is one, two, or three bytes, big-endian. The width is selected by the first
width that parses the complete edge table, delimiter, vertex table, and trim chain. The corpus uses
width 1 for compact parts and width 2 for full-form parts.

## Trim packets

Each face has one trim packet before the FBB run:

```text
01 <kind>
[count(A)] [count(B)] [count(C)]
ff <N:u32le>
[3 x f32le vector if kind & 0x08]
K[0:B+C] each count()
H[0:N] handles, width-selected, big-endian
```

`kind` is `0x40 | mask`. Mask bit 0 is independent triangles, bit 1 is strips, bit 2 is fans, and
bit 3 is a face-frame vector. `N == 3*A + sum(K)`.

The trim packet is an indexed triangle mesh. The face boundary is recovered by cancelling opposite
directed edges. The remaining directed edges form closed cycles. Cycle count is loop count.

The trim section does not start at offset zero. The corpus contains false `01 4x` signatures in the
preamble. The parser walks backwards from the FBB offset and accepts the chain of exactly one packet
per face.

## `SurfacicReps` records

The stream starts with a 17-byte header:

```text
ff <payload_length:u24le> 00 <reference:f32le> <scale:f32le> 00 <float_count:u16le> 00
```

The corpus reference is `0.785398` and the scale is `1e12`. The float count is the number of floats
in the compressed carrier-parameter lane.

Surface records start at offset 17:

| Kind | Meaning | Record length | Carrier scalars | Bounds offset |
| --- | --- | ---: | ---: | ---: |
| `0x32` | plane | 49 | 0 | +8 |
| `0x33` | cylinder | 73 | 6 | +32 |
| `0x34` | cone | 73 | 6 | +32 |
| `0x35` | sphere | 65 | 4 | +24 |
| `0x38` | torus | 77 | 7 | +36 |

Each record has a two-byte parameter length, `00 33`, the kind byte, the carrier scalars, ten
little-endian `f32` bounds, one orientation byte, and three trailing bytes. The trailing bytes are
part of the record length. A parser that stops at the orientation byte desynchronises on the next
record.

The ten bounds are:

```text
AABB center[3], AABB half extent[3], bounding sphere center[3], bounding sphere radius
```

Plane and cylinder geometry is reconstructed from the bounds and the trim vector. The carrier
scalars are compressed with `CATFloatCompactor`; the exact compressor is not yet implemented.

## Curve rows and vertex roster

After the surface records:

```text
line:   60 <tag:u24le> 00 02 00 33 36 <face_ref> <face_ref>
circle: 60 <tag:u24le> 00 12 00 33 37 <cx:f32be> <cy:f32be> <cz:f32be> <r:f32be> <face_ref> <face_ref>
spline: 60 <tag:u24le> 00 00 00 <face_ref> <face_ref>
```

`face_ref` is one byte, or `ff <u32le>` when widened.

The stream ends with a trailing roster of 7-byte rows:

```text
54 <tag:u24le> 00 00 00
```

The roster is found from the end of the stream. A forward scan finds false `54` bytes inside
surface and curve payloads.

## Neutral model

The reader maps the spine to `BrepModel`:

| Native | Neutral |
| --- | --- |
| FBB row | `BrepFace` |
| trim boundary cycle | `BrepLoop` and `BrepCoedge` |
| edge table row | `BrepEdge` |
| `05 08 01` row | `BrepVertex` |
| plane record | `PlaneSurface` |
| cylinder record | `CylinderSurface` |
| other surface record | `NativeSurface` with raw bytes |

The reader creates one shell, one region, and one body. The body id is `catia:body:1`.

## Surface record layout

The record length decomposes as `5 + carrier + 40 + 1 + 3`:

| Kind | Length | Carrier bytes |
| --- | ---: | ---: |
| plane `0x32` | 49 | 0 |
| cylinder `0x33` | 73 | 24 |
| cone `0x34` | 73 | 24 |
| sphere `0x35` | 65 | 16 |
| torus `0x38` | 77 | 28 |

The five-byte header is `00 <carrier:u8> 00 33 <kind>`. The carrier bytes are plain big-endian
`f32` parameters, not `CATFloatCompactor` output. The next 40 bytes are ten little-endian `f32`
bounds. The orientation byte follows, then three padding bytes.

Carrier layout:

| Kind | Carrier | Fields |
| --- | ---: | --- |
| plane `0x32` | 0 | normal comes from the trim vector or the bounds |
| cylinder `0x33` | 6 | origin[3], axis[2], radius |
| cone `0x34` | 6 | origin[3], axis[2], half-angle |
| sphere `0x35` | 4 | center[3], radius |
| torus `0x38` | 7 | center[3], axis[2], major radius, minor radius |

The axis is `(ax, ay, sqrt(1 - ax*ax - ay*ay))`. A negative radius, half-angle, or major radius
means the surface is oriented inward; the reader uses the absolute value.

Verified on `Washer_8.CATPart`: outer cylinders `origin=(0,0,0.8)`, `axis=(0,0,1)`, `radius=7.5`;
inner cylinders `radius=4.2`. On `Bolt_M5x40.CATPart`: cylinder `radius=2.5`, torus
`major=2.7 minor=0.2`, cone `half-angle=0.7854`.

## Surface trailing handle

Each surface record ends with `ff <lo> <hi> 00` or `01 <lo> <hi> 00`. The 16-bit value
`<hi><lo>` increases monotonically across the 24 `Pedal_Body` surfaces:

```text
0xa60c 0xa60f 0xa618 0xa61e 0xa627 0xa62d 0xa630 0xa649
0xa706 0xa70c 0xa715 0xa724 0xa736 0xa73f 0xa748 0xa751
0xa75a 0xa763 0xa769 0xa76c 0xa775 0xa77b 0xa781 0xa78a
```

The span is 382, while the part has 338 faces. The value is a candidate face-range handle, but
the mapping is not confirmed. The handles do not appear in `MainDataStream`.

`Reservoir.CATPart` has two plane surfaces and 71 faces. Its trailing handles are `0x0be7` and
`0x0c3c`, a span of 85. The span does not match the face count (71), the loop count, the coedge
count (3438 for `Pedal_Body`), or the vertex count (424 for `Pedal_Body`, 88 for `Reservoir`).
The trailing handle is therefore not a simple face, loop, coedge, or vertex index.

The trim vector is the surface axis for cylinders, cones, and tori, and the normal for planes.
`Pedal_Body` has 66 faces with a vector; 32 match a carrier axis and 34 are plane normals. The
assignment is not contiguous in trim order, so a single vector match does not identify the
surface when several surfaces share an axis.

## Per-face table search

`MainDataStream` for `Pedal_Body` was scanned for a 338-entry table of surface or face indices.
No table exists for any of these encodings:

| Encoding | Limit | Hits |
| --- | ---: | ---: |
| `u8` | `< 24` | 0 |
| `u16` | `< 24` | 0 |
| `u32` | `< 24` | 0 |
| `u16` | `< 338` | 0 |
| `u32` | `< 338` | 0 |

The head region `0..29364` has a longest plausible `f32` run of 64 (little-endian) or 90
(big-endian), far short of the 2666 tessellation points. The `SurfacicReps` tail has a longest
run of 47. The tessellation coordinates are therefore compressed, not plain floats.

## `SurfacicReps` is the B-rep surface table, and its records are interleaved

`SurfacicReps` carries the analytic B-rep surface records. The earlier hypothesis that it is only a
visualization table is wrong, and the data disproves it.

Each surface record is a plane, cylinder, cone, sphere, or torus with a carrier and ten bounds
floats. For 22 of the 27 corpus parts the number of these records equals the face count exactly.
That is not a coincidence across 22 parts: the records are per-face B-rep surfaces.

The five failing parts are not a wrong-stream problem. They are a parsing problem plus a missing
face-to-surface map.

The parsing problem is that surface records are interleaved with curve records. A contiguous parse
from offset 17 stops at the first curve record, so the reader saw only 4, 1, 1, 24, and 2 surfaces
for `4784`, `4876`, `4876_1`, `Pedal_Body`, and `Reservoir`. Scanning for the `00 33 <kind>` marker
and validating each record recovers the full pool: 270, 714, 714, 314, and 56 records. Every marker
parses, every sign byte is `+1` or `-1`, every bound is finite, and no record overlaps another. The
same scan returns exactly the face count for all 22 passing parts, including
`Brake_bias_90_degree_coupler`, where a naive marker count over-counts by one and the strict filter
removes the false positive.

The remaining problem is that the five failing parts have fewer surfaces than faces, so several
faces share one surface. The face-to-surface map is not a plain array. No 71-value window in
`Reservoir` `MainDataStream` or `SurfacicReps` is a surjective map onto the 56 surface indices, in
`u8`, `u16` little-endian, or `u16` big-endian form. The surface record header is a carrier byte
count (2 for planes, 26 for cylinders and cones, 30 for spheres and torus), not a face index. The
trim records carry no surface index. The FBB face rows are byte-identical, so they cannot carry one
either.

The vendor symbols are consistent with the stream being consumed by the visualization pipeline:
`CATViz.dll` exports `CATSurfacicRep::CATSurfacicRep`, `CATRepMapping::DecodeSurfacicRep`,
`CAT3DRep::UnStream`, and `CATVizSurfacicRepProxy`, and `CATViz.dll` and `PLNExtractCGR.dll` are
the only installed modules that reference the literal `MainDataStream` string. That does not make
the stream visualization-only; the analytic surface records and the exact face-count match show it
carries the B-rep surface data.

The `SurfacicReps` header field at offset 14 is not the first curve-row offset. Measured values are
403 (`Copper_Washer`, first curve 404), 459 (`Washer_8`, first curve 404), 1097 (`Bolt_M5x40`,
first curve 1594), and 2964 (`Reservoir`, first curve 4539). It is not a byte offset into the curve
rows, and it is not the end of the surface-record region.

The region `12376..18807` of `Reservoir` `MainDataStream` is not a length-prefixed record table:
reading it as `<u8 type> <u8 flag> <u32 len> <payload>` yields a 2850-byte first record and then a
zero-length record, and the bytes at `15232` are high-entropy bit-packed data, not a record header.
Only `Reservoir` contains a `42 ff` record at all, so it is not a shared B-rep surface table.

### Face-to-surface map: negative results

`Reservoir` has 71 faces and 56 surfaces, so 15 faces share a surface with another face. The map
was searched for as a plain array and not found. Every test below is a negative result.

- No 71-value window in `MainDataStream` or `SurfacicReps` is a surjective map onto `0..55` in
  `u8`, `u16` little-endian, `u16` big-endian, `u32` little-endian, or `u32` big-endian form.
- No 71-value `u8` window with stride 1, 2, 3, 4, 6, or 8 is such a map.
- No 71-value window with values in `1..56` and at least 40 distinct values exists in either stream.
- The surface record header is a carrier byte count: 2 for planes, 26 for cylinders and cones, 30
  for spheres and torus. It is not a face index.
- The trim record carries no surface index. Its `kind` bits select which of three counts and the
  optional vector are present, and the counts sum to 348, 273, and 30 over the 71 trims, which
  matches neither the 150 edges nor the 88 vertices.
- The FBB face rows are byte-identical (`30 04 04 ff ff e1 e1 e1`), so they cannot carry a
  per-face surface index.
- The surface record's three-byte tail is monotonically increasing (3047..4543) and points into
  float data in `MainDataStream`, not at a surface offset, a record end, or a curve-row start.
- The 78 curve rows start at 4539 and all carry tag `0x60`. They are not addressed by the surface
  tails.
- `CATFace` is exported only by `CATPartDesignFeature.dll`, and that module exports no
  `CATFace::UnStream`. `CATTopologicalObjectsCGM.dll` exports no face unstream either, so the
  face record layout cannot be read from the export tables alone.
- The `CATFace` strings in `CATTopologicalObjectsCGM.dll` are fragments of the export name table,
  not a registered class name. No pointer to them exists in the image, so the meta class cannot be
  located from the string.

### The deficit is entirely in the non-planar faces

`Reservoir` decomposes cleanly by surface kind.

- 13 trims carry a non-zero vector and 58 carry no vector.
- The surface pool has 13 planes and 43 non-plane surfaces (23 cylinders, 9 cones, 11 torus).
- So the 13 planar faces map one-to-one onto the 13 planes, and the 58 non-planar faces share the
  43 non-plane surfaces. The 15-face deficit is exactly `58 - 43`.

The plane surface record does not store its normal. The bounds are an axis-aligned box, and the
normal is the axis with the smallest extent. That matches the trim vector for axis-aligned planes
(`surf 7` and `surf 51` both give `(0, 1, 0)`), but it fails for the tilted face whose trim vector
is `(-0.5736, 0, -0.8192)`, because a tilted plane's axis-aligned box has three non-zero extents.
The face's trim vector is therefore the authoritative normal, and the surface record is incomplete
without the face that uses it.

The 78 curve records each carry two face references in their last two bytes (for example
`(2, 0)`, `(3, 0)`, `(5, 2)` in `Copper_Washer`), so the curve table gives edge-to-face adjacency.
It does not give a surface reference, so it cannot be used to build the face-to-surface map
directly.

### The surface tail is a tag, and the tag space is shared with curves

`Copper_Washer` has five readable surface tails, `445, 449, 476, 495, 499`, and eight curve tags,
`428, 444, 447, 448, 452, 475, 479, 494`. The two sets interleave in one ascending sequence, so the
tail is a tag in a shared object-tag space, not a byte offset.

The surface tags do not appear anywhere in `MainDataStream` as `u16` little-endian, `u16`
big-endian, `u24` little-endian, or `u32` little-endian. No 71-value window in `MainDataStream`
holds tags in `400..500` in any of those encodings. So the face record does not reference the
surface by tag in the B-rep stream.

The three body headers in `Reservoir` carry counts `3`, `19`, and `4140`. Those are neither the 71
faces nor the 56 surfaces, so the surface pool is not partitioned per body by that field.

The tessellation coordinate table starts at 569 with 18 five-float records of the form
`(x, y1, z, y2, z)` and switches at 929 to three-float records `(x, y, z)`. The trim handles reach
1430 while the table holds roughly 990 points, so the handles do not index the table directly.

A disassembly search of `CATGeometricObjectsCGM.dll` for a surface-kind dispatch found no
`cmp $0x33` or `cmp $0x38`; the only `cmp $0x32` is in unrelated code. The surface reader does not
dispatch on the kind byte with a simple compare chain, so the face record cannot be located by
following the surface reader's callers from a constant.

### The face stores its surface as a linked object

`CATTopologicalObjects.dll` exports the face stream functions:

| Symbol | RVA |
| --- | ---: |
| `CATCXFace::Stream` | `0x54eba0` |
| `CATCXFace::StreamV2R0` | `0x54ed60` |
| `CATCXFace::UnStream` | `0x54eef0` |
| `CATCXFace::UnStreamV2R0` | `0x54f110` |

`StreamV2R0` calls `CATCGMStreamImpl::WriteLinkedObjectsCount(face, 2)` and then
`CATCGMStreamImpl::WriteObject(support, face)`, where `support` is the face's surface obtained
through the face vtable at offset `0x400`. So the face record begins with a linked-object count of
two and then a reference to the surface. The second linked object is read after the surface.

This rules out the FBB row as the face record. The 71 FBB rows are byte-identical, so they cannot
carry a per-face surface reference. The face record with the surface reference must be a different
record, and the trim record that precedes the FBB run carries no surface field.

The linked-object reference is written by `CATCGMStreamImpl::WriteObject` and read by
`CATCGMStream::ReadObject`. The reference encoding is not a plain tag in `MainDataStream`: the
surface tags do not appear there in any of the four integer encodings tested. The reference is
therefore resolved through the stream's object table, which is not the `SurfacicReps` surface
record order.

### The object reference is a scalable tag difference

`CATCGMStreamImpl::WriteObject` at `0x72970` reads the object tag from offset `0x70` and writes it
with `CATMathStreamImpl::WriteTagDifferenceAsCATULONG64_Scalable` at `0xb8ed0`. The read side is
`CATMathStreamImpl::ReadTagDifferenceAsLONG64_Scalable` at `0xb8480`.

The encoding is a variable-length signed delta:

- one byte when the delta is at most 63: `(delta << 2) | sign | 1`, where `sign` is `2` for a
  negative delta and `0` for a positive one, and bit 0 is always set;
- otherwise the first byte is `(n << 2) | sign` with `n` in `1..8`, followed by `n` bytes of
  magnitude.

So a reference is a *difference* from the previous tag in the stream, not an absolute tag. That is
why the absolute surface tags do not appear in `MainDataStream`.

The FBB row `30 04 04 ff ff e1 e1 e1` is not a sequence of tag differences. Its first byte `0x30`
has bit 0 clear and `0x30 >> 2 = 12`, which is outside the valid `1..8` length range, so the row
cannot start a tag-difference sequence. The row is a fixed flag record, not the face record that
carries the surface reference.

### The shell record carries index arrays, and the face surface is list slot 2

The `.pdata` exception directory gives the real function boundaries, which the export table does
not. `CATCXFace::UnStream` is `0x54eef0..0x54f10a` split into six `.pdata` regions, and
`CATCXFace::UnStreamV2R0` is `0x54f110..0x54f212`. The function at `0x54f220` is a separate write
function, not part of the unstream.

`CATCXShell::UnStream` at `0x5540a0..0x554a19` reads a boolean, three `u32` scalars, three `u32`
arrays, and a tag resolved with `CATCGMContainer::FindObjectFromTag`. It then loops over the first
array and, for each entry, takes `list[index + 1]` from the linked-object list, resolves it with
`GetImplementCXFace`, and adds it to the shell. So the shell record stores *indices into the
linked-object list*, not tags.

`CATCXFace::UnStream` takes the same linked-object list and uses slot 2 as the face's surface: it
calls `list[2]`, checks the `0x6000002` interface, and stores the result as the face support. Slot
1 is read first and is a different object. So the face's surface is the third entry of the face's
own linked-object list.

The face unstream is vtable slot 27 (offset `0xd8`) of the `CATCXFace` vtable at `0xbc7b18`. The
caller that populates the face's linked-object list is the remaining unknown: the shell unstream
does not call it, and the body unstream reads only scalars and a byte count.

### The face record field order

`CATCXFace::StreamV2R0` at `0x54ed60..0x54eee6` writes the face record in this order:

1. `WriteLinkedObjectsCount(face, 2)`, which writes a plain `u32` count of 2 through
   `CATMathStreamImpl::WriteULong`;
2. `WriteObject(support, face)`, the surface reference as a scalable tag difference;
3. `WriteObject(second, face)`, a second reference as a scalable tag difference;
4. `WriteShort(0xb0(face))`, a `u16`;
5. one more call through `0x180b792c0`;
6. `WriteUChar`, a single byte.

So a face record is at least nine bytes and variable-length, because the two tag differences are
variable-length. The FBB row is eight bytes and identical for all faces, so it cannot be the face
record.

The face record is also not `02 00 00 00` followed by a tag difference. `Reservoir`
`MainDataStream` contains only three occurrences of `02 00 00 00`, at offsets 37, 47, and 18110,
not 71. So the count is not written as a plain `u32` at the start of each face record in that
stream, and the face records are not laid out as a simple sequence there.

### The shell record holds the face references, not the face records

`CATCXShell::Stream` at `0x553640..0x553dd6` writes, in order:

1. `WriteLinkedObjectsCount(shell, n)`;
2. `WriteObject(body, shell)`;
3. `WriteBoolean`;
4. three `WriteULong` scalars;
5. three `WriteULong` arrays;
6. `WriteLinkedObjectsCount(shell, face_count)`;
7. a loop of `WriteObject(face, shell)`, one per face;
8. two `WriteUChar` and two `WriteShort`.

So the shell record stores the *face references* as scalable tag differences, not the face records
themselves. `CATCXBody::Stream` at `0x541d60..0x541eb7` writes the domain count, one
`WriteObject(domain, body)`, a `WriteLong`, and a `WriteShort`. Neither function writes the face
record body.

The face record is written when the face object is first emitted, which is the first
`WriteObject(face, shell)` in the shell loop. The face record body follows that reference. So the
face record is inline in the shell record, at the first face reference, and the remaining face
references are tag differences only.

`SurfacicReps` contains no `02 00 00 00` at all, so the face records are not in that stream either.

### The body header is 30 bytes and its count is not a face count

`Reservoir` has three body records at offsets 54, 101, and 153. They are 47, 52, and 53 bytes long,
not a fixed size. Each starts with the same 30-byte object header:

```
30 04 04 fd ff 00 00 00 01 00 62 d6 3c 42 00 00 00 00 00 00 d8 c0 95 63 37 3d 00 00 f0 41
```

That is a 5-byte record marker `30 04 04 fd ff`, five bytes `00 00 00 01 00`, and five floats
`47.209, 0.0, -6.75, 0.0448, 30.0`. The marker is distinct from the face marker `30 04 04 ff ff`,
which appears exactly 71 times at the face-outer-bound run. So the body and face records are
distinguishable by their marker byte, and the three body records are the only `fd` markers.

A `u32` count sits at offset +30: 3, 19, and 4140. After it the three records diverge:

| Body | Offset | Length | Count | Tail |
| --- | ---: | ---: | ---: | --- |
| 1 | 54 | 47 | 3 | `ff 03 01 00 00` `ff 01 00 00 00` `00 62 00` |
| 2 | 101 | 52 | 19 | `ff 03 01 00 00` `ff 01 00 00 00` `00 95 ff ed 78 00 00 00` |
| 3 | 153 | 53 | 4140 | `ff ff 02 00 01` `ff 97 05 00 00` `ff 97 05 00 00` `00 00 00 00` |

The counts 3, 19, and 4140 are neither the 71 faces nor the 56 surfaces. Body 3's 4140 is far
larger than either, so the field is not a face or surface count. The two `ff`-prefixed values are
`259` and `1` for bodies 1 and 2, and `1431` twice for body 3. `1431` is the handle count, so body
3's tail carries the handle count twice, but bodies 1 and 2 do not.

The body record therefore does not carry the face-to-surface map. The map has to come from the
inline face records in the shell record, which are not at a fixed offset from the body header.

### The body record writes one reference per domain

`CATCXBody::Stream` at `0x541d60..0x541eb7` writes, in order:

1. `WriteLinkedObjectsCount(body, count)`, a `u32`;
2. a loop from 1 to `count` of `WriteObject(domain, body)`, one scalable tag difference per domain;
3. `WriteLong(count)`, a `u32`;
4. `WriteBox(0xd8(body))`, a `CATMathBox` of six floats;
5. `WriteShort(0x11c(body))`, a `u16`.

So the body record is `4 + count + 4 + 24 + 2` bytes. For body 1 with count 3 that is 37 bytes,
and the 47-byte header leaves 10 bytes for the object header. The three domain references are
scalable tag differences, so the shell record is reached through the tag, not at a fixed offset
from the body header.

The body header's `ff 03 01 00 00` and `ff 01 00 00 00` are not the domain references. They are
the `WriteLong` and part of the box, and the domain references are the single bytes `ff`, `03`,
`01` immediately after the count.

### Only two `30 04 04` type tags exist, and neither is the shell

`Reservoir` `MainDataStream` contains exactly two five-byte prefixes that start with `30 04 04`:

| Prefix | Count | Meaning |
| --- | ---: | --- |
| `30 04 04 ff ff` | 71 | face flag rows |
| `30 04 04 fd ff` | 3 | body headers |

There is no `30 04 04` variant for the shell. The shell record is not identified by a `30 04 04`
type tag, so it cannot be found by scanning for a type prefix. It is reached only through the
domain tag difference in the body record, which resolves through the stream's object table.

The object header is written by `CATCGMStreamImpl::WriteObject` at `0x72970`: it writes the tag
difference, then the class identifier, then calls the object's own `Stream` method. The shell's
`Stream` method then writes the linked-object count, the body reference, the boolean, the three
scalars, the three arrays, the face count, and the face-reference loop. So the shell record is
`tag difference + class id + shell fields`, and the class id is not `30 04 04`.

### The class identifier is a plain u32

`CATCGMStreamImpl::ReadObject` at `0x71b40` reads the tag with
`ReadTagDifferenceAsLONG64_Scalable` and the class identifier with `CATMathStreamImpl::ReadULong`
at `0x1801e3c48`, a plain `u32`. So the object header is a scalable tag difference followed by a
four-byte class identifier.

The body header `30 04 04 fd ff 00 00 00 01 00` does not split cleanly under that rule: `0x30` has
bit 0 clear and `0x30 >> 2 = 12`, outside the valid `1..8` length range, so the first byte is not a
scalable tag difference. The same holds for the face row `30 04 04 ff ff e1 e1 e1`. So the first
byte of both records is a separate type tag, and the tag difference and class identifier follow it.

The shell's class identifier is therefore not recoverable from the two `30 04 04` prefixes. It has
to be read from the class table that `ReadObject` consults after reading the `u32`.

### The second field is an object-table index, not a class id

`CATCGMStreamImpl::ReadObject` at `0x71b40` reads the scalable tag difference, then a `u32` at
`0x180071c8a`, then tests the `u32`:

- if it is zero, a new object is created and the stream continues with the object's own
  `UnStream` data;
- if it is non-zero, the value is used as an index into the object table at `0x2b8(stream)` and
  the existing object is returned.

So the second field is an object-table index, not a class identifier. The class is determined by
the object's own `UnStream` method, which is dispatched from the object's vtable, not from a class
id in the stream.

This means the shell record cannot be found by scanning for a class-id byte pattern. The shell is
reached only by resolving the body's domain tag difference through the object table, and the
object table is built as the stream is read, not stored as a byte pattern in `MainDataStream`.

### `ReadObject` reads only the table index

`CATCGMStream::ReadObject` at `0x6eb70` is a thin wrapper that calls
`CATCGMStreamImpl::ReadObject` at `0x71b40`. The implementation reads exactly one `u32` through
`CATMathStreamImpl::ReadULong` at `0x180071c8a` and does not call
`ReadTagDifferenceAsLONG64_Scalable` at all. The tag difference is read by the caller before the
call, and the `u32` is the object-table index.

So an object reference in the stream is two fields: a scalable tag difference that updates the
current tag, and a `u32` table index that selects the object. The table is populated as the stream
is read, so a byte-pattern scan cannot recover it.

The face and shell unstream functions do not call `ReadObject` directly. Only
`CATDynBooleanSharedFaceData::ReadFromStream` and `TopoDebugTools::ReadBody` do. The face and shell
references are therefore read by a higher-level object reader that is not yet located, and that
reader is what builds the table the body's domain references resolve against.

### The linked-object list is an array of u32 tags

`CATCGMStreamImpl::ReadListOfLinkedObjects` at `0x717f0` reads a `u32` count with
`CATMathStreamImpl::ReadULong`, then an array of `u32` values with the array overload at
`0x1801e3b50`, then for each value calls `CATCGMHashTableBase::KeyLocate` at `0x1801e5278` and
appends the resolved object with `CATListPtrCATSurface::Append` at `0x180071ac2`.

So the face's linked-object list is an array of `u32` tags resolved through the object hash table,
and the resolved objects are surfaces. The face record therefore contains a `u32` count followed by
that many `u32` surface tags.

The surface record's three-byte tail values `445, 449, 476, 495, 499` in `Copper_Washer` do not
appear as `u32` little-endian anywhere in any stream except inside the surface bounds floats, at
`SurfacicReps` offsets 87, 160, 209, 258, and 331. So the tail is not the tag that the face record
stores, and the tag array is not a plain `u32` array of those values.

`Copper_Washer` `MainDataStream` contains no `u32` value in `400..500` in either byte order. So the
surface tags are not stored as `u32` in the B-rep stream at all. The tag array that
`ReadListOfLinkedObjects` reads must therefore be encoded differently from a plain `u32` array, or
the tags are assigned at read time from the object header rather than stored in the face record.

The object header is a scalable tag difference plus a `u32` table index. The tag difference is
relative to the previous tag, so the absolute tag of each object depends on the order in which the
objects are emitted. That order is not recoverable from a byte-pattern scan, because the same
difference bytes mean different absolute tags at different stream positions.

## The surface list is in face order only when the counts match

For all 22 parts where the surface count equals the face count, the surface planarity sequence is
*identical* to the face planarity sequence. A face is planar exactly when its trim record carries a
vector, and a surface is planar exactly when its kind is `0x32`. The two sequences match at every
index for all 22 parts, with no exceptions. So `surfaces[i]` is the surface of `faces[i]` for those
parts.

For the five parts where the surface count is smaller than the face count, the surface planarity
sequence is a *subsequence* of the face planarity sequence. The greedy alignment matches all
surfaces in every case:

| Part | Faces | Surfaces | Matched | Skipped faces |
| --- | ---: | ---: | ---: | --- |
| `4784` | 416 | 270 | 270 | 146 |
| `4876` | 870 | 714 | 714 | 156 |
| `4876_1` | 870 | 714 | 714 | 156 |
| `Pedal_Body` | 338 | 314 | 314 | 24 |
| `Reservoir` | 71 | 56 | 56 | 15 |

A subsequence match is much weaker than an index match, and it does not survive a stronger test.
The stronger test asks for a *monotone surjection*: a non-decreasing map from faces to surfaces that
uses every surface and gives every face a surface of the same planarity class. That is the exact
shape of "the surface list is the face list with duplicates removed, in face order".

Solving that as a path problem (each face either keeps the current surface or advances by one, and
the planarity must match) gives:

| Part | Monotone surjection exists | Solutions |
| --- | --- | ---: |
| `Reservoir` | yes | 12600 |
| `Pedal_Body` | yes | 129679067468302852500 |
| `4784` | no | 0 |
| `4876` | no | 0 |
| `4876_1` | no | 0 |

So the surface list is *not* in face order for `4784`, `4876`, and `4876_1`. For `Reservoir` and
`Pedal_Body` a monotone surjection exists but is wildly non-unique, so planarity does not determine
the map even there. The earlier "surface list is the face list with duplicates removed" conclusion
was wrong; the subsequence match was a weak property of binary sequences, not evidence of ordering.

The trim kind is a second, weaker planarity signal. A trim kind of `0x4a` or above always carries a
vector (994 of 994), but 68 trims below `0x4a` also carry one. The vector is authoritative; the kind
nibble is not.

The missing surfaces are not stored anywhere else. `MainDataStream` contains no `00 33 <kind>`
surface marker in any of the five parts (the one or two byte hits are coincidental), and the
`SurfacicReps` header field at offset 18 is `2` for `Reservoir` and `26` for the others, not the
surface count. So the five parts genuinely share surface records, and the face-to-surface reference
must come from the face record's own object reference, not from a positional rule.

The trim record has no spare field for a surface index. Its layout is fully consumed by the kind
byte, the three optional counts, the `ff`-prefixed total, the optional vector, the lengths, and the
handles. The surface record has no face-count field either: no byte position in any record sums to
the face count over the record set.

## The arity-2 edge handles are the B-rep vertices

`Copper_Washer` is small enough to check end to end. It has 6 faces, 8 vertices, 8 roster entries,
12 edges, and 76 distinct handles. The 6 surfaces are two planes at `x = 0` and `x = 1` and four
cylinder halves at radius 8 and radius 5, all with axis `x`. The trim vector is the plane normal:
face 2 has vector `(-1, 0, 0)` and its surface is the plane at `x = 0`; face 3 has vector
`(1, 0, 0)` and its surface is the plane at `x = 1`.

The 12 edges are four closed loops plus four arity-2 connectors:

```
loops:       (0,1,3,6,12,17,22,28,32,34,37)   (38,39,41,44,50,55,60,66,70,72,75)
             (5,8,10,14,16,20,24,26,31,30,27,25,21,19,15,11,9)
             (43,46,48,52,54,58,62,64,69,68,65,63,59,57,53,49,47)
connectors:  (36,74)  (0,38)  (31,69)  (5,43)
```

The four loops are the four boundary circles: outer at `x = 0`, outer at `x = 1`, inner at `x = 0`,
inner at `x = 1`. The four connectors are the seam edges, and each connects a handle at `x = 0` to a
handle at `x = 1` at the same `(y, z)`.

The eight connector handles are `0, 5, 31, 36, 38, 43, 69, 74`, and there are exactly eight
vertices. The eight loop endpoints are `0, 5, 31, 37, 38, 43, 69, 75`, which differ from the
connector set only by `{37, 75}` versus `{36, 74}` (adjacent tessellation points). So the connector
handles and the loop endpoints both identify the eight vertices, and the mapping is:

| Handle | Vertex |
| ---: | --- |
| 0 | `(0, -8, 0)` |
| 37 | `(0, 8, 0)` |
| 38 | `(1, -8, 0)` |
| 75 | `(1, 8, 0)` |
| 5 | `(0, 5, 0)` |
| 31 | `(0, -5, 0)` |
| 43 | `(1, 5, 0)` |
| 69 | `(1, -5, 0)` |

This is a real handle-to-vertex map, but only for the eight corner handles. The other 68 handles are
tessellation points along the four circles, and their positions are not recovered.

The same test holds exactly for the simple parts and fails for the complex ones. Counting the
distinct handles that appear in arity-2 edges and comparing to the vertex count:

| Part | Vertices | Arity-2 handles | Match |
| --- | ---: | ---: | --- |
| `Copper_Washer` | 8 | 8 | yes |
| `Washer_5` | 8 | 8 | yes |
| `Washer_6` | 8 | 8 | yes |
| `Washer_8` | 8 | 8 | yes |
| `Banjo` | 50 | 50 | yes |
| `Nut_ISO_7040-M6_1.1` | 40 | 40 | yes |
| `Nut_M6` | 40 | 40 | yes |
| `Brake_bias_90_degree_coupler` | 20 | 20 | yes |
| `Reservoir` | 88 | 109 | no |
| `4784` | 772 | 830 | no |
| `Pedal_Body` | 424 | 491 | no |

So for the simple parts the arity-2 handles are exactly the vertices, and for the complex parts they
are a strict superset. The extra arity-2 handles in the complex parts are not explained.

## The face-to-loop structure is complete for Copper_Washer

The four loops and six faces form a complete, consistent B-rep. Assigning each face to the loops its
handles fall in gives:

| Face | Loops | Surface | Meaning |
| ---: | --- | --- | --- |
| 0 | A, B | cylinder r=8 | outer cylinder half |
| 1 | A, B | cylinder r=8 | outer cylinder half |
| 2 | A, C | plane x=0 | annular plane at x=0 |
| 3 | B, D | plane x=1 | annular plane at x=1 |
| 4 | C, D | cylinder r=5 | inner cylinder half |
| 5 | C, D | cylinder r=5 | inner cylinder half |

Loop A is the outer circle at `x = 0`, loop B the outer circle at `x = 1`, loop C the inner circle
at `x = 0`, and loop D the inner circle at `x = 1`. The two planar faces are bounded by the outer
and inner circles at their own `x`, and the four cylinder halves are bounded by the outer or inner
circles at both `x` values. This is exactly the topology of a flat washer.

Placing the loop handles on their circles at equal angular spacing, with the eight corner vertices
fixed by the arity-2 map, makes both planar faces coplanar with their trim vectors at zero deviation:

```
face 2 planar n=(-1,0,0)  placed 42/56  maxdev=0.000000
face 3 planar n=(1,0,0)   placed 37/50  maxdev=0.000000
```

The placement is not a decode, though. Each planar face has handles that are in no loop: face 2 uses
nine distinct handles (`2, 4, 7, 13, 18, 23, 29, 33, 35`) that are not in loop A or loop C. Those
are interior tessellation points, and their positions are not recovered. So the loop points are
placed correctly, but the full tessellation is not determined by the loops alone.

## The trim handles are corners, not points

The decisive measurement is how many faces each handle belongs to. For `Copper_Washer`, counting the
faces that use each handle gives:

| Faces using the handle | Handles | Meaning |
| --- | ---: | --- |
| 3 | 4 | vertices |
| 2 | 68 | edge interiors |
| 1 | 4 | seam or interior |

The four 3-face handles are `0, 5, 38, 43`, and the four 1-face handles are `30, 36, 68, 74`. So a
handle is a *corner* on an edge, not a point. That is why the handle count (76) exceeds the vertex
count (8): the handles are the corners along the edges, and each edge carries several of them.

Grouping the 2-face handles by the face pair gives the eight face-to-face edges:

| Face pair | Handles | Circle |
| --- | ---: | --- |
| 0, 2 | 10 | outer at `x = 0` |
| 1, 2 | 9 | outer at `x = 0` |
| 0, 3 | 10 | outer at `x = 1` |
| 1, 3 | 9 | outer at `x = 1` |
| 2, 4 | 7 | inner at `x = 0` |
| 2, 5 | 8 | inner at `x = 0` |
| 3, 4 | 7 | inner at `x = 1` |
| 3, 5 | 8 | inner at `x = 1` |

So each of the four circles is split into two edges: the outer circles into 10 + 9 handles, the
inner circles into 7 + 8. The totals are 19 + 19 + 15 + 15 = 68 edge handles, plus 4 vertices and 4
one-face handles, which is the full 76.

This also explains the "interior" handles of the planar faces. Handles `2, 4, 7, 13, 18, 23, 29, 33,
35` are not interior points at all: they are the 2-face handles of the `(0, 2)` edge, so they lie on
the outer circle at `x = 0`. The planar face 2 uses them because they are on its boundary, and the
cylinder face 0 uses them because they are on its boundary too. So the planar faces are bounded
entirely by the circles, and the earlier "interior point" reading was wrong.

The 2-bit block does not resolve the positions. For `Copper_Washer` the candidate block is 27 bytes
at `199..226`, and every 19-byte window in it decodes to a two-bit distribution dominated by 2 and 3
(for example `{0:21, 1:10, 2:18, 3:27}`), which is the opposite of `Reservoir`'s `{0:866, 1:289,
2:198, 3:78}`. So either the block boundaries differ per part or the block is not the same encoding.

## The Copper_Washer B-rep rebuilds from the corner structure

The corner structure is enough to rebuild the whole B-rep. The eight vertices are the arity-2
handles, and the eight edges are the 2-face handle groups. Each edge lies on the intersection of its
two faces, which for a plane and a cylinder is a circle, so each edge is a circular arc between its
two endpoint vertices.

| Edge (faces) | Circle | Handles | Endpoints |
| --- | --- | ---: | --- |
| (1, 2) | outer at `x = 0` | 9 | `0 -> 36` |
| (0, 2) | outer at `x = 0` | 10 | `36 -> 0` |
| (1, 3) | outer at `x = 1` | 9 | `38 -> 74` |
| (0, 3) | outer at `x = 1` | 10 | `74 -> 38` |
| (2, 5) | inner at `x = 0` | 8 | `5 -> 31` |
| (2, 4) | inner at `x = 0` | 7 | `31 -> 5` |
| (3, 5) | inner at `x = 1` | 8 | `43 -> 69` |
| (3, 4) | inner at `x = 1` | 7 | `69 -> 43` |

Placing the edge handles at equal angular spacing along their arcs places 74 of the 76 handles. The
two unplaced handles are `30` and `68`, the 1-face seam handles, which lie on the inner circles at
the seam angle. With the placement, both planar faces verify at zero deviation with every handle
placed:

```
face 2 planar n=(-1,0,0)  placed 56/56  maxdev=0.000000
face 3 planar n=(1,0,0)   placed 50/50  maxdev=0.000000
```

The arcs are consistent with semicircles of the expected radii:

| Edge | Arc length | Expected |
| --- | ---: | ---: |
| outer (9 handles) | 25.030 | `pi * 8 = 25.133` |
| outer (10 handles) | 25.047 | `pi * 8 = 25.133` |
| inner (8 handles) | 15.628 | `pi * 5 = 15.708` |
| inner (7 handles) | 15.607 | `pi * 5 = 15.708` |

So the topology and the arc geometry are correct. The angular positions are assumed equal-spaced,
not decoded: the two semicircles of each circle carry 9 and 10 handles (outer) and 7 and 8 handles
(inner), which is not consistent with one uniform spacing around the full circle. So the placement
is a reconstruction from the topology, not a decode of the stored tessellation.

## The intersection-arc placement generalizes to plane-cone

The 2-face handle groups fall into nine surface-kind pairs across the corpus. Counting groups and
the handles in them:

| Kind pair | Groups | Handles | Placed on a circle |
| --- | ---: | ---: | ---: |
| plane-cylinder | 190 | 1249 | 1249 |
| plane-cone | 191 | 555 | 423 |
| plane-torus | 35 | 259 | 0 |
| cylinder-cylinder | 45 | 112 | 0 |
| cylinder-torus | 10 | 74 | 0 |
| cone-cone | 32 | 72 | 0 |
| torus-torus | 20 | 61 | 0 |
| plane-sphere | 11 | 45 | 0 |
| sphere-sphere | 6 | 10 | 0 |

A plane-cone intersection is a circle exactly when the plane is perpendicular to the cone axis. The
cone carrier gives the origin, the axis, and the half-angle, so the circle radius is
`distance(origin, plane) * tan(half_angle)` and the center is the cone origin projected onto the
plane. That covers 423 of the 555 plane-cone handles. The other 132 are oblique sections (ellipse,
parabola, hyperbola) and are not circles, so they stay on the vertex-table fallback rather than being
forced onto a circle.

The placement invariant is checkable and holds exactly. For every handle, the placed point must
satisfy every surface of the faces that use it: on the plane, and at the cylinder or cone radius.
Across the 22 decoded parts that is 4682 of 4682 handles on-surface, with zero exceptions.

## Edge curves are circular arcs, not chords

An edge joins two consecutive handles in a face cycle. When both endpoints lie on the same
intersection circle, the edge curve is a `CircleCurve` with that center, axis, and radius, and the
edge parameters are the start angle and the swept angle. Otherwise the edge stays a `LineCurve`.

Across the corpus that is 1661 circular-arc edges, and the worst endpoint radius error is 1.8e-6.
For `Copper_Washer` the per-circle arc totals are:

| Circle | Arcs | Total arc | Circumference |
| --- | ---: | ---: | ---: |
| inner at `x = 0`, r=5 | 17 | 31.416 | 31.416 |
| inner at `x = 1`, r=5 | 16 | 27.925 | 31.416 |
| outer at `x = 0`, r=8 | 21 | 48.209 | 50.265 |
| outer at `x = 1`, r=8 | 21 | 48.209 | 50.265 |

The inner circle at `x = 0` closes exactly. The others fall short by the seam gap and by the seven
edges that are not on a circle, which is expected because the seam handles are 1-face handles and
the connectors are arity-2 edges.

## The trim handles are not point indices

The trim handles are dense: `Reservoir` uses every value in `0..1430`, and `Copper_Washer` uses
every value in `0..75`. The tessellation point table does not have that many points.

`Reservoir` `MainDataStream` holds 1000 points in the float table at `569..12369`, while the handles
span 1431 values. `Copper_Washer` holds 38 points in the float table at `226..682`, while the
handles span 76 values. In both cases the handle count is larger than the point count, and the ratio
is not constant.

`Copper_Washer` shows the structure directly. Face 0 is a triangle strip whose handles alternate
between the two halves of the handle space: `0, 38, 2, 40, 4, 42, 7, 45, ...`. The offset is 38,
which is the point count. So the handle space is two parallel loops of 38 entries, and the strip
joins them. The two loops are the two boundaries of the annular face.

The point table is not a plain triple array. `Copper_Washer` has a 116-float run at `226`, a 2-byte
gap, then a 74-float run at `692`. `Reservoir` has twelve float runs between `569` and `12377`
separated by 4- and 8-byte gaps. The gaps are record markers, and the second loop of a face is
stored separately from the first.

The reader no longer uses `handle % len(vertices)`. It places each handle by the corner structure
described above, which makes the planar faces coplanar and puts every handle on its surfaces. The
angular positions are still assumed equal-spaced, so the geometry is a reconstruction, not a decode.

## The object reference is a tag difference against a running tag

The face-to-surface reference is a cross-stream object reference, and the reference encoding is now
recovered from the binaries. Three functions in `CATMathStream.dll` and `CATGeometricObjects.dll`
give the whole mechanism.

`CATMathStreamImpl::ReadTagFromTagDifference` at `0x1800b8670` decodes one tag difference:

```
b = read_byte()
if b & 1:  diff = b >> 2
else:      n = b >> 2 (1..8); diff = read n bytes little-endian
if b & 2:  tag = current - diff - 1
else:      tag = current + diff
```

So bit 0 selects an inline 6-bit difference or a 1-to-8-byte difference, and bit 1 selects the
direction. The `- 1` on the negative branch means the encoding is a bijection: `+0` and `-0` are
distinct, so a zero difference still advances the tag.

`CATMathStreamImpl::ReadTagDifferenceAsLONG64_Scalable` at `0x1800b8480` is the same byte layout
returning a signed 64-bit difference, and `CATMathStreamImpl::ReadULongWithSign` at `0x1800a3420`
reads the object index as a 4-bit-per-byte varint with continuation bit `0x10`.

`CATCGMStreamImpl::ReadRelativeTag` at `0x180071da0` reads a whole tag array:

```
ReadLONG64_Scalable(stream, count, buffer)
for i in range(count): out[i] = base_tag - buffer[i]
```

`CATCGMStreamImpl::ReadListOfLinkedObjects` at `0x1800717f0` then resolves each tag through the
container's virtual method at vtable offset `0xc0` and appends the result to a
`CATListPtrCATSurface`. The container is `0x2b0(stream)` and the object table is `0x2b8(stream)`,
which is a `CATCGMHashTableBase` probed with `KeyLocate`.

`CATCXFace::UnStream` at `0x18054eef0` does not read the surface itself. It calls
`SkipRemainingLinkedObjectsToRead`, so the face's surface reference lives in the generic object
header that precedes the face body, not in the face body. That is why the trim record has no spare
field for a surface index: the reference was never in the trim record.

The object header offset is not yet located. Decoding tag differences at the body records, the
two-bit block, the face-outer-bound run, the edge table, and the vertex table all fail on the first
or second byte with an out-of-range length, so none of those regions starts with a tag array.

## The pooled parts differ only in their non-planar faces

The five parts that fail the surface-count check have an exact planar correspondence. Counting the
faces whose trim record carries a vector (planar) against the surfaces of kind `0x32` (planes):

| Part | Faces | Surfaces | Planar faces | Plane surfaces | Non-planar faces | Non-planar surfaces | Deficit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `Reservoir` | 71 | 56 | 13 | 13 | 58 | 43 | 15 |
| `Pedal_Body` | 338 | 314 | 66 | 66 | 272 | 248 | 24 |
| `4784` | 416 | 270 | 91 | 91 | 325 | 179 | 146 |
| `4876` | 870 | 714 | 359 | 359 | 511 | 355 | 156 |
| `4876_1` | 870 | 714 | 359 | 359 | 511 | 355 | 156 |

The planar count equals the plane-surface count exactly in every part, and the deficit equals the
non-planar face count minus the non-planar surface count. So the surface pooling is entirely among
non-planar faces: cylinders, cones, spheres, and tori are shared, planes are not.

That narrows the map but does not determine it. Three cheap rules were tested and all fail:

- the trim `counts` fields are not surface indices: they are all in range but have only 12 to 27
  distinct values against 56 to 714 surfaces;
- matching planar faces to plane surfaces by normal and then scoring candidate planes by how many
  vertex-table points they contain is not unique: `Reservoir` has 0 unique of 13, `Pedal_Body` 22 of
  66, `4784` 20 of 91;
- no contiguous tag array of 56 or 71 tags exists in `MainDataStream` or `SurfacicReps` under a
  bounded, distinct, plausible-range filter.

## The stream preamble carries a payload length, not a header table

`Reservoir` has three `MainDataStream` streams of 19, 63, and 31156 bytes. The 31156-byte one starts
with `a3 ff b2 79 00 00 00 00`, where `b2 79` is `31154`, exactly the payload length after the
8-byte preamble. The 63-byte one starts with `ff 3e 00 00`, where `3e 00` is `62`, exactly the
payload length after a 1-byte preamble, and its payload carries the tolerances `0.1`, `1.0`, and
`0.02`. The 19-byte one starts with `56 d0 10 00 36 00 00 00 07 00 00 00`, where `36 00 00 00` is
`54`, the offset of the first body record, and `07 00 00 00` is `7`.

So the small `MainDataStream` is a pointer record, not a header table. `SurfacicReps` starts with
`ff 33 1f 00 00 db 0f 49 3f`, where `db 0f 49 3f` is `pi / 4`, and its first surface record begins
at offset 17. None of these preambles contains a table of object-header offsets, so the object table
is built at load time rather than read from a table.

## The surface records are interleaved with per-surface control points

The surface records are not contiguous. In `Reservoir` the first ten records start at 17, 66, 350,
423, 500, 667, 740, 789, 979, and 1052, and the gaps between them are 0, 235, 0, 0, 94, 0, 0, 141,
and 0 bytes. The gap bytes are six-float groups of a point and a normal, for example
`(-19.32, 1.478, 21.76, 0.523, 1.236, 0.876)` followed by `(-19.32, 1.49, 21.76, 1.59, ...)`, where
the two groups share `x` and `z` and differ in `y`. Each gap is preceded by a `ff <byte> 0c 00`
marker.

So `SurfacicReps` is a sequence of surface records each followed by its own control-point block, and
the marker scan that recovers the records is the right approach. The control-point blocks are not
the face-to-surface map either: they belong to the surface, not to a face.

## Evidence

- `re/catia/tooling/ParseBrep.py` decodes 22 of 27 parts.
- `re/catia/tooling/BuildModel.py` validates every decoded model.
- `src/convert/adapters/catia/NativeBrep.py` is the production reader.
- `CATMathStream.dll` SHA-256 `712e258f9c39f552e52f441713719cc5f1d7bea61dfb1b29c642af7cfb24e01b`.
- `CATFloatCompactor::ReadFloatWithRef` at `0x18009c220`.
- `CATFloatCompactor::ReadFloatStandard` at `0x18009c030`.
- `CATFloatCompactor::ReadDoubleWithRef` at `0x18009b590`.
