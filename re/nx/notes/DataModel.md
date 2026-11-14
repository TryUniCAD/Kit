# Siemens NX native part data model

## Evidence boundary

This note describes the bytes observed in NX 2506 and in the public cadmpeg
format documentation. It separates confirmed container facts from unresolved
object-model and feature semantics. The production reader in
`src/convert/adapters/nx/` does not read files from this directory.

## Envelopes

NX saves the same part in two envelopes.

| Envelope             | Signature                 | Directory                                  | Geometry                                                         |
| -------------------- | ------------------------- | ------------------------------------------ | ---------------------------------------------------------------- |
| SPLMSSTR             | `SPLMSSTR`                | `HEADER` and optional `FOOTER` path tables | zlib-compressed Parasolid streams inside `/Root/UG_PART/UG_PART` |
| Compound File Binary | `D0 CF 11 E0 A1 B1 1A E1` | OLE storage and stream tree                | clear Parasolid streams inside `UG_PART/UG_PART`                 |

The modern envelope uses little-endian directory fields and a 48-bit footer
offset. A `FOOTER` offset of `0xffffffffffff` means the `HEADER` table is the
complete directory. The root entry payload is the stable UUID
`611ec9b3-fa60-d111-8ad9-0800362fb302`; it is not a file range.

The header directory is followed by a reserved trailer before the first file
payload. The trailer stores an xxh32 seal, little-endian, at trailer offset
`0x21E`. The seal covers the header directory from the `HEADER` marker at
`0x19` through the seal field. The file ends with a second xxh32 value: the
footer fingerprint covers the footer directory.

Seven NX 2506 saves with different payload sizes and directory layouts matched
both formulas exactly. Rebuilding a directory therefore only requires
recomputing these two seals. The production writer does that for every rewrite,
including rewrites that change stream sizes and shift later offsets.

## Canonical part payload

`/Root/UG_PART/UG_PART` begins with a counted segment index of 12-byte rows:

```text
type_code:u32  subtype_code:u32  value:u32
```

Row ordinal 1 is `type_code=1`, `subtype_code=1`, and `value` is the payload
offset after the index. The index may end up to eleven bytes before a twelve
byte boundary; the row count is the aligned part. The index words name
object-model sections and compressed stream wrappers.

NX 2506 also saves parts with no compressed streams. Their payload holds only
the index and OM sections, and NX requires both the `UG_PART` payload and its
`UG_PART/ExternalReferences` stream. Fast-load streams, `qafmetadata`,
`part/attrs`, and the saved toggle stream can be one byte each in a loadable
part. Replacing the `ExternalReferences` stream with a one byte placeholder
fails with `Unexpected end of file`. A section begins with an optional `c0 d1 f1 ed`
separator, `ff ff ff ff`, four zero bytes, a big-endian payload size, and the
`OM 01 01` signature. Section bodies contain the NX object-model class
registry, attribute registry, object records, feature history, expression
records, and assembly records.

A compressed wrapper starts with `marker:u32 LE` and
`compressed_byte_len:u32 LE`. Marker `0x80000000 | extension_length` has an
eight-byte fixed header. Marker `0xa0000000` has a sixteen-byte fixed header.
Marker `0xc0000000 | extension_length` selects a 33, 45, or 57 byte fixed
header from its code and version words. The checksum-valid zlib member starts
after the wrapper. NX stores Parasolid binary data in that member.

## Object model

The class registry is a sequence of length-framed records:

```text
06  name_len:u16  class_name  version:u32  base_len:u16  base_name  class_id:u32
```

The attribute registry uses tag `07` and adds the attribute name and attribute
id. Object records refer to class and attribute ids. The reader retains the
registry markers and exact section bytes rather than claiming a complete typed
decode of every class.

Feature history sections carry ordered operation headers. A header starts with
`80 cd 01 04 01`, a shifted binary64 value, `ff ff`, four object-index slots,
and an optional length-framed label. The label identifies operations such as
`SKETCH`, `UNITE`, `SUBTRACT`, `INTERSECT`, `MOVE_FACE`, `CYLINDER`, and
`MOVE_OBJECT`. The four slots address object records in the section. Boolean
operations add a target list and a tool list. Expression records use the
`UGS::EXP_expression` marker.

The controlled `block.prt` control has a `BLOCK` operation and six expression
objects. NX reports `p0=40`, `p1=30`, `p2=20`, `length=40`, `width=30`, and
`height=20`. The neutral reader exposes the retained native graph, but it does
not yet project those expression values into independent neutral parameters.

## B-rep geometry

The compressed Parasolid stream in the block control begins `PS` and carries a
transmit-file description with schema `3701250`. The existing Kit Parasolid
decoder reads it as one body with six faces, twelve edges, and eight vertices.
NX reports the same body, volume `23999.999999999996 mm3`, area `5200 mm2`,
centroid `(19.999999999999996, 15, 9.9999999999999982)`, and mass
`0.18793536 kg` for the block control.

The NX process rebuilt the live feature tree after changing the `length`
expression from `40` to `45`. The body changed to volume `27000 mm3`, area
`5700 mm2`, and centroid
`(22.500000000000004, 15.000000000000002, 10.000000000000002)`.

NX stores analytic surfaces and curves as Parasolid records. The supported
families documented by cadmpeg and observed in the corpus are points, lines,
circles, ellipses, planes, cylinders, cones, spheres, tori, B-surfaces,
B-curves, trimmed curves, offset surfaces, and blend surfaces. Topology uses
BODY, REGION, SHELL, FACE, LOOP, FIN, EDGE, and VERTEX records with big-endian
fields. Geometric doubles are metres; Kit converts them to millimetres.

## Why the format was difficult

1. The `.prt` extension is shared by NX and Creo, so the envelope cannot be
   selected from the suffix.
2. NX uses both OLE and SPLMSSTR envelopes, and the modern envelope has a
   reserved header trailer with its own checksum coverage.
3. The part payload is a segment index, object-model sections, and compressed
   Parasolid streams, not a single contiguous record table.
4. The object model uses class and attribute registries, length-framed object
   records, shifted binary64 values, and object-index encodings.
5. Feature history, expressions, placement, and B-rep topology use separate
   record families and reference namespaces.

## Current implementation boundary

The production reader parses both envelopes, extracts the native stream map,
decodes Parasolid geometry through the existing Kit reader, retains the exact
native document, and exposes the native feature graph as one imported step. The
production writer
rebuilds the SPLMSSTR directory from parsed streams, supports equal-length
native attribute replacement and whole-stream replacement at any byte length,
and reseals the header and footer after every rewrite.

It does not author a new NX part from a neutral model, does not emit new NX
feature records, and does not project NX expressions into neutral parameters.
Those are the remaining gaps to the full acceptance criterion.

The reader refuses to claim parametric history: the feature step uses the
`imported` kind, so capability inference does not report `parametric_history`.
It does accept neutral edits away from the retained native graph: the writer
compares a stored projection digest and raises when features, parameters,
bodies, sketches, planes, or selections changed.

Legacy compound parts keep attributes and the object model but return no B-rep
and record `nx.legacy_geometry_unavailable`. Their payload streams are not
decoded, so a write is refused instead of converting to a modern container.
