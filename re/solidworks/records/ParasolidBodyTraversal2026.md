# Parasolid 37.01.250 plain body traversal

Task `B04-SW2026-DRAWING-KERNEL-ORDER`, owner `configuration_header`, delivery PR #121. The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) and [RE playbook](../../Playbook/README.md) govern this source-only result. It supplies the traversal dependency for the [drawing downstream map](DrawingDetailingEdgeMap2026.md); it does not qualify a writer or a new native trace.

For the demonstrated ordinary body, list order comes from topology links. The kernel does not walk each face's fins and deduplicate first encounters, sort tags, use transmit-record order, or consult a separate order table in these paths.

## Exact source and fields

The original external `PSKERNEL.dll` is version `37.01.250`, 72,681,488 bytes, SHA-256 `2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969`, preferred base `0x180000000`. [Numeric/source ledger](ParasolidBodyTraversal2026.json) pins six complete API bodies, their PE-unwind fragments and five complete field-registration leaves. No binary or vendor instruction listing is included.

| Field | Runtime member |
| --- | --- |
| `BODY.owner` / `BODY.shell` | `+0xb8` / `+0xc8` |
| `BODY.region` / `BODY.edge` / `BODY.child` | `+0x100` / `+0x108` / `+0x138` |
| `REGION.next` / `REGION.shell` | `+0x18` / `+0x28` |
| `SHELL.next` / `SHELL.face` / `SHELL.edge` / `SHELL.region` | `+0x18` / `+0x20` / `+0x28` / `+0x38` |
| `FACE.next` / `EDGE.next` | `+0x48` / `+0x60` |

The field names and runtime offsets come from the original registration functions, independently of the traversal guesses. Each field descriptor carries its runtime offset at `+0x28`. The five registration leaves start at `0x181432890` (`BODY`), `0x18144b000` (`REGION`), `0x1814534d0` (`SHELL`), `0x18143e4c0` (`EDGE`) and `0x18143f390` (`FACE`). These are decoded straight-line leaves with exact return boundaries. Offsets above refer to kernel objects, not SOLIDWORKS archive nodes or transmit positions.

## Plain list recipe

1. Edge order starts with `BODY.edge`, following `EDGE.next`.
2. Traverse regions from `BODY.region` using `REGION.next`.
3. Within each region, traverse `REGION.shell` using `SHELL.next`.
4. For each shell, append its `SHELL.edge` chain through `EDGE.next`.
5. Face order uses the same region/shell traversal, appending each `SHELL.face` chain through `FACE.next`.

The direct `BODY.shell` pointer is not the region-iteration head. The parallel `front_face` chain is not appended as another set of faces. A void-side shell may have no primary faces, even though each actual face has that shell as its front-side owner. These distinctions avoid duplicate face visits.

`PK_BODY_ask_edges` (`0x1800f2050`) counts and fills through that same walk; its unfiltered fill starts at `0x1800f290f` and converts the selected edge to a tag at `0x1800f29bf`. `PK_BODY_ask_faces` (`0x1800f2b90`) does likewise; its unfiltered count/fill starts at `0x1800f3322/0x1800f33fd`, with tag emission at `0x1800f349f`.

`PK_BODY_ask_first_edge` (`0x1800f42b0`) and `PK_BODY_ask_first_face` (`0x1800f4be0`) use the same link walks to choose their first eligible entity. The ordinary next-body APIs start at `0x1802101c0` and `0x18025a280`; they follow the entity's next link and advance its shell/region ownership at chain boundaries. The linked-body-owner and entity-exclusion branches are separate scopes. They must not be silently generalized from this plain path.

The exact `sldgciParau.dll` bridge SHA-256 is `96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce`. Its array wrappers at `0x32fd8ed0/0x32fd90b0` call the two kernel APIs and preserve the returned order while widening tags. Thus the wrapper adds no independent ordering.

## Disclosed saved-topology correlation

Three already-disclosed cache inputs—L1, A13 child and A14 child—were checked independently in fresh host processes. They are three save contexts of one rectangular shape, not three independent designs and not held-out validation. Each walk exhausts one body, two regions, two shells, six faces and twelve edges with correct typed owner/backlinks and closed fin loops. Each complete partition re-encodes exactly. [Inspection receipt](../measurements/2026/ParasolidBodyTraversalSource01.json)

On all three, edge-chain order differs from first face/fin encounter order and from transmitted edge-record order. Face-chain order also differs from face-record order. These are saved-graph counterexamples to the tempting alternatives. The predicted API list is source-derived; no new live `PK_BODY_ask_*` result was observed. The initial observer's final re-emission comparison had a helper-arity error; its retained failure is an observer setup issue, and the three successful reports bind the corrected observer.

## Scope and open work

The supported rule is the ordinary plain `WORLD`-owned one-solid topology walk. Compound/body-owned subsets, ref-instance paths, framed regions, changed entity-exclusion policies, lattice/mesh topology, and arbitrary visibility or suppression semantics remain outside this tranche. It establishes how given head/next links determine order. It does not derive how a modelling operation initially chooses those heads and links from a neutral feature, or qualify a new populated cache in SOLIDWORKS.

The initial REA/Hopper analysis timed out. The logical target closed, with application cleanup still unconfirmed. The source conclusions come from the original PE and LLVM inspection.

[Order gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/BodyTraversalIsNotTransmitOrder.md) · [Change](../../../Documentation/Changes/Solidworks/Inspection/Drawings/Downstream/SolidworksKernelBodyTraversal.md)
