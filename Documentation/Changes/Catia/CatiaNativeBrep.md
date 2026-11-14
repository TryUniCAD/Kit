# CATIA native B-rep reader and writer

## Behavior

The `catia.v5` adapter now decodes the standard nested CATIA V5 B-rep spine.
It reads the face-outer-bound run, trim packets, edge table, vertex table, surface records, curve
rows, and vertex roster from `MainDataStream` and `SurfacicReps`.
It maps the result to a neutral `BrepModel` with faces, loops, coedges, edges, vertices, and
analytic plane or cylinder surfaces.

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

- The reader decodes 25 of 27 corpus parts. The two `4876` parts use an unsupported layout.
- The reader reconstructs plane and cylinder geometry from bounds and trim vectors.
- The reader does not decode compressed carrier parameters, feature records, sketches, dimensions,
  constraints, or relations.
- The writer supports plane faces with one loop per face.
- The writer does not emit feature history, sketches, dimensions, or constraints.
- The writer reports `vendor_loadable=False` and `application_usable=False`.
- CATIA acceptance is not measured because the local CATIA install has no license.

## Verification

- `re/catia/tooling/ParseBrep.py` decodes 25 of 27 parts.
- `re/catia/tooling/BuildModel.py` validates every decoded model with zero errors.
- A six-face box emitted by the writer reads back as six faces, twelve edges, and eight vertices
  with zero validation errors.
- `tests/convert/catia/CatiaNativeTests.py` covers the corpus reader and the writer round trip.

## Related information

- [CATIA adapter](../Reference/Adapters/Catia.md)
- [CATIA B-rep findings](../../re/catia/Brep.md)
- [CATIA measurements](../../re/catia/Measurements.md)
