# Generated downstream collector and face operands, SOLIDWORKS 2026

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID` is delivered in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). Root owns the construction and native qualification. The source rules apply to SOLIDWORKS 2026 SP05.2 build `34.5.2.0604` and archive version 19000.

## Shared part allocation

The active generated Parasolid partition supplies the body and its linked faces and edges. The projection follows that chain independently of the order of nodes in the decoded table. It verifies a single world-owned solid and checks every attached `DOWNSTREAM_FACE_ID` and `DOWNSTREAM_EDGE_ID` array against the same fresh allocation. In this profile the face IDs occupy the first consecutive range, then the edge IDs. The retained model update second must contain the allocation's FILETIME.

| Body field | Producer |
| --- | --- |
| `f08` | The first unused ID from that allocation. |
| `f0c, f10, f14, f18` | The target archive version and build date code in the finalized prefix. |
| `f1c, f20, f28` | The actual configuration ModelHeader's update counter, body counter and update time. |
| `f30, f38` | The allocation's explicit cache GUID and its two unsigned UTF-16 polynomial hash words. |
| `f40` | The first-seen generated surface representations in the linked face order. Each retained member is a new typed clone with its own file owner. |

The two exercised single-boss cylinders each have one sketch-derived side and two caps with distinct end selectors. Their three semantic keys are distinct. The projection derives the keys from `FACE_ID_2001` on each actual generated face, the corresponding surface carrier, producing feature, profile marker or end selector, and actual local file and configuration. The [collector membership record](DownstreamIdentityMembership2026.md) binds the native comparison, first-seen traversal and transfer. The [copy record](DownstreamCollectedSurfaceClones2026.md) explains the separate file owners and shared definitions.

For edge collection, `moEdge_c::getMultiEdgeId` at `0x4be81980` calls the selected kernel query through `0x43b38cd0` and `0x43e80f50`. The Parasolid implementation at `0x32fa26d0` queries the actual `EDGE_PERM_ID_2001` definition at `0x3312d718` through `0x330384d0`. A zero result returns without contributing a member. The emitted cylinders have zero of those attributes and two separate `DOWNSTREAM_EDGE_ID` records. A positive permanent-ID inventory requires the corresponding typed edge representations. Complete source fragment hashes and the separate generated inventory are retained in the [measurement receipt](../measurements/2026/DownstreamGeneratedCollector01.json).

## Ordinary one-loop face operands

The same allocation supplies the starting operands for six face rows on each generated rectangular boss. Each row uses the selected face, the right faces of the four reciprocal fins in the selected loop's coedge order, and a terminal null. The initial role map uses the allocated row IDs of adjacent faces already registered at that moment. The selected row is registered after constructing those operands. The full pre-store validator may replace them. [Native face construction](DownstreamFreshFaceRows2026.md) · [Role ordering gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/FaceRoleMapUsesPreviouslyAllocatedRows.md)

A separate read-only inventory parsed 152 tracked, disclosed part, assembly and drawing containers across the repository examples and ten 2026 corpus folders. None contained a name ending in `-DownstreamIdData`. That inventory supplies a negative observation for the listed sources and no native cache-body fixture. [Directory inventory receipt](../measurements/2026/DownstreamGeneratedCollector01.json)

## Process verification

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  python -B -m downstream.CheckCollectorProjection 1
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  python -B -m downstream.CheckFaceOperands 1
```

Run both commands with variant `2` for the second designs. Two fresh processes per command and variant reproduce the same receipts. Each cylinder produces a 736-byte typed cache-body witness with three members and preserves the eleven originally generated part streams. Each prism reproduces 36 inline operands and twelve earlier-face role values against a separate walk of its emitted partition. Both checks also reverse the in-memory node table while retaining its links, then compare the resulting values. The four regular inputs reject eight invalid allocation or collector combinations and four invalid face topology or mode combinations across the distinct variants.

Eight earlier partition, boundary, surface and clone process exercises also pass. The four surface and clone receipts match their prior versions byte-for-byte. The guards recorded zero file opens, outbound connections or subprocess launches after Python package initialization. The cache-body witness contains the prefix and collector members, and the face proof terminates at the constructor operands. Native population of the remaining collections, the final face wrappers, independent linked drawing lifecycles and held-out corpus qualification remain open. [Process receipt](../measurements/2026/DownstreamGeneratedCollector01.json)
