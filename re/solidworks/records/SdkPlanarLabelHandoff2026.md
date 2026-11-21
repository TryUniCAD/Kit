# Typed sketch label handoff for the scoped planar assembly constructor

Workstream `B04-SW2026-MATES-PLANAR/source-root-projection` in PR #121, owner `assembly_frontier`. The comparison base is `fecc574bad42189dbbc2c66c997b7e71e9005972`. This prerequisite links a typed neutral input to the existing child projection. Its exit is exact default and explicit byte parity plus guarded owner refusals. The public whole-source conversion remains gated. [Prior source audit](SdkPlanarPriorSourceAdmission2026.md) · [Existing source comparison](SdkPlanarSourceLabelBridge2026.md) · [Host proof](../measurements/2026/SdkPlanarLabelHandoff01.json)

## Modeling and ownership

`SketchLabelIn` names the actual neutral child sketch and one actual driving parameter. It accepts finite XYZ in metres in the selected sketch frame and an explicit centreline routing Boolean. The private `SketchLabels` input to `PlanAsmWrite` and `PrepareAssembly` requires both actual sketch drivers. The current model projection already validates the actual support, six exact sketch relations and both driver owners. Label row order is independent of width and height role order. The scoped input accepts the canonical origin Front plane and positive blind rectangle. [Semantic input](../../../src/convert/adapters/solidworks/Core/AssemblyPreparation/Children/SketchLabelIn.py) · [Owner check](../../../src/convert/adapters/solidworks/Core/AssemblyPreparation/Children/BindRectLabels.py)

The binder checks the proposed point XY against the selected edge with the same `ReadRectPlace` used by the archive display builder. Both branches derive their endpoint and outward witnesses from the actual model geometry. The point's normal component is retained directly in `moDisplayDistanceDim_c.f6a0.f38`. Each display owns its centreline bit in `f1014` independently. The shared rectangle composer supplies the parameter, value, handle, display and annotation identities, then `MakePlanarGroup` links the actual generated child. [Witness rule](../../../src/convert/adapters/solidworks/Archive/Construction/SketchDimensions/ReadRectPlace.py) · [Typed display emission](../../../src/convert/adapters/solidworks/Archive/Construction/SketchDimensions/MakeRectDisplay.py) · [Assembly preparation](../../../src/convert/adapters/solidworks/Core/AssemblyPreparation/PrepareAssembly.py)

The neutral companion is internal. The `CadDocument` wire and ordinary registry use the existing declaration. The whole-source gate continues to refuse unprojected assembly root content. Other native presentation, material, property and allocator state retains its owning admission requirements. [Current source closure](SdkPlanarRootSourceProjection2026.md)

## Model-only proof

| Authored rectangle in mm | D1 point in m | D2 point in m | Centreline routes |
| --- | --- | --- | --- |
| 51.75 × 36.125 × 10.875 | `(-0.00815, -0.02685, 0.000293)` | `(0.03529, 0.00473, -0.000711)` | D1 true, D2 false |
| 28.375 × 45.625 × 13.125 | `(0.004872, -0.03411, -0.000392)` | `(0.02398, -0.00729, 0.000908)` | D1 false, D2 true |

Fourteen positive fresh workers compare the exact base, current default, explicit default, planar-only, mixed routing, repeated spatial, and the existing independent research constructor across both designs. The ordinary and explicit-default archives match the archived base byte for byte. The spatial variants modify only the child's `Contents/Config-0-ResolvedFeatures`. The full parent files, XY witnesses, live drivers, value records and actual handle references match their scoped controls. The models' XYZ and Boolean values match exactly. Each generated child replays both Config and ResolvedFeatures, for 28 linked replays. Ten separate guarded refusals cover crossed or missing IDs, input type and bounds, translated support and unprojected root content. None reaches the child builder. No runtime file access, reserved source reads or native launches were observed. [Verification tool](../../tooling/sw2026/planar_registry/ProvePlanarLabelHandoff.py) · [Queue process coverage](../../../tests/Convert/Solidworks/Research/Construction/Assembly/SketchLabelHandoffTests.py)

```sh
KIT_PLANAR_LABEL_REPORT="$(mktemp -d)/Result.json"
python3.14 -I -B re/tooling/sw2026/planar_registry/ProvePlanarLabelHandoff.py prove \
  --output "$KIT_PLANAR_LABEL_REPORT"
```

The prior cohort and renderer-save evidence serve as comparisons for field interpretation. This proof uses newly authored neutral inputs. Publication of a portable document annotation contract and any new native claim require independently locked sources and controlled native edits, saves and fresh reopens for that exact boundary. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
