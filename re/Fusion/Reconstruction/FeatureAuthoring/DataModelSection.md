# Draft section: independently authored part features

This draft is for `Documentation/Reference/Research/FusionDataModel.md`.
It is kept here because that document is maintained in a separate change.

## Independently authored part features

`DocumentSpec.Features` adds an ordered tuple of `FilletSpec`, `ChamferSpec` and `ShellSpec` values to an unconstrained cuboid. `CheckFeatures` accepts at most 16 features, requires the shell to be last and reserves generated `d<digits>` parameter names. `SolvePart` applies each feature to an exact prism model in millimetre inputs and centimetre geometry. A fillet or chamfer replaces one convex vertical corner of the current profile with an arc or a line. A shell removes the single upward roof, offsets every wall inward and adds an inner floor. Rejected corners, collapsed sides and over-thick shells raise `ValueError` before any record is written.

Each timeline feature owns a typed Design subgraph. Fillets use `DcFilletEdgeFeature` with one `DcFilletEdgeData` row, `TangencyWeight` and `Radius` parameters and edge tracking type 8. Chamfers use `DcChamferFeature`, one `DcChamferData` row and a `Distance` parameter. Shells use `DcShellFeature`, tracking type 16, an `innerThickness` parameter and two operation identifiers. The pick is a `ModelDataRef` to `BrepRef` pair with an `ASMRecipe`. Corner recipes name the vertical edge through its two wall labels and the cap labels at its ends. The shell recipe names the roof and its bounding walls in first-appearance order around the roof loop. `ETCachedLineSeg3d` stores the solved edge. `ETCachedTopology` stores the roof entity tag.

Feature `n` takes state ID `n+4`, start state `n+3` and operation IDs from 303 upward. `LinkTimeline` updates the creation order, the entity and feature identifier maps, the per-class `featureIndexMap` and the component `operationSeedId`. Parameters use `d<n>` user names after the existing parameter watermark, and their expressions omit a trailing `.0`.

`EmitPartHist` writes one journal state for the base extrusion and one state for each feature. Each state contains the complete solved body. A face that keeps its draft key across two states is a modification and keeps its tag. A face whose key changes is a deletion plus an insertion, and the inserted face receives a fresh tag. The body claims tag 0 before any face. That tag must equal the `mapBodyId` key of `BRepHistorySerializer`, or Fusion shows a body without geometry.

Every reference scope (`BrepRef.rScope` and `ETCachedTopology.scope`) carries the component `persistentId`. A body identifier in this field still opens with correct geometry. After `computeAll`, the shell then reports `Face 1 missing` and the body reverts to the extruded box.

Fusion 2706.1.17 does not recompute a feature when it opens a document. Truncated native journals and five persisted dirty-flag variants opened as the stale box with healthy timeline items. Only `computeAll` produced the feature geometry. The writer must therefore emit the solved journal for every state.

Fusion 2706.1.17 accepted five independently authored cases against same-session API controls: fillet, chamfer, shell, fillet then shell, and a four-feature part. Each case opened healthy with control geometry before any recompute. Every rollback marker, `computeAll`, a driving parameter edit, export and reopen also matched the control. The four-feature part has 17 faces, 42 edges, 28 vertices and 7.004101559 cm³. After a 5 mm fillet edit and a 25 mm height edit, it has 8.242145243 cm³. See [the change entry](../../../../Documentation/Changes/Fusion/Features/FusionPartFeatures.md), [the acceptance report](../../LocalOracle/FeatureAuthoring/Authored/NativeAcceptance.json) and [the rejected-rule regressions](../../LocalOracle/FeatureAuthoring/Regressions/Observation.json).

Revolve, hole, cut extrusion, pattern, mirror, combine, sweep, loft, draft, split, move, offset-face and construction features are captured as [native family records](FamilyRecords.json.xz) only. The draft and copy-body controls use class versions that the typed catalog does not qualify, and no offset-face control was captured.
