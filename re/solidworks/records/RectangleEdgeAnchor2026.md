# Forward fin anchors for a generated 2026 rectangular solid

The [rectangle geometry constructor](../../tooling/sw2026/para/rectangle/Geometry.py)
selects each `EDGE.halfedge` from the authored edge orientation. The
selected fin ends at the authored edge end. Its mate ends at the authored
edge start. An ordinary straight segment has exactly one such fin in the
generated closed prism.

## Pinned kernel evidence

Parasolid kernel `pskernel.dll` has SHA-256
`2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969`.
Addresses use the preferred x64 PE image base `0x180000000`.

| Kernel owner | Ordinary solid branch |
| --- | --- |
| `PK_EDGE_ask_first_fin` (`0x18020ec40`) | `0x18020efa1` and `0x18020f012` select the runtime edge pointer at offset `0x50`. `0x18020efed` loads the anchor. With its loop present, the branch through `0x18020eff4–0x18020eff7` keeps that fin and writes its tag at `0x18020f054`. |
| `PK_EDGE_ask_vertices` (`0x1802125d0`) | The edge's same anchor slot is selected at `0x180212931–0x180212935`. With a terminal vertex present, `0x1802129be–0x1802129d4` follows anchor `+0x30` (mate) and `+0x28` (terminal vertex) to fill output vertex zero. `0x1802129d8–0x1802129ed` fills output vertex one from the anchor's own terminal. |

The six disclosed L1, P0, C1a, C1b, A13 and A14 rectangles have all 72
edge roots pointing to the positive fin. For each root, the chord from
its mate's vertex to its own vertex agrees with the supporting line's
positive direction. The original generated case disagrees on five edges.
Its outward faces and closed topology still satisfy the analytic geometry
checks. The edge anchor determines an additional ordered relation.
[Endpoint ordering gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/ParasolidEdgeHeadSetsEndpointOrder.md).

## Single-variable native probe

The [probe generator](../../tooling/sw2026/para/rectangle/CheckEdgeAnchors.py)
builds the corrected 23.25 × 14.5 × 8.75 mm part from the same neutral
request and deterministic attachment session used for the original. The
fresh construction and readback run under the file-open guard. The
comparison then reads the frozen generated original and checks the
identical encoded path, input dimensions, analytic geometry and neutral
request. [Original generation evidence](../measurements/2026/GeneratedRectangleAttachment03.json).

Only `Contents/Config-0-Partition` differs. The ten other logical streams
are byte-identical. The active payload length stays 6627 bytes and its
only changed bytes are at offsets 1705, 1737, 1769, 1801 and 1961 measured
from the first byte of the decoded partition payload. Each is the low
byte of one encoded edge-to-fin pointer. The 661-byte stored rollback
section is byte-identical with SHA-256
`53d059e585037824e397c70d4948a9a58c36f8bf9a4f0248a8c56d0ac1ade0d2`.
Both parts have the same transmit record order, index assignments,
history graph, attributes, independent mass properties and outward
face winding. [Exact stream and field comparison](../measurements/2026/GeneratedRectangleEdgeAnchor01.json).

```sh
PYTHONPATH=src:re/tooling/sw2026:re/tooling/sw2026/serial:. \
  python3.14 -B -m para.rectangle.CheckEdgeAnchors /absolute/old-deck /absolute/empty-output
```

Stage `AnchorFreeze.json`, `EdgeAnchorJob01.json` and the original and
corrected comparison copies under the original encoded guest stage. Run
the updated [standalone inspector](../../tooling/sw2026/InspectRectanglePartitionOpen.py)
from an independent tools folder. It retains the original idle guard,
two healthy L1 process controls, same-path comparison, and frozen hashes.
It captures open errors, warnings, bodies, feature ownership and geometry
before and after explicit rebuild. The original-warning and corrected-open
observations have separate result fields.

## Native result

Both generated parts opened with warning 32 and zero solids on
SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`. The comparison used four distinct
processes. Both L1 controls passed, and the staged input hashes matched
their originals after close. The runner came from commit
`6353bf9aa45cdbc4489892b1616e8fc276151f97`.
[Native comparison receipt](../measurements/2026/GeneratedRectangleEdgeAnchorNative01.json).

| Variant | Opened | Errors | Warnings | Solids after open | Rebuild returned | Solids after rebuild | Update stamp |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| Original attachment | Yes | 0 | 32 | 0 | True | 1 | 110 → 125 |
| Forward fin anchors | Yes | 0 | 32 | 0 | True | 1 | 110 → 125 |

Both cases reported `NeedsRebuild2=0` and `What's Wrong=0` before and
after explicit rebuild. Each rebuilt solid had six extrusion-owned faces,
volume 2949.84375 mm³, area 1334.875 mm² and centre
`(14.25, -5.5, 4.375)` mm. The five-anchor correction establishes the
authored endpoint order. The cache-open failure persists with those
anchors, and its receive or attachment stage remains unobserved.

The earlier standalone projection and attachment receipts identify the
original edge selection. Their hashes remain the basis for reproducing
the historical comparison. [Original native observation](../measurements/2026/GeneratedRectangleAttachmentNative04.json).
