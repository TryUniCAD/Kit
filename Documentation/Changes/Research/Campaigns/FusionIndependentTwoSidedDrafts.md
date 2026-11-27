# Independent two-sided circular extrusion drafts

## Scope

Task `A08h-FusionTwoSidedDraft20261127` records solid NewBody circular extrusions with unequal distances and independently signed taper angles.
The campaign varies both distances, both drafts, radius, profile placement and sketch frame.
Swapped-side cases and two combined parameter holdouts distinguish side ownership and signed geometry.

The [research package](../../../../re/Fusion/TwoSidedDraft20261127/README.md) retains actual native files, observations, deterministic documents and receipts.
The [automation register](../../../Reference/Research/AutomationSteps.md#a08h-fusiontwosideddraft20261127) owns the child task and remaining requirements.
Shared decoders, catalogue builders and native workers are unchanged.

## Behavior and use

The existing catalogue builder cannot express two separate Distance extents with independent draft angles.
The isolated research script uses the existing native script worker and documented `setTwoSidesExtent` API.
Private configuration and credentials stay outside the checkout.
The existing controller and supervisor serialize Fusion jobs and run independent offline batches.
Models remain disabled.

Use the package's committed-blob manifest with `kit research --offline --root ABSOLUTE_CHECKOUT fusion`.
Select its native asset paths and an unused output directory.
Explicit partial mode preserves strict refusals before fallback.
The package describes source hashes, exact revisions, worker bindings and reproduction commands.

## Verification and remaining scope

Source commit `c2f00415b3f48dea33b349dcc43048509db3568d` contains 68 native archives and 101 matching API observations.
The source application is Fusion `2706.1.17`; the package records the executable hash.
The frozen SDK and research revision is `18b41b98c96fd123a11d1ae0d1cda29b9d9746ed`.

Strict replay accepts two untapered controls and rejects 66 drafted states.
Explicit partial replay retains all 68 documents and receipts, including 66 partial outcomes.
The existing native helper matches all 1,224 side-distance, signed-draft, operation, profile and ownership comparisons.
All 136 BRep initial tables parse through the existing production width-aware reader.
The separate research helper still refuses complete reconstruction at its ASM4 body-identity boundary.
This limitation does not establish unknown grammar or conversion acceptance.
The separate public strict boundary explicitly requires zero second-side taper in `ReadParameters.py`.
Non-identity profile placement has its own guard in `GraphValues.py`.
These existing admission rules remain unchanged.

Eleven distinct fresh processes passed all 198 lifecycle, process and control comparisons.
All four feature drivers were edited independently, restored, rebuilt, saved and reopened.
The oracle was released idle with no recovery marker.
The [API script-size gotcha](../../../Gotchas/Research/Workers/Verification/PersonalApiScriptSizeControl.md) records refused preparations and their correction.
Independently driven sketch radius/placement, general profiles and operations, complete source-to-body reconstruction and editable target conversion remain open.
