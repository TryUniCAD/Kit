# Distinct Fusion body and physical appearances

This research procedure generates a cuboid with two independently authored finishes. One appearance belongs to the physical material's aspect graph. The other belongs to the body and supplies the color exposed by the strict public reader. Each role gets its own generated identity.

## Use

Run the commands from a checkout with Python 3.14 and the checkout SDK on `PYTHONPATH`. Choose new destination paths.

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -B re/Fusion/DistinctMaterialAppearances/GenerateSavedCuboid.py Request.json Candidate.f3d
python -B re/Fusion/DistinctMaterialAppearances/PrepareRequest.py Candidate.f3d Readback.json
```

The request contains `schema: 1`, `scope: fixed_cuboid_distinct_material_appearances`, `material_request`, `physical_appearance_rgba` and `body_finish`. The [authored material request](FusionAuthoredMaterialProperties.md) keeps the mechanical and thermal properties, physical finish and optional component default. Its nested RGBA names the body-visible color. Use `physical_appearance_rgba` to set the aspect color and `body_finish` to set the independently selected modern finish.

## Verification

Independent CLI processes generated and re-prepared a metal aspect with an opaque body finish and a basic physical material with a metallic body finish. Both retained the complete typed model through strict public JSON. A fresh repeat produced byte-identical output. An explicit body color and roughness edit left the physical finish intact.

| Authored candidate | Generated archive SHA-256 |
| --- | --- |
| Metal aspect with opaque body | `007f3f283fbea5646f037a12fe63a4d59e05dc9084617356e56ea442563569d1` |
| Body color and roughness edit | `3edd397ab9ab0442ba69a18b8e13db9f9723af06fba5ac31854c936cca5ba045` |
| Basic material with metallic body | `5c2d31eca3f17934d71625a142dd7d5b5521d71699b9b66b608b0f42541e8733` |

The scoped preparation command refused a shared body and physical aspect, saved legacy aliases and an independently generated modern alias pair. Each refusal left its destination absent. All four tracked compatibility cases passed in 113.84 seconds, including two distinct body roughness values with a constant physical finish. Both refusal tests passed again in 32.17 seconds with exact error assertions.

Eight independent replays passed in 157.681 seconds. They tested two finishes with the same Metal schema and different color and roughness values, isolated edits to each role, byte-identical repeats and replay from a freshly prepared request.

Sixteen invalid requests and four captured legacy-alias sources refused publication. A deliberately shared appearance passed the general read-only SDK and failed scoped preparation. The lower codec refused a visual link to an incompatible asset role.

All five tracked compatibility cases passed in 91.98 seconds after the mapping guard. A [Design texture mapping without graphics](../../../Gotchas/Conversion/Fusion/Materials/FusionDesignTextureWithoutOgs.md) survived strict read-only JSON. The preparation command refused both linked and unlinked mappings without writing an output. Independent checks verified that an existing destination retained its bytes and an unmapped source prepared to byte-identical JSON.

## Limits

Both appearances use supported modern material schemas. Historical legacy compatibility aliases, packages with additional resources or assets, and procedural texture mappings require further rules. See the [appearance role gotcha](../../../Gotchas/Conversion/Fusion/Materials/FusionPhysicalAndBodyFinish.md). The strict version-2 read-only contract continues to apply. Whole saved-source and native Fusion acceptance remain open.
