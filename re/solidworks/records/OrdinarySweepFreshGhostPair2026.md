# Model-only ghost partition for the ordinary SOLIDWORKS sweep

The fresh ghost composer takes the two independent SI radii and an actual allocated sweep owned by a fresh part. It allocates the Section and Path ghost IDs from the current model seed, builds the two analytic input bodies, attributes them, and emits one typed partition and its companion inline manager. The composer and observer stay in research. [Ghost owner evidence](OrdinarySweepGhostOwnership2026.md) [Model-only receipt](../measurements/2026/OrdinarySweepFreshGhostPair01.json)

The existing `MakeModelSeeds` supplies the initial manager, and the native positive allocation branch advances that counter once for each actual support. The model's sweep allocator independently assigns the live sweep ID. Both manager rows use that exact ID. Its packed count comes from the two new rows and its body-present flag comes from the constructed two-body partition profile. The existing typed Config write schemas independently reproduce the complete 72-byte manager, including both distinct ghost IDs and no archive-map allocations. [Exact allocator and serializer](../measurements/2026/OrdinarySweepConstructorAnchors01.json)

The shared `MakePrismNodes` allocator builds each isolated support body. The ghost composer relocates every actual typed pointer with its local-to-partition map, allocates a common WORLD and native attribute definitions, and binds one body attribute to its actual ghost ID and one empty edge attribute to the actual rim. The local node IDs remain separate from those new transmit addresses. All cells are created in memory and passed to the shared current typed kernel serializer and compressor. The fresh WORLD and ordered body links are independently decoded. The source archive's historical node ordering and reclaimed IDs stay a separate observation.

The two physical attribute definitions are shared within the generated partition. Exact `sldgciParau` `gci_InitGcAttribs` builds `GHOST_REF_BODY_ID_2001` from the registered body type at `0x32f9ed9c` and `EDGE_ID_2001` from the registered edge type at `0x32f9ef2e`. Both modern names dispatch to the shared definition constructor at `0x32f9d010`. The measured types, legal owner masks, action and field kinds agree across the two native source geometries and all four edits. This tranche uses those exact definitions for a matching one-wire and one-sheet model. [Registered definitions](../measurements/2026/OrdinarySweepGhostAttributeRegistration01.json)

| Independent authored input | Map consumer ID | Raw bytes | Compressed bytes | Stream SHA-256 |
| --- | ---: | ---: | ---: | --- |
| Near | 173 | 2140 | 1066 | `0ab990a2217590c31c5dda0853bb4e6564f161bbcda202255169192aae13bc9c` |
| Wide | 174 | 2140 | 1065 | `20be6593e1b0bd0f18f82c9336dc519ad5ac05ffedea8696b2f8322a12cddd47` |

Both positive cases use the public [disclosed source specification](../../tooling/sw2026/sweep_source/DisclosedSweepInputs.json) and are computed without a source CAD file. Their guarded fresh process checks all 36 typed cells, exact wrapper re-emission, actual owner attributes and analytic support geometry. Foreign owners, an unallocated sweep, an altered manager and out-of-profile radii refuse. The six previously qualified source replays retain their same stream digests, maps and ownership comparisons after sharing the path node construction.

Evaluate the populated ghost partition with the future complete generated sweep. Restoring the attributed ghost partition and the editable path requires a native trial beyond the passing standalone sheet exchange. The remaining constructor boundary is the live path sketch, Section state fields and complete sweep feature/atom and side-owner generation. Full part and held-out qualification remain open.

```sh
python3.14 -I -B re/tooling/sw2026/sweep_source/AuditSweepGhostPair.py --model-only
python3.14 -I -B re/tooling/sw2026/sweep_source/AuditSweepGhostPair.py --licensed-bin /path/to/licensed/bin
python3.14 -I -B re/tooling/sw2026/sweep_source/AuditSweepGhostPair.py --emit SweepArcNear > /tmp/unused-sweep-ghost-stream
```

[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) [Writer modeling](../../Playbook/WriterModel.md)
