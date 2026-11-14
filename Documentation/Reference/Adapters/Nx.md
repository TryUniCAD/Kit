# Siemens NX adapter

## Purpose

The Siemens NX adapter reads native `.prt` containers and writes native
container rewrites. It recognizes both the modern SPLMSSTR envelope and the
legacy compound-file envelope.

The adapter is for native NX-to-NX work. It does not author new NX feature
records from a neutral model.

## Before you start

- Use an NX part with the `.prt` suffix.
- Use NX 2506 or a compatible native save.
- Keep referenced component `.prt` files beside the assembly when the part has
  external references.

## Read a part

```python
from convert.adapters.nx import ReadNx

Document = ReadNx("part.prt")
print(Document.source.format_id)
print(len(Document.bodies))
print(Document.metadata["nx.attributes"])
```

The reader returns:

- the native feature graph as one `imported` feature step;
- Parasolid B-rep bodies when the embedded stream is supported;
- part attributes from `/Root/part/attrs`;
- external-reference strings;
- the exact source container as a `document` payload.

The reader does not convert NX expressions into neutral parameters.

## Write a part

```python
from dataclasses import replace

from convert.adapters.nx import ReadNx, WriteNx

Document = ReadNx("part.prt")
Changed = replace(
    Document,
    metadata={
        **Document.metadata,
        "nx.attribute_overrides": {"NX_ReferenceSet": "KitNX"},
    },
)
WriteNx(Changed, "part-rewrite.prt")
```

The writer rebuilds the SPLMSSTR directory from the parsed stream map. It
recomputes every offset and both native seals, so a rewrite may change stream
sizes.

Attribute overrides must keep the same byte length because the matching
object-model record is length framed. To replace a whole stream at a new
length, use `nx.stream_overrides`:

```python
Changed = replace(
    Document,
    metadata={
        **Document.metadata,
        "nx.stream_overrides": {
            "/Root/FastLoad/ExternalReferences": new_bytes,
        },
    },
)
WriteNx(Changed, "part-rewrite.prt")
```

The writer raises an error when a rebuilt seal does not match, so an
inconsistent container is never written.

A part can be renamed with `nx.part_name`:

```python
Changed = replace(
    Document, metadata={**Document.metadata, "nx.part_name": "black.prt"}
)
WriteNx(Changed, "renamed.prt")
```

The new name must keep the current byte length and the `.prt` suffix. NX stores
the name in five places, so a rename updates all of them or none.

## Limits

- The writer does not create new NX geometry, features, expressions, or
  assemblies.
- Attribute overrides keep their byte length because the object-model record is
  length framed.
- Legacy compound parts are readable without B-rep projection. Writing one is
  refused because the modern container checksum layout would change.
- Full object-model field semantics remain research work.

## Verification

The local NX 2506 oracle opened the Kit rewrite with one body and the original
feature tree. The `DATUM_CSYS` and `BLOCK` features were present and not
suppressed. The six expressions, volume, area, centroid, and mass matched the
control. Changing `length` from `40` to `45` and updating the model rebuilt the
body to volume `27000 mm3`, area `5700 mm2`, and centroid
`(22.500000000000004, 15.000000000000002, 10.000000000000002)`.
NX also loaded a header-changing rewrite that grew
`/Root/FastLoad/ExternalReferences` by four bytes and shifted every later
offset. The header seal and footer fingerprint were recomputed from the format
rules, not copied from the source.

See [the NX data model](../../../re/nx/notes/DataModel.md) and
[the change entry](../../Changes/Nx/NxNativeContainer.md).

## Related information

- [Siemens NX header checksum gotcha](../../Gotchas/Conversion/NxHeaderChecksum.md)
- [NX acceptance evidence](../../../re/nx/notes/AcceptanceEvidence.md)
- [B-rep model](../Model/Brep.md)
- [Document model](../Model/Document.md)
