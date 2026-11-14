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

## Evidence

- `re/catia/tooling/ParseBrep.py` decodes 22 of 27 parts.
- `re/catia/tooling/BuildModel.py` validates every decoded model.
- `src/convert/adapters/catia/NativeBrep.py` is the production reader.
- `CATMathStream.dll` SHA-256 `712e258f9c39f552e52f441713719cc5f1d7bea61dfb1b29c642af7cfb24e01b`.
- `CATFloatCompactor::ReadFloatWithRef` at `0x18009c220`.
- `CATFloatCompactor::ReadFloatStandard` at `0x18009c030`.
- `CATFloatCompactor::ReadDoubleWithRef` at `0x18009b590`.
