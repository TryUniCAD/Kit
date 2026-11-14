# CATIA native B-rep reader and writer

## Behavior

The `catia.v5` adapter now decodes the standard nested CATIA V5 B-rep spine.
It reads the face-outer-bound run, trim packets, edge table, vertex table, surface records, curve
rows, and vertex roster from `MainDataStream` and `SurfacicReps`.
It maps the result to a neutral `BrepModel` with faces, loops, coedges, edges, vertices, and
analytic plane, cylinder, cone, sphere, and torus surfaces.

The trim handles are dense indices into a shared tessellation table, not B-rep vertex identifiers.
The handle-to-point map is not decoded: the handle count exceeds the point count in every part
(`Reservoir` has 1431 handles and 1000 points, `Copper_Washer` has 76 handles and 38 points), and
the point table is split into runs by record markers. The reader therefore maps a handle to a
vertex with a placeholder rule and derives loops from the tessellation boundary. That is a
documented structural approximation, not the native B-rep topology or geometry.

The surface records are ordered by face. For all 22 parts where the surface count equals the face
count, the surface planarity sequence is identical to the face planarity sequence. For the five
parts with fewer surfaces than faces, the surface planarity sequence is a subsequence of the face
planarity sequence, so the surface list is the face list with duplicate surfaces removed. The
reader still requires the two counts to match, because the reuse map for the skipped faces is not
decoded.

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
  placeholder, so the decoded geometry is not the file's geometry even for the 22 parts that pass
  validation. The coordinate region is a sequence of float runs separated by 1- to 8-byte record
  headers, and it holds 1003 points for `Reservoir` against a 1431-value handle space, so the
  handles are not indices into it. The 363-byte block before the first large run is a sparse bit
  array, not a compactor stream: the compactor decodes it to denormals and then `1e297`.
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
