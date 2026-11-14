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

### The body header is 47 bytes and its count is not a face count

`Reservoir` has three body headers at offsets 54, 101, and 153, each 47 bytes. The layout is:

- 30 bytes of object header, identical in all three:
  `30 04 04 fd ff 00 00 00 01 00 62 d6 3c 42 00 00 00 00 00 00 d8 c0 95 63 37 3d 00 00 f0 41`;
- a `u32` count at offset +30: 3, 19, and 4140;
- two `ff`-prefixed counts: `ff 03 01 00 00` (259) and `ff 01 00 00 00` (1) for bodies 1 and 2;
- three trailing bytes.

The counts 3, 19, and 4140 are neither the 71 faces nor the 56 surfaces. Body 3's 4140 is far
larger than either, so the field is not a face or surface count. The two `ff`-prefixed values are
the same for bodies 1 and 2 and differ for body 3, so they are not per-body face counts either.

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

## Evidence

- `re/catia/tooling/ParseBrep.py` decodes 22 of 27 parts.
- `re/catia/tooling/BuildModel.py` validates every decoded model.
- `src/convert/adapters/catia/NativeBrep.py` is the production reader.
- `CATMathStream.dll` SHA-256 `712e258f9c39f552e52f441713719cc5f1d7bea61dfb1b29c642af7cfb24e01b`.
- `CATFloatCompactor::ReadFloatWithRef` at `0x18009c220`.
- `CATFloatCompactor::ReadFloatStandard` at `0x18009c030`.
- `CATFloatCompactor::ReadDoubleWithRef` at `0x18009b590`.
