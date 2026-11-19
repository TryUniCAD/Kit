# Concentric kernel face identities in SOLIDWORKS 2026

Task `B04-SW2026-MATES-CONCENTRIC`; owner `assembly_occurrence`; delivery PR #121. This supplements the immutable [face/snapshot field mapping](ConcentricFaceIdentity2026.md). It establishes the actual saved child kernel owners behind the separately serialized mate endpoints. It does not generate a new kernel face number, construct an endpoint, or qualify a concentric writer. Dependencies are the SDK's active partition and history readers, linked native part archive reader, actual header `DatumTime` rule, [analytic schema work](SdkRevolveBodyNames2026.md), and disclosed D01–D03 source locks. Exit for this tranche is full six-child typed parsing, exact twelve-endpoint correlation, deterministic process evidence and explicit construction limits.

[Sanitized receipt](../measurements/2026/ConcentricKernelFaceIdentity01.json) · [Native supplement](ConcentricKernelFaceIdentity2026.json) · [Auditor](../../tooling/sw2026/AuditConcentricKernelFaces.py) · [Process replay](../../tooling/sw2026/RunConcentricKernelFaces.py) · [Native collector](../../tooling/sw2026/CollectConcentricEdgeAttributes.py)

## Typed cylinder closure

The previous tranche honestly stopped at its then-unqualified partition kind `51`. This separate replay uses the exact `AnalyticShapes.py` supplied by the independent body-name lane: SHA-256 `5c5fbbcab060e8c4a4d035adc429afc7649f27e663d653959de0e9609c490979`, bound by source-stageable manifest `64e185c02e680a277e1ced16cae0fc8691b0f0d76e512db9bccd50199ec1d8ba`. That file is the only SDK delta against the first frozen circle/face-reader closure. No SDK source is duplicated in this supplement.

Kind `51` uses ordered fields `node_id`, `attributes_features`, `owner`, `next`, `previous`, `geometric_owner`, `sense`, `pvec`, `axis`, `radius`, `x_axis`. Radius precedes `x_axis`. The related kind `31` circle uses `centre`, `normal`, `x_axis`, `radius` after its common ownership prefix. The ordinary point, line and plane entries remain unchanged.

Both original and edited partitions now parse completely, with checked active graph references and rollback histories. There are 96 active nodes per original and 92 per edited child, 564 across all six. Each has exactly three faces: one cylinder and two plane caps. The selected cylinder surface's actual `owner` points back to that face, whose shell resolves to the actual body.

## Actual identity correlation

| Owner or field | Source-derived relationship | Verified scope |
| --- | --- | --- |
| `moFacetedData_c.f40` | Equals the cylindrical face's `node_id` | All 12 saved endpoint pairs |
| `moFacetedData_c.f50` | Equals the body's `ATOM_ID_2001` integer, also the actual extrusion's `moAtom_c.f140` | All 12 pairs, with independent child archive ownership |
| Lateral `FACE_ID_2001` | Integer vector `[74, extrusion_id, first_creation_epoch, flags, arc_permanent_marker]` | All six actual kernel faces; actual flags are zero here |
| Active side representation | `moFR.f10.f00`, `moFR.f10.f08`, and `moFromSktEntSurfIdRep_c.f38` match that kernel vector's extrusion ID, creation epoch and permanent marker | All 12 active pairs |
| Two plane-cap `FACE_ID_2001` vectors | `[40, extrusion_id, first_creation_epoch, flags, cap_role, contour]` match the two adjacent `moEndFaceSurfIdRep_c` owners | All 12 pairs, compared as a set; no cap traversal order inferred |
| Active `moCylinderRef_w.f108` | Equals the actual child-local cylinder surface `axis` | All 12 pairs; D03 distinguishes this from the wrapper's world axis |

The body and face attribute definitions are found by their actual owned attribute chain and native name, never by fixed stream positions. The auditor requires the selected face, body, atom, profile, arc and feature references to resolve unambiguously. It derives creation time from the actual header and actual extrusion ID. It preserves the distinct arc permanent-marker `f08` and creation-ID `f0c` roles established by the earlier native binding.

The cylindrical face's transmit object index is `41` before the edit and `39` after it. Its actual kernel face `node_id` remains `27`. The body atom is measured as `101`. These values describe this corpus only. The demonstrated rule is to resolve the true owner and its ID, not to emit those repeated numbers as constants or use a face-array index.

## Supplemental publication trace

The [native collector](../../tooling/sw2026/CollectConcentricEdgeAttributes.py) verifies original `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` and `sldgcu.dll` SHA-256 `77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594`. It retains function/fragment hashes and numeric call edges, with no vendor listings or bytes.

`sgEntHandle::makeEdge` at `0x4ba9e830` gets the actual sketch entity through slot `+0x378`, makes a kernel edge through actual entity slot `+0x88`, and, when argument bit `1` is set and an edge exists, publishes the actual entity pointer into `edgeId_ad`. The pointer publication occurs at `0x4ba9e8ed` through the imported `gcPointerAttrib_w::makeAttribute(..., void*)`. It does not read the entity permanent marker in that branch.

`gcEdge_w::propagateEdgeIds` at `0x439bac50` calls the helper at `0x439bbfd0`, passing the destination `fromEdgeId_ad` attribute. The helper copies non-null single pointer values, or a three-pointer payload, from `edgeId_ad` to the destination face attribute. The relevant single-pointer read/write sites are `0x439bc043` and `0x439bc056`; the three-pointer store is `0x439bc070`. This helper does not convert a sketch-entity pointer into its permanent marker. Its complete body is five contiguous unwind fragments, ending at `0x439bc0bd`; the first exception range alone covers only eight bytes and is not the full body.

The unsigned `gcEdge_w::assignId` and `getId` exports are forwarding thunks through the geometry kernel switch to `sldgciParau` methods. Those unsigned APIs and pointer-valued sketch attributes must not be assumed interchangeable. The prior confirmed final surface-assignment edge remains valid: it consumes the face `fromEdgeId_ad` value and creates the actual feature-owned surface representation. The missing upstream conversion/publication decision remains open, rather than being filled by the coincident observed integer values.

## Verification and remaining work

Eight isolated host processes passed: seven process-boundary checks plus one exact-build collector. Two fresh SDK audits produce identical owner receipts. Five negative probes reject using a transmit index as face ID, selecting a cap face, changing the marker, changing the body atom and substituting the world axis for the child-local optional vector. The six child files, disclosed graph, locks, tools and full SDK source closure remain unchanged. No VM, COM, hidden input, writer output or Hopper session was used.

This qualifies saved owner consistency only. Fresh kernel node numbering, end-to-end sketch permanent-marker publication, optional `f108` construction/presence conditions, faceted snapshot omission/recovery, and fresh concentric endpoint construction still need their own rules and native acceptance. A fully typed read does not establish a source-free writer. The original early class-51 stopping receipt is retained unchanged.

[Identity-domain gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Assembly/Mates/KernelFaceIdsAreNotTransmitIndexes.md) · [Change entry](../../../Documentation/Changes/Solidworks/Research/ConcentricKernelIdentityAudit.md)
