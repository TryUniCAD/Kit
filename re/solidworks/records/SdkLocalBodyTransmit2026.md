# Package serializer for generated local BODY nodes

`EncodeLocalXmt` accepts an ordered tuple of freshly generated `XmtNode`
records. It writes the local BODY role of `SCH_3701250_37102_13006`. The
first node is a single ownerless solid BODY at index 1. Wire indices are
consecutive, with a maximum of 4,096 resident nodes. The admitted topology
uses points, lines and planes. The optional single BODY attribute list uses
resident declarations and integer or Unicode value slots.
[Package writer](../../../src/convert/adapters/solidworks/Archive/Partition/LocalWrite/EncodeLocalXmt.py)
· [Local transmit grammar](ImportedLocalBodyKernel2026.md)

The writer uses the current reader's base and effective shapes, emits a
computed schema descriptor on each kind's first occurrence, and encodes
native pointers and scalar widths in effective field order. Schema constants
identify the format and role. Counts follow typed values and references
resolve to resident records of the required kind. Mandatory curve, plane and
point links bind their own edge, face and vertex. The writer checks the
solid inventory and each attribute's owner, type head and slot counts before
returning bytes. The neutral model and its construction code own geometry,
attribute values and node allocation.
[Current shape registry](../../../src/convert/adapters/solidworks/Archive/Partition/KernelShapes.py)
· [Fresh node construction](GeneratedLocalBodyKernel2026.md)

## Offline construction and readback

| Generated body | Resident nodes | Raw bytes | Framed bytes |
| --- | ---: | ---: | ---: |
| Rectangular, bare | 87 | 3,759 | 1,666 |
| Rectangular, minimally owned | 108 | 4,560 | 2,077 |
| Concave, bare | 125 | 5,193 | 2,231 |
| Concave, minimally owned | 146 | 5,994 | 2,646 |

The verifier gives both encoders the same newly allocated records from two
neutral prisms. It compares every derived transmit and compression frame
byte for byte. The package decoder preserves the complete typed records
and its solid graph check passes. Independent measurements of the decoded
face loops match analytic volume, area and centroid for both shapes.

Two offline processes produced identical receipts. They opened zero source
files during construction and verification. Twenty-one malformed graphs
or requests were refused, including an alternate schema, missing and unknown
fields, incorrect scalar and array domains, and absent, nonresident, wrongly
typed or wrongly owned geometry links.
[Numeric receipt](../measurements/2026/SdkLocalBodyTransmit01.json)

The completed research part builder emits both modes through the package
serializer. At the same logical destination, four fresh containers and
their 48 streams matched the pre-port generator at
`41b7859c562e315d82255df0a69a42b9ae8b2bdd` byte for byte. The four containers
were 9,805, 10,233, 10,360 and 10,791 bytes. The receipt lists the current
builder hash, container digests and every stream digest.
[Integrated builder](../../tooling/sw2026/imported_body_source/BuildImportedLocalPart.py)

This is local transmit evidence for a package writer prerequisite. Native
lifecycle and public conversion acceptance are measured separately.
[Existing native lifecycle](../measurements/2026/GeneratedLocalBodyPartCompleted01.json)

## Reproduce the comparison

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  uv run --offline --no-project --python 3.13 python -B \
  re/tooling/sw2026/imported_body_source/VerifyLocalXmtWriter.py
```
