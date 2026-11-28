# Disclosed offset-plane typed source audit

Task `B04-SW2026-REFPLANES`; owner `/root/assembly_occurrence`; delivery PR #121. This is a prepared readback boundary for the [offset source protocol](ReferencePlaneConstruction2026.md), after the [dimension ownership retry](ReferencePlaneDimensionOwnership2026.md). Root owns native execution and shared registers. No new writer, generated native file or source-model observation is introduced by this preparation.

## Exact reader extension

[ReferencePlaneReadRules.py](../../tooling/sw2026/serial/ReferencePlaneReadRules.py) explicitly extends a fresh research registry with only two provisional schemas. It does not enter the shared `defs` auto-registration package and does not change an existing serializer or SDK reader.

| Class | Exact pinned native rule | Added readback |
| --- | --- | --- |
| `moRefPlaneDistanceGeom_c` | `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, serializer `0x4c2d8ae0` | Complete existing geometry base, `f64 f38`, canonical reverse byte `f40`, `i32 f44` |
| `moConstraintRefplaneData_c` | Same module, shared serializer `0x4b8e2ac0` | Complete existing common plane data, then the existing three-slot constraint-interface object at `f88` |

The concrete default constructor publishes the base archive name, as independently proved by [runtime-class publication](ReferencePlaneRuntimePublication2026.md). The initial RTTI-name preparation was superseded before any source read. The extension requires explicit archive version `19000` and ordinary serialization conditions `0`. It refuses an existing schema with either new name. Both new schemas remain provisional until source correlation; the native rules and their [concrete construction bindings](ReferencePlaneManagedConstruction2026.md) establish framing, not complete authored-state classification. Angle geometry/angle data, other selected entities, the compatibility face-plane route and other versions remain outside this tool's admitted offset profile.

The source projection requires a typed `moPart_c`, the named authored plane, its actual principal parent, the named profile and its boss. It measures the exact ordered geometry triplet, distance/reverse/count inputs, selected wrapper and component/datum handles, common stored origin/normal/transform, selected-location UV and point, profile-to-plane handle, boss depth and native scalar parameters. Common plane runtime owner `f10` is not a serialized member; it is never invented as a file field. Stored transform direction and complete display/publication state remain separate open rules.

## Custody and native prerequisites

[AuditReferencePlaneSources.py](../../tooling/sw2026/serial/AuditReferencePlaneSources.py) accepts only explicit case IDs `D01`–`D04`. It requires an absolute canonical `Source.json`, its supplied SHA-256, the exact independently authored disclosed JSON and every frozen source-tool hash. It checks before/author/reopen/after public phase receipts, four distinct ordered native process identities, healthy terminal states, identical original/edited native manifests and the saved-author snapshot hash before opening a model.

A process audit hook restricts packet reads to the selected disclosed paths and source tools. Only the selected case's two exact native siblings may be opened; other CAD inputs and writes inside the source packet are blocked. It neither reads hidden specs, private inspection records nor hidden source/native phase subtrees. The output records actual allowed native open events. No held-out values are needed to prepare or execute the disclosed audit.

The audit reuses the production container and ordinary archive primitives, the shared SDK configuration-manager bridge and the existing versioned research Config/Resolved readers. Six scoped streams must consume completely and round-trip byte-identically: `Config-0`, linked `Config-0-ResolvedFeatures`, both headers, `CMgr` and `CMgrHdr2`. Config re-emission must produce the same inherited map seed used by ResolvedFeatures. The receipt retains schema usage, remaining provisional owners and raw-operation counts. Byte identity does not establish generative construction or production admission.

The original and edited projections compare the stored distance, native API distance, declared reverse/count, selected principal ID/kind, cached origin/normal, profile support and boss depth against the independently authored case and its math prediction. The edit must preserve feature/support identity and slot classes, change the declared distance and stored origin, and preserve boss depth. A different native concrete owner, missing schema, unread tail, unknown mode, changed source or failed correlation is an explicit failed audit; no spans, offsets or recorded rows repair it.

## Prepared source snapshot

[Preparation receipt](../measurements/2026/ReferencePlaneSourceAuditPreparation01.json), SHA-256 `267c0132aa16c3a31c2aef95db55efd7285f400a815952ff98af3ea1a1a32d30`, binds the two new tool hashes, a source-only private snapshot of 3,423 Python files and its executable request. The code manifest is SHA-256 `6032cfbe11b27830914cea2b1a0e2a3e95103e660ab63a4655f1d6b0763ae7df`; the private recipe is `838af77b1a37ce9a24d5e8efc26b3fd4be39bc20f60d0db8f0710c697fa3bc7d`. The snapshot contains repository Python sources only, never vendor software or native source payloads.

The frozen invocation points at source packet `c05c429097c4ad94177afd3cddd9535ca373a31e6dcfa845375d9c09c96d2e89` and disclosed `D01`. Root can repeat it for another explicitly declared disclosed case using a separate unused output. Run it only after the required native source phases and trailing bracket pass. A typical invocation is:

```sh
python -B /absolute/frozen/CodeRoot/re/tooling/sw2026/serial/AuditReferencePlaneSources.py \
  /absolute/source/Source.json --packet-sha256 SOURCE_SHA256 \
  --case D01 --output /absolute/unused/D01.json
```

Python parsing and real-process admission checks passed: `H01` was rejected by argument admission, a relative packet was rejected, and the frozen process rejected the still-incomplete disclosed native prerequisites without opening models or publishing a result. No native source file was decoded and no native schema round-trip was executed during preparation. The new actual source correlation, expanded field classification and native generated acceptance remain unfinished.

## First executed disclosed audit

After source packet 03 completed healthy `D01` author/reopen brackets, root authorized the frozen snapshot above. The exact process returned `3`; receipt SHA-256 `14623835f6e73dd85aa705f9b86c3d1eb70d926c05f5a80488e8c05065e62b86`. Both siblings passed the six complete stream round-trips and inherited-map re-emission before the projection rejected their actual `moFaceRefPlnData_c` owner. The process audit recorded only the two declared disclosed native siblings, six native open events, zero denied events and zero writes. This is a successful fail-closed branch boundary, not a successful complete source projection.

The [separate native source receipt](../measurements/2026/ReferencePlaneSourceD01Native01.json) qualifies the actual source author/edit/save/reopen and measures the persistent compatibility distance display/handle/parameter graph. That branch was already identified from the managed `Distance_c.CreateData` path. The new constrained owner schemas remain provisional and were not exercised by this saved source. A subsequent explicit compatibility projection must use that native field/constructor evidence and preserve this first failed audit; no captured rows or fallback bytes may be added. Hidden sources remain sealed and no writer is enabled.
