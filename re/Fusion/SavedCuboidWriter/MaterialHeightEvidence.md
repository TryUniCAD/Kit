# Saved cuboid material and texture mapping across a height edit

[MaterialHeightEvidence.py](MaterialHeightEvidence.py) checks four prior edit and restore pairs from Fusion 2706.1.17. Each pair traces to the candidate archive opened in its recorded process and the two native exports hashed in a separate reopen receipt. The three baseline paths share one width and depth. The holdout has different dimensions and a nonzero initialized mapping origin. The script uses the typed SDK reader, writes a report to stdout and leaves the input archives intact.

## Body material binding

The saved body's `physicalMaterial` and `visualMaterial` both link to a Design `ProteinAssetManager`. The manager names the single typed package member under `ProteinAssets.BlobParts` and declares exactly one reference with count one for each role. The body reference identifies the package asset. The bound definition and library agree with the body's references. The visual reference resolves via the base `Generic` asset to its `_Post2015` companion. All eight bodies have an empty per-face visual material map. The SDK's [body material check](../../../src/convert/Formats/Fusion/DocumentCodec/Reading/Materials/CheckBodyMat.py) and [asset resolution](../../../src/convert/Formats/Fusion/DocumentCodec/Reading/Materials/ResolveMatAsset.py) define these joins.

The body bindings and both visual assets retain complete typed equality within each edit and restore pair. The only physical asset change is in `physmat_aspects`. Its enabled link still resolves to one Structural asset and one appearance asset in the same order. Their records retain equality after normalizing the two regenerated instance identifiers. The material package member name and four package core records change in all four pairs. Timestamps and resource links also change in the reconstruction pair. The native package therefore needs coherent manager, package, asset and aspect identifiers. The observed envelope changes alone do not establish which identifiers a height-only writer must regenerate. Preserve the source's typed material assignments and resolved asset content. Keep envelope and link generation behind the same-document export contrast until that churn is isolated.

## Mapping ownership and coordinates

`Body.textureMapping` resolves to `LayeredTextureMapping`. The body-owned OGS solid GroupNode's `TextureMappingAttribute.TextureMapping.Reference` resolves to that same Design entity. Its layer map links `2` to `ASMTextureMapping` and `3` to `ProceduralWoodTextureMapping`. OGS primary mode `0` and secondary mode `6` mirror the corresponding Design layers. Their axes agree, and the Design identity transforms agree with the explicit OGS identity matrices in this cohort. The mode and class names identify wire structures. They do not establish a portable wood material or a portable mapping model.

All three Design mapping boxes, both OGS texture cache boxes and the solid `BrepWorld.ModelBox` exactly match the immediately preceding solved BRep frame bounds in all eight exports. The [existing display analysis](../SavedCuboidRoundTrip/Findings.md#display-bounds-can-retain-the-previous-height) found that the current edge and face bounds follow the newly solved frame. Keep the two sets of dependencies separate. A reproduction of the observed stale-cache behavior would derive the aggregate and texture boxes from the source's pre-edit solved frame. It would derive the current solid geometry and child boxes from the requested height. Taking the prior box from the source's saved display can lag another edit. Substituting the current designed height into the previous box also loses precision. The holdout precursor frame stores max Z `3.1399999999999997` cm, while the restored parameter and frame store `3.14` cm.

`ProceduralWoodTextureMapping.originInitilized` is true in all eight exports. OGS secondary `WoodOrigin` exactly mirrors the Design origin. That origin remains stable across each edit and restore. The six baseline exports use `(0, 0, 0)` cm. Both holdout exports use `(2.185, 0.645, 1.5699999999999998)` cm, the midpoint of the opened precursor's frame. The holdout restore's mapping box follows the intervening 19.7 mm frame, whose midpoint has Z `0.985` cm, while its origin retains Z `1.5699999999999998` cm. A height edit on this observed initialized state should retain the source origin and mirror it to OGS. The uninitialized-to-initialized policy remains unknown. The four opened precursor candidates carry no Design body mapping, and the first native re-exports already have an initialized one. The capture sequence cannot separate initial creation from intervening native operations.

| Prior group | Edited solved height → mapping box height (cm) | Restored solved height → mapping box height (cm) | Initialized origin Z in both saves (cm) |
| --- | ---: | ---: | ---: |
| OracleReconstruction | `2.83 → 1.3800000000000001` | `1.3800000000000001 → 2.83` | `0` |
| OracleEdited | `2.83 → 2.2600000000000002` | `2.2600000000000002 → 2.83` | `0` |
| NativeBaselineEdited | `2.83 → 2.2600000000000002` | `2.2600000000000002 → 2.83` | `0` |
| NativeHoldoutEdited | `1.97 → 3.1399999999999997` | `3.14 → 1.97` | `1.5699999999999998` |

## Reproduce the measurement

Use the local prior capture directories and Python 3.14 with the checkout SDK available. Supply each receipt directory and its corresponding pre-edit archive. The first pair's edited and restored archives also appear in the [pinned saved cuboid corpus](../SavedCuboidRoundTrip/Corpus/Manifest.json).

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -B re/Fusion/SavedCuboidWriter/MaterialHeightEvidence.py `
  --group ../EncoderIntegratedFusion01/OracleReconstruction ../EncoderIntegratedFusion01/reconstruction.f3d `
  --group ../EncoderIntegratedFusion01/OracleEdited ../EncoderIntegratedFusion01/edited.f3d `
  --group ../FusionEncoderNativeCandidateArtifacts/NativeBaselineEdited ../FusionEncoderNativeCandidateArtifacts/encoder_0.f3d `
  --group ../FusionEncoderNativeCandidateArtifacts/NativeHoldoutEdited ../FusionEncoderNativeCandidateArtifacts/encoder_1.f3d
```

Two fresh invocations produced byte-identical UTF-8 output with SHA-256 `8889532188ddbc527df7d9f5dc40b82bac02b4167721a316e583916c0dec7964`. Separate probes refused a wrong archive digest and a fresh-box substitution for the restored holdout's preceding-frame box. The next controlled capture needs two unchanged exports at each height following an initialized native input, with zero and nonzero origins. That capture can separate package churn from the height change and check retention before a generated candidate goes through the [native acceptance procedure](../../../Documentation/Reference/Operations/CadSuccessCriteria.md#c5-to-c7-loadable-usable-and-measured).
