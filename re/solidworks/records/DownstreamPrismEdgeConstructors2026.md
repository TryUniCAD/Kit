# Generated ordinary prism edge rows in SOLIDWORKS 2026

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID` is delivered in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). Root owns the cache projection and native qualification. SOLIDWORKS 2026 SP05.2 build `34.5.2.0604` source binds the initial mode-1 edge constructor and collision-free post-insertion step for the ordinary rectangular blind boss. This record covers that stage of construction.

## Actual body and four face roles

The native body traversal at `0x4b512b00` gets the actual atom and sheet result ahead of its face and edge loops. It passes the edge, the entity kind, the owning body, sheet result and atom into batch virtual `+0xa8`. This reaches `0x4b5199b0`, which prepares the tuple for `0x4b5164c0`. That insertion stores the tuple from node `+0x18`, so the sheet result lands at `+0x1c` and the owning body at `+0x20`. The entry exists for every selected edge even without permanent representations.

The edge constructor recovers the actual body from that tuple. The sheet lookup at `0x4b519760` reads the same tuple's classification to decide reference flag `0x4`. The ordinary solid's flag is clear. Current and previous/next permanent edge lookup are independent. The active collector checks the separate representation list at `+0x130` and its edge count at `+0x12c`. The generated partition carries no permanent edge representations. [Permanent attribute distinctions](DownstreamBoundaryRoles2026.md)

Each generated line edge has exactly two live opposite-sense fins. Select the positive one. Its actual loop supplies the left face, reciprocal fin supplies the right face, and the reciprocal of the previous and next fins supplies the start and end faces. The current edge is the unique common edge of the left and right faces. All four faces are distinct and already registered. Build the four signed role pairs from those actual face row IDs and use their four existing collected surface representations by object identity. [Shared collector entries](DownstreamCollectedSurfaceOwnership2026.md)

## Constructor and retention

| Owner | Selected state |
| --- | --- |
| `moCompEdge_c` body and component | Actual underlying body atom in `f18/f1c`, own local unit component in `f58`, actual edge reference in `fe8`. Ordinary wrapper flags remain zero. |
| Composite edge base | Empty link array, `f188/f18c=0`, two default points each at `(0,0,0)`. The point constructor at `0x31dd3a20` initializes all three coordinates. |
| `moEdgeRef_c` identity and condition word | Mode 1 reaches `0x4b75ac71`, writes `f60/f64=(1,0)`, and publishes a valid classical body and nonnull positive coedge. The resulting `fe8` is `0x300`, with permanent, sheet and ghost flags clear. |
| `moEdgeRef_c` handle and data | Constructor `f70` stays zero through the mode-1 return. The two scalar sentinels remain `1e100`. Its four face role pairs are present with an empty edge list, zero face hint and zero initial vertex hints. |

Initial edge validation accepts the unique common edge obtained through the first two face roles. The key prefix is `s,` with the sheet bit clear. Concatenate the four ordered surface descriptions and apply the existing modulo-1000000009 polynomial hash. The nondegenerate anti key exchanges slots `0↔1` and `2↔3`. With neither key already present, native insertion registers the original and retains the current wrapper. This stage retains `0x300` and the zero handle. The ordinary BEnt serializer writes those supplied fields in their usual order. [Initial and post-insertion validation](DownstreamEdgeValidation2026.md)

## Reproduction

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  python -B -m downstream.CheckPrismEdgeConstructors 1
```

Repeat with variant `2`. Four guarded processes verify 24 rows and 96 collected surface references across the two designs. Independent vertex incidence derives the same four roles and kernel attribute payloads derive the same keys. Reversing the partition node table leaves operands unchanged. Two original/anti collision probes per variant refuse the unsupported path. Both cache bodies round-trip exactly with map counter 92 and preserve the eleven generated input streams. [Process receipt](../measurements/2026/DownstreamPrismReferenceReplay01.json)

The [source ledger](DownstreamPrismEdgeConstructors2026.json) and [source receipt](../measurements/2026/DownstreamPrismEdgeConstructorsSource01.json) bind the original functions, typed imports and batch virtual cell. Use the [source verifier](../../tooling/sw2026/downstream/VerifyRuntimeOwnerSources.py) against the pinned model and math modules.

This witness ends before edge lookup registration, late vertex handling and native linked drawing qualification.

The [registered cache replay](DownstreamPrismCacheRegistration2026.md) combines these retained rows with their generated lookup records.
