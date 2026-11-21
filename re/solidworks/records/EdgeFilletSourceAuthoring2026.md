# Source acquisition for constant-radius edge fillets

Workstream `B04-SW2026-EDGE-FILLET-SOURCES` is part of the PR #121 takeover. The source packet covers two separately authored single-edge fillets on rectangular Front-plane blind bosses. The oracle owner runs the packet and retains the hash-bound source lock. Exit for this step requires two complete sources and edited derivatives, eight distinct native processes, clean opens and rebuilds, and healthy immutable controls. This packet supplies no format rule, writer or held-out result.

## Model and checks

The [disclosed case definitions](../../tooling/sw2026/edge_fillet_source/DisclosedFilletInputs.json) vary the stock dimensions, stock offset, selected edge, and initial and edited radius. One edge runs along the extrusion through a side corner. The second runs across one base-plane coordinate, at the far end of the extrusion and on the opposite transverse side.

The projected removed cross section is a square of side `r` minus a quarter disk. Its area is `(1 − π/4) r²`. Its centroid has inward offset `r (5/6 − π/4) / (1 − π/4)` from the corner in both transverse coordinates. The removed volume is the sectional area times the edge length. The remaining centroid comes from subtracting its first moments from those of the stock. The surface-area change subtracts the two removed end sections and replaces two strips of width `r` with the quarter cylinder. Exact predicted vertex positions and 7 faces, 15 edges and 10 vertices distinguish a full-length edge fillet from other geometry. [Independent model calculation](../../tooling/sw2026/edge_fillet_source/FilletModel.py)

The authoring worker finds one actual straight edge by its two model-space endpoints on the available stock, then verifies its two planar faces belong to the same stock boss. The worker uses `IEntity.Select4` with mark 1 and checks the actual selected object identity. It initializes the registered constant-radius type, selects the symmetrical circular profile, verifies one actual edge in `Edges`, and sets `DefaultRadius` in metres. `CreateFeature` creates the fillet. [Definition API](https://help.solidworks.com/2025/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeatureManager~CreateDefinition.html) · [2026 constant-radius enum](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swSimpleFilletType_e.html) · [2026 Initialize](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.ISimpleFilletFeatureData2~Initialize.html) · [2026 Edges](https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.ISimpleFilletFeatureData2~Edges.html) · [2026 CreateFeature](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeatureManager~CreateFeature.html)

After rebuild, rollback selection exposes the one actual edge and stock dependency again. The worker releases that selection access before measuring the active solid. The one cylindrical face belongs to the actual fillet feature and must agree with the predicted axis and radius. The native editable radial display belongs to that feature by its actual full name and driving state. The edit uses the dimension setter and checks the new geometry in the current process and after a fresh reopen. The original source hash must survive the edit. Every full state records the recursively ordered feature tree, one solid, exact bounds and topology, and volume, area and centroid agreement to six significant figures. [2026 selection lifecycle](https://help.solidworks.com/2026/english/api/sldworksapiprogguide/Miscellaneous/Accessing_Selections_that_Define_Features.htm) · [2026 radial dimension enum](https://help.solidworks.com/2026/English/api/swconst/SOLIDWORKS.Interop.swconst~SOLIDWORKS.Interop.swconst.swDimensionType_e.html) · [2026 setter status](https://help.solidworks.com/2026/english/api/swconst/SOLIDWORKS.Interop.swconst~SOLIDWORKS.Interop.swconst.swSetValueReturnStatus_e.html)

## Stage and run

The host packager reads the exact committed revision and the one known healthy disclosed native control. That control is SHA-256 `28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0`. Use fresh host and guest output paths. The entire packet is verified before launch and before each phase.

```sh
python3.14 -B re/tooling/sw2026/edge_fillet_source/FreezeFilletJob.py \
  --source-revision EXACT_COMMIT \
  --control /absolute/path/to/Control.SLDPRT \
  --output /absolute/new/host/packet \
  --guest-packet 'C:\KitEdgeFilletSource01\Packet' \
  --guest-capture 'C:\KitEdgeFilletSource01\Capture' \
  --guest-checkout '\\Mac\Home\Documents\UniCAD\Kit'
```

Copy the packet to its recorded local guest path. The oracle owner starts the following command from the host via the existing Parallels route and substitutes the recorded job digest.

```sh
prlctl exec --current-user 'Windows 11' py -3.12 -B \
  'C:\KitEdgeFilletSource01\Packet\Tool\AuthorEdgeFillets.py' \
  --job 'C:\KitEdgeFilletSource01\Packet\SourceJob.json' \
  --job-sha256 EXACT_JOB_SHA256
```

Use `--verify-packet` after the two job arguments to verify the frozen bytes without starting the native app. The native mode pins `SldWorks.Application.34`, executable version `34.5.2.0604` and SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`. It records actual registered interfaces and enum values and keeps per-phase receipts, the native sources, both geometry siblings, and the terminal `Capture/SourceLock.json` outside the checkout. A failed control, native warning, timeout, changed immutable input, incorrect actual ownership or missing fresh process keeps the lock failed. Leave the receipts alone until the supervisor returns.

The host freezes disclosed intent and validates analytic and packet structure without running native CAD. Registered dispatch, variant marshaling, rollback behavior, exact display identity, and actual native results remain pending the oracle owner's run. An independent protected pair can be authored and locked before testing a future writer. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Generative corpus method](../../Playbook/GenerativeCorpus.md)
