# Concentric face and faceted snapshot identities in SOLIDWORKS 2026

Task `B04-SW2026-MATES-CONCENTRIC`; owner `assembly_occurrence`; delivery PR #121. This is an offline source-identity investigation. It does not construct a concentric endpoint or qualify a writer. Dependencies are the [linked archive mapping](ConcentricMateArchive2026.md), the [circle field plan](CircleDimensionFieldPlan2026.json), the [feature-reference creation rule](ModelConstruction2026.md#feature-reference-creation-time) and the existing SDK Header → Config → Resolved readers. Exit for this tranche is a reproducible exact-build field binding, twelve actual disclosed owner correlations, immutable process evidence and explicit unresolved construction edges. Full native and held-out writer acceptance remain separate.

[Native bindings](ConcentricFaceIdentity2026.json) · [Sanitized receipt](../measurements/2026/ConcentricFaceIdentity01.json) · [Owner auditor](../../tooling/sw2026/AuditConcentricFaceOwners.py) · [Process replay](../../tooling/sw2026/RunConcentricFaceIdentity.py)

## Distinct owner domains

The source packet's D01, D02 and D03 each provide an original child and an edited child. The auditor checks their declared lock hashes before decoding. It reads all six complete ordinary Header, Config and Resolved graphs through the real SDK. It consumes only the separately hash-bound disclosed parent graph; no hidden inputs or native application are involved.

For each active endpoint, the actual ownership path is:

`moMateConcentric.f410[row].o → moCylinderRef_w.f58 → moCompFace_c.fe8 → moFaceRef_c.f10[0].f08 → moFromSktEntSurfIdRep_c`

The child ownership path is:

`moExtrusion_c.f60.list.items[0].o → moProfileFeature_c.pd_f80 → sgSketch.arcs[0].arc`

The surface representation's `f10.f10` selects a `moFR_c`. Its `f10.f00` resolves to the actual extrusion's persistent `f08`, and its `f10.f08` equals `DatumTime(actual_child_header, actual_extrusion_id)`. The recorded child sketch and extrusion IDs are distinct. Those measured numbers identify these controls only; a constructor must use its actual allocated nodes. The reference epoch matches the extrusion's first creation event in all six child states and remains unchanged by the later depth edits. It is not the profile's creation event, a feature FILETIME or the file save epoch.

The representation's `f38` matches the generating arc's permanent marker `f08`. Arc creation ID `f0c` is a different owner. The two values happen to coincide in these one-arc controls. This comparison does not establish that they are interchangeable.

## Native binding

All addresses use the original x64 `sldmodu.dll`, build `34.5.2.0604`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The [collector](../../tooling/sw2026/CollectConcentricFaceIdentity.py) verifies the image, whole exception-directory ranges, direct call edges, primary tables and simple native field getters. It emits numeric rules and hashes, never vendor bytes or decompiled listings.

| Native owner | Exact evidence | Interpretation and status |
| --- | --- | --- |
| Ordinary selected arc | Runtime descriptor `0x4dafb0e8` → factory `0x4c5780d0` → constructor `0x4c55d940` → primary table `0x4d1c5ae8`; table slot `+0x378` is `0x4c562f20` | The concrete entity receiver selects the actual arc through the handle's sketch and index; confirmed static |
| Permanent marker | `sgEntHandle::getPermanentMarker` at `0x4c5c7740`; ordinary non-block call at `0x4c5c780d` → direct integer getter `0x4b283ba0` | Reads the selected entity at member `+0x08`; confirmed static |
| Surface construction | `makeFromSktEntSurfaceId` at `0x4c6d2b00` → constructor `0x4c6c2870`; member write at `0x4c6c28d0` | Actual `moModelFeature_c` owner plus unsigned entity input; the latter becomes representation `f38`; confirmed static |
| Reference keeper | Constructor call at `0x4c6c28a5` → `0x4bb5d2a0` | Uses the actual supplied feature; the FR creation rule is shared with existing constructors |
| Lateral assignment | `moMakeFromExtendedEdgeSurfIds` at `0x4b788170`; surface factory call `0x4b7883f5` | Reads the face's `fromEdgeId_ad` kernel pointer attribute, passes its integer value and the actual extrusion into the surface constructor; confirmed at this edge |

The complete upstream sketch-marker → kernel `fromEdgeId_ad` publication edge has not been traced end to end in this tranche. The permanent-marker domain, the constructor input and twelve disclosed correlations are supported separately. No stronger causal claim or new writer admission is made.

## Faceted support snapshot

The separate support path is:

`moMateConcentric.f3c8[row].o → moCylinderRef_w.f58 → moCompRefCylinder_c.fb0 → moFacetedData_c`

It is distinct from the active `moCompFace_c` path above.

| Snapshot field | Exact native binding | Construction meaning |
| --- | --- | --- |
| `f40` | `getFaceID` at `0x4b286570` reads `+0x40`; graphics path `0x4b7fa3d0` calls imported `sldgcu!gcEnt_w::getNodeId` through IAT `0x4cd380d8` | Actual kernel face node identity; observed values are not fresh-file defaults |
| `f50` | `getBodyID` at `0x4b283940` reads `+0x50`; same graphics path calls `sldgcu!gcBody_w::getAtomId` through IAT `0x4cd38788` | Actual body atom identity; matches the real child extrusion's one `f528` atom and that atom's `f140` in all twelve endpoints |
| `f54` | `getFeatID` at `0x4b286690` reads `+0x54` | A separate feature identity field; ordinary direct-face graphics construction supplies its no-feature value |
| `f58` | Graphics call `0x4b7fa672` → `moFace::getFaceIdStrWithMultiSurfIds` at `0x4be98610`; surface primary slot `+0xa0` → `0x4ba878b0`, with base text `0x4c6ce4a0` | Ordinary single-surface text is computed from the concrete class name, actual FR feature ID and representation entity ID, followed by comma-space and newline |

For the admitted single-side identity, the text rule is `class_name + ',' + decimal(extrusion_id) + ',' + decimal(arc_permanent_marker) + ', \n'`. The exact native `'%s,%d'` append format and comma-space separator are independently read from the pinned image. The auditor computes this text from the actual child owners and compares it with all twelve snapshots. It does not load a recorded text value into a writer.

The member constructor `[0x4b7e9c60,0x4b7e9dc0)` stores its supplied face, body, edge, vertex and feature identity arguments separately. Its empty constructor `[0x4b7e9dc0,0x4b7e9e1f)` initializes the identity words to `-1`. Those defaults do not prove that replacing a populated snapshot's face identity, or omitting the snapshot, is load/save safe. The lookup at `0x4b7ff2c0` forwards the actual body ID, face ID and identity text to the model's graphics manager. Its recovery behavior remains unmeasured here.

## Verification and limits

Eight fresh host processes passed: one exact-build collector, two deterministic real SDK owner audits and five negative consistency probes. Each positive audit reads the six actual child files and checks twelve active/snapshot endpoint pairs. Replacing the marker, extrusion ID, creation epoch, body atom ID or exact identity text is rejected. Inputs, tools and the full SDK source closure remain unchanged. No unit test, VM operation, COM call, hidden input or writer output was used.

A separate honest typed kernel probe reaches the first unqualified cylinder record, class `51`, before the face inventory. It retains the exact stopping point and does not claim a complete partition parse. This tranche therefore does not derive the actual kernel face node number from a fresh parametric model. The source controls' repeated face-node and body-atom numbers must not become constants in a constructor.

The next useful experiment is an independently bracketed disclosed load/edit/save/reopen diagnostic for the faceted support owner, separate from actual endpoint generation. Keep every active face identity and its occurrence ownership intact. An optional-owner result would qualify only its measured scope. The new concentric writer still needs the missing construction/publication edges, complete endpoint topology and vector rules, native acceptance and blinded generalization.

[Snapshot identity gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Assembly/Mates/ConcentricSnapshotIdsNeedKernelOwners.md) · [Change entry](../../../Documentation/Changes/Solidworks/Research/ConcentricFaceIdentityMapping.md)
