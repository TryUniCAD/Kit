# Independent fillet, chamfer and shell features

`DocumentSpec.Features` adds an ordered sequence of parametric part features to the independently authored cuboid. Each feature becomes a native Fusion timeline item with its own driving parameter. `EmitDocument` writes a fresh Design graph, a solved multi-state BRep journal and an exact mass cache. No captured record, source archive or donor geometry is a runtime input.

## Usage

```python
from pathlib import Path

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec

Specification = DocumentSpec(
    "Hollow bracket",
    "height",
    20.0,
    ProfileKind="cuboid",
    WidthMm=40.0,
    DepthMm=30.0,
    Features=(
        FilletSpec((40.0, 30.0), 3.0, "Corner Round"),
        ChamferSpec((0.0, 0.0), 3.0, "Corner Bevel"),
        ShellSpec(2.0, "Hollow"),
    ),
)
Path("Bracket.f3d").write_bytes(EmitDocument(Specification))
```

`MakeFusionDoc` accepts the same specification through the public adapter. It adds one `FeatureStep` for each feature, with the kinds `KFillet`, `KChamfer` and `KShell`. Each step owns one length parameter, and the final `DesignBody` carries the solved topology counts.

## Feature inputs

| Specification | Fields                                   | Fusion feature        | Driving parameter |
| ------------- | ---------------------------------------- | --------------------- | ----------------- |
| `FilletSpec`  | `CornerMm`, `RadiusMm`, `FeatureName`    | `DcFilletEdgeFeature` | `Radius`          |
| `ChamferSpec` | `CornerMm`, `DistanceMm`, `FeatureName`  | `DcChamferFeature`    | `Distance`        |
| `ShellSpec`   | `ThicknessMm`, `FeatureName`             | `DcShellFeature`      | `innerThickness`  |

`CornerMm` is an `(x, y)` point in millimetres on the sketch plane. It must identify one convex vertical corner between two straight sides of the current body. Fillets and chamfers can follow earlier corner features. A shell opens the single top face, keeps the outer walls and must be the final feature.

`CheckFeatures` rejects an unsupported family, a constrained or non-cuboid profile, non-finite or non-positive values and more than 16 features. It also rejects an empty or invalid feature name and a user parameter named `d<digits>`. `SolvePart` rejects a corner that is not on the body, a size that consumes an adjacent side and a shell that collapses the profile.

## Construction

`SolvePart` applies every feature to an exact prism model and keeps each intermediate solid. `EmitPartHist` writes one journal state for the extrusion and one for each feature. Each state contains the complete solved body, with exact planes, cylinders, lines and circles. Fusion does not recompute features when it opens a document, so these solved states are required. See [the stale-open gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureStaleOpen.md).

Each feature subgraph contains the feature, its parameters, a `ModelDataRef` and `BrepRef` pick, an `ASMRecipe`, a geometry cache and a progenitor table. Corner recipes name the vertical edge through its two wall labels and its end caps. The shell recipe names the roof and its bounding walls. `LinkTimeline` adds the features to the creation order, the identifier maps, the per-class index map and the component operation seed.

Three journal and record rules are necessary for native acceptance:

| Rule                                                                         | Failure without the rule                                     |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------ |
| The body claims tag 0, the `mapBodyId` key                                   | The body opens without geometry                              |
| A face replaced by delete and insert receives a fresh tag                    | Fusion cannot open the document                              |
| `BrepRef.rScope` and `ETCachedTopology.scope` carry the component identifier | `computeAll` loses the shell face and reverts to the box     |

The [body tag gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureBodyTag.md) and the [reference rules gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureReferenceRules.md) record the evidence.

## Native acceptance

The [acceptance script](../../../../re/Fusion/LocalOracle/FeatureAuthoring/AcceptAuthoredFeatures.py) builds a native API control in the same session for each case. It then opens the Kit document without a recompute, walks every rollback marker and runs `computeAll`. It applies the driving edits, exports the document, reopens it and runs `computeAll` again. Geometry must match the control in volume, area, faces, edges, vertices, surface types, bounds and centre of mass.

[Fusion 2706.1.17 accepted all five cases](../../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/NativeAcceptance.json). All documents were closed after the run.

| Case           | Features                                           | Volume (cm³) | Faces, edges, vertices | Edit                           | Edited volume (cm³) |
| -------------- | -------------------------------------------------- | -----------: | ---------------------- | ------------------------------ | ------------------: |
| `Fillet`       | Fillet 3 mm                                        |  23.96137167 | 7, 15, 10              | Radius 4 mm                    |         23.93132741 |
| `Chamfer`      | Chamfer 3 mm                                       |  23.91000000 | 7, 15, 10              | Distance 2 mm                  |         23.96000000 |
| `Shell`        | Shell 2 mm                                         |   7.15200000 | 11, 24, 16             | Thickness 3 mm                 |         10.12800000 |
| `FilletShell`  | Fillet 3 mm, shell 2 mm                            |   7.11723450 | 13, 30, 20             | Thickness 1.5 mm, height 25 mm |          6.48656166 |
| `MultiFeature` | Fillet 3 mm, chamfer 3 mm, fillet 4 mm, shell 2 mm |   7.00410156 | 17, 42, 28             | Fillet 5 mm, height 25 mm      |          8.24214524 |

The base part is a 40 × 30 × 20 mm cuboid. Every case opened with healthy timeline items and the control geometry before any recompute. Every rollback marker matched the control. Save and reopen preserved the parameter expressions and the edited geometry.

The [manifest](../../../../re/Fusion/LocalOracle/FeatureAuthoring/Authored/Manifest.json) records the SHA-256 of each authored document. The acceptance report repeats each digest and records the digest of the Fusion-saved export.

## Verification

The integration cases in `tests/convert/formats/FusionCodec/Documents/PartFeatures` check archive reading, exact re-emission, solid stages, rejected inputs and the public adapter. They also check journal tag chains, reference scopes and the acceptance evidence. They run remotely, and no local tests were executed. Local Black, Ruff, Mypy, Pyright, steering, rationale-comment and path-policy checks passed.

## Limits

The writer supports fillets, chamfers and shells on an unconstrained cuboid. Revolve, hole, cut extrusion, pattern, mirror, combine, sweep, loft, draft, split, move, offset-face and construction features are not authored. [Native records for these families](../../../../re/Fusion/Reconstruction/FeatureAuthoring/FamilyRecords.json.xz) are captured as research evidence only. The specifications cannot express variable-radius, chord-length or two-distance corners, outside shells or multi-face shell openings. A corner edit next to a curved side raises `ValueError`.
