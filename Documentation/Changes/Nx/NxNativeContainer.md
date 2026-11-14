# Siemens NX native container reader and rewrite writer

## Behavior

Kit now discovers a `siemens.nx` adapter for native `.prt` files.

The reader accepts the modern SPLMSSTR envelope and the legacy compound-file
envelope. It extracts the `/Root/UG_PART/UG_PART` payload, parses the segment
index, finds object-model sections, inflates Parasolid streams, and decodes
supported B-rep geometry through the existing Kit Parasolid reader.

The neutral result contains:

- the native NX feature graph as one `native` feature step;
- decoded Parasolid body records and B-rep topology;
- part attributes from `/Root/part/attrs`;
- external-reference strings;
- the exact source container as a `document` payload.

The writer accepts a document with a retained native NX payload. It parses the
container, rebuilds the SPLMSSTR directory, and writes a native NX part.
Equal-length native attribute overrides are supported. Header-changing edits
are refused because NX validates a checksum over the header trailer.

## Usage

```python
from convert.adapters.nx import ReadNx, WriteNx

Document = ReadNx("part.prt")
WriteNx(Document, "part-rewrite.prt")
```

See [the adapter guide](../../Reference/Adapters/Nx.md).

## Limits

- The writer does not author new NX geometry, feature records, expressions, or
  assemblies from a neutral model.
- The writer does not support header-changing directory layouts.
- Legacy compound parts are read without B-rep projection. Writing one is
  refused because the modern container checksum layout would change.
- NX expressions remain native objects; they are not projected into neutral
  parameters.

## Verification

The local NX 2506 oracle opened a control part and the Kit rewrite:

| Check       |                                                         Control |              Kit rewrite |
| ----------- | --------------------------------------------------------------: | -----------------------: |
| Bodies      |                                                               1 |                        1 |
| Features    |                                           `DATUM_CSYS`, `BLOCK` |    `DATUM_CSYS`, `BLOCK` |
| Expressions | `p0=40`, `p1=30`, `p2=20`, `length=40`, `width=30`, `height=20` |                     same |
| Volume      |                                        `23999.999999999996 mm3` | `23999.999999999996 mm3` |
| Area        |                                                      `5200 mm2` |               `5200 mm2` |
| Centroid    |                  `(19.999999999999996, 15, 9.9999999999999982)` |                     same |
| Mass        |                                                 `0.18793536 kg` |          `0.18793536 kg` |

The rewrite changed the native `NX_ReferenceSet` attribute from `Empty` to
`KitNX`. NX loaded the rewrite with `NumberUnloadedParts=0`.

The live feature tree rebuilt after the `length` expression changed from `40`
to `45`. NX reported volume `27000 mm3`, area `5700 mm2`, and centroid
`(22.500000000000004, 15.000000000000002, 10.000000000000002)`.

The repository boundaries were exercised by a synthetic SPLMSSTR integration
test that builds a container from bytes, reads it, rewrites it with an
equal-length attribute change, and reads the result again. No vendor part is
shipped as a test fixture.

## Related information

- [NX adapter guide](../../Reference/Adapters/Nx.md)
- [NX data model](../../../re/nx/notes/DataModel.md)
- [NX acceptance evidence](../../../re/nx/notes/AcceptanceEvidence.md)
- [NX header checksum gotcha](../../Gotchas/Conversion/NxHeaderChecksum.md)
