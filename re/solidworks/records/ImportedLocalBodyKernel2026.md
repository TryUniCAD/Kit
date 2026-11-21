# SOLIDWORKS 2026 imported local-body Parasolid transmit

The disclosed imported box from SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`
has source SHA-256
`13f1ef12ab727323a826ead989087079f44e9b24a4326aa9b65be61c9d81f325`.
The [native source receipt](../measurements/2026/ImportedBaseBodySourcesNative01.json)
binds the source authoring and fresh reopen. The
[local-body envelope receipt](../measurements/2026/ImportedLocalBodyEnvelope01.json)
covers the enclosing SOLIDWORKS archive. This investigation covers the
Parasolid transmit reached from that envelope.

## Typed replay

The `Config-0-FeatureBodies/LocalBodies` stream occupies 3,050 bytes. The
single compressed wrapper begins at sample byte 44 and ends at the stream
boundary. Its zlib frame begins at sample byte 72. The raw payload identifies
`SCH_3701250_37102_13006` and has the description
`: TRANSMIT FILE created by modeller version 3701250`. It uses the bare
model description without a partition or delta role.

| Component | Bytes | SHA-256 |
| --- | ---: | --- |
| Typed active body after its transmit header | 6214 | `9a73c63d1daf74dc1549e7eef3a87d7f0fc48c98461c95854f16393c554e8051` |
| Complete raw transmit including the 84-byte header | 6298 | `ffc52d3cd19c4cba65fa798df5ffa0e45b3c85120fbd139e96092da292e836b0` |
| Complete wrapper including the 2,970-byte zlib frame | 3006 | `059616a6df73a274dc12ce6b50534e7762b72061cecc53b06574d84dd6312b0f` |

The [local kernel tool](../../tooling/sw2026/imported_body_source/LocalBodyKernel.py)
decodes the graph with `para.Partition.decode_active` and re-emits it with
`write_node`. It constructs the known bare header and recomputes all
compression and wrapper lengths through `EncodePartData`. The raw transmit
and compressed wrapper both match byte for byte in memory. The
[measurement](../measurements/2026/ImportedLocalBodyKernel01.json) records
the owning source hashes and the Python and zlib versions.

## Body and attribute ownership

The first record is a single solid BODY at sample index 1 with
`BODY.owner = 0`. Every one of the 172 resident nodes is reachable from that
body. The graph contains no WORLD, PARTITION, PMARK, or rollback payload.
The reciprocal solid and void region and shell chains reach the same six
faces. Each face has its own loop and the 24 fins bind their local loop and
edge mates. The body owns the twelve edges and eight vertices. All eight
points span the independently specified box bounds in metres.

Nine attributes belong to the BODY and eighteen belong to the six FACE
owners. All seven owner chains and twelve definition-type chains resolve
within the transmit. Each declaration identifier, populated value slot and
owner resolves to a typed resident node. All twelve definitions match the
prism catalog's type ID, action codes, legal-owner flags and field kinds.
The [attribute catalog](../../tooling/sw2026/para/rectangle/Attributes.py)
and [slot receipt](../measurements/2026/ImportedLocalBodyKernel01.json)
record the exact comparison.

Twelve nonresident pointers occur, all in `ATTRIB_DEF.next`. The saved
transmit uses them even though each local definition and attribute is
reachable from BODY. Their targets and native resolution remain unproven.
The audit carries these values through the disclosed memory comparison. The
closed-graph encode entry point rejects any nonresident link.
[Definition link gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/LocalBodyDefinitionsCanLinkOutsideTransmit.md)

## Reuse for later construction

The shared node writer, current schema descriptors and compression frame
already cover this profile. The [prism topology projection](../../tooling/sw2026/para/rectangle/Geometry.py#L95)
has the corresponding planar body, shell, region and fin structures.
Its [topology completion](../../tooling/sw2026/para/rectangle/RectanglePartition.py#L77)
includes three-fin vertex incidence for the ordinary prism family.
Reuse these pieces for their proven topology after separating the
ordinary WORLD owner and mark input from the body.

The [per-owner attribute installer](../../tooling/sw2026/para/rectangle/AttributeChains.py#L53)
also supplies the local owner chain and the single type list and pointer-block
structure. Its [ordinary registration wrapper](../../tooling/sw2026/para/rectangle/AttributeChains.py#L111)
installs a definition head on WORLD. The local transmit needs its own
definition link rule and its imported feature, body name and persistent ID
values derived from their actual owners. Resolve whether the native receive
path ignores, rebinds, or requires the twelve nonresident links before
constructing a fresh payload. The disclosed replay establishes no general
neutral B-rep lowering or native writer acceptance.

## Reproduce the disclosed measurement

```sh
PYTHONPATH=src:re/tooling/sw2026:re/tooling/sw2026/serial \
  uv run --offline --no-project --python 3.13 python -B \
  re/tooling/sw2026/imported_body_source/LocalBodyKernel.py "$DISCLOSED_PART"
```

The process requires the pinned disclosed source and prints the numeric
receipt. It saves no reconstructed bytes and contributes zero generated
SOLIDWORKS outputs or held-out acceptance credit.
