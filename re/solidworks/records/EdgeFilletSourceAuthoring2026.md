# Source acquisition for constant-radius edge fillets

Workstream `B04-SW2026-EDGE-FILLET-SOURCES` is part of the PR #121 takeover. The source packet covers two separately authored single-edge fillets on rectangular Front-plane blind bosses. The oracle owner runs the packet and retains the hash-bound source lock. Exit for this step requires two complete sources and edited derivatives, eight distinct native processes, clean opens and rebuilds, and healthy immutable controls. This packet supplies no format rule, writer or held-out result.

## Model and checks

The [disclosed case definitions](../../tooling/sw2026/edge_fillet_source/DisclosedFilletInputs.json) vary the stock dimensions, stock offset, selected edge, and initial and edited radius. One edge runs along the extrusion through a side corner. The second runs across one base-plane coordinate, at the far end of the extrusion and on the opposite transverse side.

The projected removed cross section is a square of side `r` minus a quarter disk. Its area is `(1 − π/4) r²`. Its centroid has inward offset `r (5/6 − π/4) / (1 − π/4)` from the corner in both transverse coordinates. The removed volume is the sectional area times the edge length. The remaining centroid comes from subtracting its first moments from those of the stock. The surface-area change subtracts the two removed end sections and replaces two strips of width `r` with the quarter cylinder. Exact predicted vertex positions and 7 faces, 15 edges and 10 vertices distinguish a full-length edge fillet from other geometry. [Independent model calculation](../../tooling/sw2026/edge_fillet_source/FilletModel.py)

The authoring worker finds one actual straight edge by its two model-space endpoints on the available stock, then verifies its two planar faces belong to the same stock boss. The worker uses `IEntity.Select4` with mark 1 and checks the actual selected object identity. It initializes the registered constant-radius type, selects the symmetrical circular profile and sets `DefaultRadius` in metres. `CreateFeature` creates the fillet. [Definition API](https://help.solidworks.com/2025/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeatureManager~CreateDefinition.html) · [2026 constant-radius enum](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swSimpleFilletType_e.html) · [2026 Initialize](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.ISimpleFilletFeatureData2~Initialize.html) · [2026 Edges](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.ISimpleFilletFeatureData2~Edges.html) · [2026 CreateFeature](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeatureManager~CreateFeature.html)

After rebuild, rollback selection must expose the one actual edge in `Edges` and the stock dependency again. The worker releases that selection access before measuring the active solid. The one cylindrical face belongs to the actual fillet feature and must agree with the predicted axis and radius. The native editable radial display belongs to that feature by its actual full name and driving state. The edit uses the dimension setter and checks the new geometry in the current process and after a fresh reopen. The original source hash must survive the edit. Every full state records the recursively ordered feature tree, one solid, exact bounds and topology, and volume, area and centroid agreement to six significant figures. [2026 selection lifecycle](https://help.solidworks.com/2026/english/api/sldworksapiprogguide/Miscellaneous/Accessing_Selections_that_Define_Features.htm) · [2026 radial dimension enum](https://help.solidworks.com/2026/English/api/swconst/SOLIDWORKS.Interop.swconst~SOLIDWORKS.Interop.swconst.swDimensionType_e.html) · [2026 setter status](https://help.solidworks.com/2026/english/api/swconst/SOLIDWORKS.Interop.swconst~SOLIDWORKS.Interop.swconst.swSetValueReturnStatus_e.html)

## Stage and run

The host packager reads the exact committed revision and the one known healthy disclosed native control. That control is SHA-256 `28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0`. Use fresh host and guest output paths. The entire packet is verified before launch and before each phase.

```sh
python3.14 -B re/tooling/sw2026/edge_fillet_source/FreezeFilletJob.py \
  --source-revision EXACT_COMMIT \
  --control /absolute/path/to/Control.SLDPRT \
  --output /absolute/new/host/packet \
  --guest-packet 'C:\KitEdgeFilletSource03\Packet' \
  --guest-capture 'C:\KitEdgeFilletSource03\Capture' \
  --guest-checkout '\\Mac\Home\Documents\UniCAD\Kit'
```

Copy the packet to its recorded local guest path. The oracle owner starts the following command from the host via the existing Parallels route and substitutes the recorded job digest.

```sh
prlctl exec --current-user 'Windows 11' py -3.12 -B \
  'C:\KitEdgeFilletSource03\Packet\Tool\AuthorEdgeFillets.py' \
  --job 'C:\KitEdgeFilletSource03\Packet\SourceJob.json' \
  --job-sha256 EXACT_JOB_SHA256
```

Use `--verify-packet` after the two job arguments to verify the frozen bytes without starting the native app. The native mode pins `SldWorks.Application.34`, executable version `34.5.2.0604` and SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`. It records actual registered interfaces and enum values and keeps per-phase receipts, the native sources, both geometry siblings, and the terminal `Capture/SourceLock.json` outside the checkout. A failed control, native warning, timeout, changed immutable input, incorrect actual ownership or missing fresh process keeps the lock failed. Leave the receipts alone until the supervisor returns.

The host freezes disclosed intent and validates analytic and packet structure without running native CAD. Registered dispatch, variant marshaling, rollback behavior, exact display identity, and actual native results remain pending the oracle owner's run. An independent protected pair can be authored and locked before testing a future writer. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Generative corpus method](../../Playbook/GenerativeCorpus.md)

## First native attempt and marked-selection retry

The first source-only packet completed both healthy controls and launched three distinct exact-build processes. The axial phase completed all twelve unfilleted stock checks, matched both adjacent planar faces to the actual stock body and boss, and verified the sole mark-1 object as the intended edge. The fresh `Edges` property put returned without error. Its getter then returned one null element although `GetEdgeCount` returned 1. The next call passed that null as an object to `IsSame`, which returned COM type mismatch `-2147352571`, argument 1. The first attempt ended before feature creation or any native save. [Sanitized failed receipt](../measurements/2026/EdgeFilletSourceAttempt01.json) · [Fresh definition gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Fillets/FreshFilletEdgeCanBeNull.md)

The retry sends the measured mark-1 selection directly to `CreateFeature`. This follows the vendor's constant-radius creation procedure and avoids relying on a fresh definition's edge pointer. Stock face/body identity and exact live preselection identity remain required. After creation, the retry obtained a nonnull typed edge from the rollback selection and matched it to the current unfilleted body by endpoint and native object checks. It then stopped at a separate item-count assumption described below. [Vendor constant-radius creation procedure](https://help.solidworks.com/2022/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISimpleFilletFeatureData2.html?id=2.2.1.334) · [2026 selection data](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISelectionMgr~CreateSelectData.html) · [2026 selection access](https://help.solidworks.com/2026/english/api/sldworksapiprogguide/Miscellaneous/Accessing_Selections_that_Define_Features.htm)

## Uniform-radius item inventory

The second packet created the axial fillet and rebuilt without diagnostics. Its rollback definition retained the constant-radius and circular enums, `IsMultipleRadius=false`, and radius `0.00437 m`. `Edges` returned one actual dispatch object, `GetEdgeCount` returned 1, and `IsSame` returned 1 for the two typed `IEdge` objects. The edge was independently found by endpoints on the current stock, with both adjacent planar faces joined to that same body and producing boss. `Features` and `Loops` were null. The phase passed all fourteen completed numeric checks, then rejected `FilletItemsCount == -1` before measuring the finished body or saving. Both controls and native cleanup passed. [Sanitized attempt 02 receipt](../measurements/2026/EdgeFilletSourceAttempt02.json)

The official API remarks specify `-1` for a simple fillet that uses a uniform radius. The third packet requires this sentinel after the existing constant-radius, symmetric, one-edge checks. It records both counts and omits per-item indexing for the uniform case. The original shape, marked-selection proof, typed rollback edge comparison, independent geometry, and live edit checks all remain required. The completed lifecycle for this packet is recorded below. [Official item-count property](https://help.solidworks.com/2025/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISimpleFilletFeatureData2~FilletItemsCount.html) · [Uniform radius gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Fillets/UniformFilletItemCountIsNegative.md)

## Completed disclosed acquisition and protected source lock

The third packet completed the two independent disclosed source lifecycles on SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`. Both brackets passed, all eight processes were distinct, and the application was idle at the end. Each case passed 31 authoring, 40 edit and 19 edited-reopen numeric checks. The terminal source lock SHA-256 is `1f2652129840582cb663063b08f590dadbaf8dd046f0b96f5a1b99cf5ae47797` for source job `e37e868be9a2b394c296b30c08a586f5dd5cced5309c2f23503f2b8ba0532c01`.

The [protected supervisor](../../tooling/sw2026/edge_fillet_source/SealFilletSources.py) reuses that exact successful native authoring, phase, COM registration and inspection code. Freeze a method packet from the committed supervisor revision with `FreezeFilletJob.py --seal-method` and the same unchanged disclosed control. The recorded `--guest-capture` must be a fresh unused local path. This packet has no private data and cannot run as an ordinary source job. `--verify-packet` checks it without starting CAD.

The oracle owner provides two independent guest-local cases ordered as `Slot01` and `Slot02`, with their combined JSON SHA-256 computed in the guest. Use the disclosed specification's exact case fields and shape domains, with outer `"schema": "kit.sw2026.edge-fillet-heldout-spec.v1"` and `"cohort": "heldout"`. The new pair independently varies the stock sizes and all radii from the disclosed cases. Intent, frozen copies, original and edited saves, geometry siblings and terminal raw records remain under a local protected guest root. Start the supervisor from the exact method packet, supplying a new run directory within that root and a fresh digest-only target in a disjoint local directory.

```sh
prlctl exec --current-user 'Windows 11' py -3.12 -B \
  'C:\KitEdgeFilletSealedMethod\Packet\Tool\SealFilletSources.py' \
  --method-job 'C:\KitEdgeFilletSealedMethod\Packet\SourceJob.json' \
  --method-job-sha256 EXACT_METHOD_JOB_SHA256 \
  --disclosed-job 'C:\KitEdgeFilletSource03\Packet\SourceJob.json' \
  --disclosed-lock 'C:\KitEdgeFilletSource03\Capture\SourceLock.json' \
  --private-root 'C:\KitEdgeFilletSealedPrivate' \
  --spec 'C:\KitEdgeFilletSealedPrivate\Spec.json' --spec-sha256 GUEST_INTENT_SHA256 \
  --run-root 'C:\KitEdgeFilletSealedPrivate\Run01' \
  --publish 'C:\KitEdgeFilletEvidence\PrewriterSourceLock01.json'
```

The unchanged native phases require the same healthy brackets, clean reopen and edit, original hashes, independently predicted geometry and eight distinct processes. Copy out only the digest-only lock. It binds the four source and edited source SHA-256 digests to the exact method, build, controls and zero writer outputs. No private paths, intent, numeric model values or raw phase receipts are published. This is a pre-writer acquisition method. It has not yet run on the independent pair. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Held-out method](../../Playbook/GenerativeCorpus.md)
