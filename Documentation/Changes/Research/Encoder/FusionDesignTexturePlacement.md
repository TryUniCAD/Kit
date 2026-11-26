# Generate Fusion Design texture placement

The research commands generate a cuboid with two distinct modern finishes and an explicitly initialized body texture origin. The placement stays fixed when the cuboid height changes. The strict public Fusion reader retains the complete generated mapping in version-2 read-only JSON.

## Use

Run from the checkout with Python 3.14 and its SDK on `PYTHONPATH`. Start with a validated [distinct material appearance request](FusionDistinctMaterialAppearances.md). Wrap it under `appearance_request` in a JSON object with `schema` set to `1`, `scope` set to `fixed_cuboid_body_texture_placement`, and `wood_origin_cm` set to three finite floating-point coordinates. Write zero as `0.0` or `-0.0` to specify its sign. Choose unused output paths.

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -B re/Fusion/DesignTexturePlacement/GenerateSavedCuboid.py Placement.json Candidate.f3d
python -B re/Fusion/DesignTexturePlacement/PrepareRequest.py Candidate.f3d Readback.json
```

Generation creates a new body-linked Layered mapping with role `2` for ASM and role `3` for Procedural Wood. It stores selector `0`, zero axes, compact identity transforms and initialized empty texture bounds. It derives the records from the requested placement and the underlying authored cuboid instead of using a source archive.

Preparation accepts the scoped graph with its exact owner links, fields and empty-box representation. It verifies the nested model and refuses unsupported placement state without writing a request. The earlier authored material and distinct appearance commands still refuse Design texture mappings.

## Verification

Fresh processes prepared and regenerated separate candidates with only the typed request in the replay directory. The strict public reader and persisted JSON preserved the complete typed model and the sign of each origin coordinate. The repeat matched every archive byte. A placement-only edit preserved the solved geometry and driving parameter roles. A separate height edit preserved the placement while the SDK-reported volume changed from 6,133.272 to 10,888.78 mm³.

| Candidate | SHA-256 |
| --- | --- |
| Baseline and replay | `bb3f59ca8e55f99731cbdac2ea923f4c5aba69d357d15f7d3dbd6248ec4381c1` |
| Origin-only edit | `8173b770b77549d9f02ad03f3c30de54a096f995f58405e2cb7be0418c1b5e99` |
| Height-only edit | `943547cc6bb9fcda22843befe9e266b58bb1457d508a2e9c7fad3ed5512b53a2` |

Four invalid requests refused generation without creating an output. A strict-readable mapping with nonzero axes refused preparation without changing the source or an occupied destination.

The edit and refusal cases passed in the first 115.77-second compatibility run. The replay initially failed only because the public source paths were different. After asserting that provenance separately, the exact replay case passed in 35.00 seconds with unchanged archive hashes.

## Limits

The commands do not generate or qualify historical texture bounds, an OGS graphics scene, arbitrary transform values, legacy compatibility appearances or whole saved-source admission. See the [saved texture bounds gotcha](../../../Gotchas/Conversion/Fusion/Materials/FusionPriorTextureBounds.md). This research result has no licensed Fusion open, edit, rebuild or reopen measurements. The production SDK boundary remains read-only for this profile.
