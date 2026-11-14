# Siemens NX native container reader and rewrite writer

## Behavior

Kit now discovers a `siemens.nx` adapter for native `.prt` files.

The reader accepts the modern SPLMSSTR envelope and the legacy compound-file
envelope. It extracts the `/Root/UG_PART/UG_PART` payload, parses the segment
index, finds object-model sections, inflates Parasolid streams, and decodes
supported B-rep geometry through the existing Kit Parasolid reader.

The neutral result contains:

- the native NX feature graph as one `imported` feature step;
- decoded Parasolid body records and B-rep topology;
- part attributes from `/Root/part/attrs`;
- external-reference strings;
- the exact source container as a `document` payload.

The writer accepts a document with a retained native NX payload. It parses the
container, rebuilds the SPLMSSTR directory, and writes a native NX part.

Rebuilding recomputes directory offsets and both native seals:

- the header seal is `xxh32` over the header directory and trailer prefix,
  stored at `trailer_start + 0x21E`
- the footer fingerprint is `xxh32` over the footer directory

Header-changing rewrites are therefore supported. Equal-length native
attribute overrides update `/Root/part/attrs` and the matching object-model
value. `nx.stream_overrides` replaces a whole stream at any byte length.

`nx.part_name` renames the part. A rename rewrites the section headers, the
file-name frame in the object-model middle, and the self references in
`RMFastLoad`, `Structure`, `FastLoad/ExternalReferences`,
`UG_PART/UG_PART`, and `UG_PART/ExternalReferences`. The new name must keep the
old byte length and the `.prt` suffix; other names are refused because the
name bytes are addressed by absolute offsets.

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
- Attribute overrides keep the value byte length because the object-model
  record is length framed.
- A part rename requires the same byte length as the current name.
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

NX also loaded a rename built by the adapter. `block.prt` written as
`black.prt` kept one body, `DATUM_CSYS` and `BLOCK`, six expressions, volume
`23999.999999999996`, area `5200`, and mass `0.18793536`, and the reader then
reported only the new external reference.

NX also loaded a header-changing rewrite built by the adapter. The rewrite
grew `/Root/FastLoad/ExternalReferences` by four bytes, shifted every later
payload offset, resealed the header and footer, and kept one body, both
features, six expressions, and the original mass.

Seven NX-saved variants confirmed the seal algorithm. The computed `xxh32`
digest matched the stored header seal and footer fingerprint in every file.

The repository boundaries were exercised by synthetic SPLMSSTR integration
tests that build a container from bytes, read it, rewrite it with an
equal-length attribute change and with a different-length stream override,
verify both seals, and read the result again. No vendor part is shipped as a
test fixture.

## Related information

- [NX adapter guide](../../Reference/Adapters/Nx.md)
- [NX data model](../../../re/nx/notes/DataModel.md)
- [NX acceptance evidence](../../../re/nx/notes/AcceptanceEvidence.md)
- [NX header checksum gotcha](../../Gotchas/Conversion/NxHeaderChecksum.md)
