# Saved Fusion cuboid configuration records

The saved-configuration research commands preserve the empty table and rule attached to a strict fixed-corner cuboid. They extend the [named-camera request](FusionSavedNamedCameras.md) with an ordered list of configuration roles. Each candidate gets fresh derived member names and matching serializer roots.

## Use

Run the commands from a checkout with Python 3.14 and the checkout SDK on `PYTHONPATH`. Choose new destination paths.

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -B re/Fusion/SavedConfigEnvelope/PrepareRequest.py Original.f3d Request.json
python -B re/Fusion/SavedConfigEnvelope/GenerateSavedCuboid.py Request.json Candidate.f3d
```

The request carries the complete typed `camera_request` and `configuration_parts`. Use `[]` for explicit absence or list `table` and `rule` once each in the required member order. The generator emits the empty JSON objects and creates the Design triggers that refer to them. See the [configuration member order gotcha](../../../Gotchas/Conversion/Fusion/Geometry/Snapshots/FusionConfigPartOrder.md) and [configuration trigger record gotcha](../../../Gotchas/Conversion/Fusion/Geometry/Snapshots/FusionConfigTriggerGroups.md).

## Verification

All five configuration compatibility cases passed in 66.69 seconds. Fresh process replay preserved each requested role and its member order with the original archive absent. The checks read the actual ZIP members and verify the exact `{}` payloads, corresponding Design roots, and identities distinct from the original pair. Camera and parameter fields retained their earlier strict readback. The source projection refused a populated object and a pair using the same identity for both roles.

| Request from the tracked cases | Archive SHA-256 |
| --- | --- |
| Baseline control, table then rule | `af6b2d538a96d2b6a9253e0203245a5e124cd7f7f60460d03bb4f00253b6dac5` |
| Saved edit, rule then table | `0d83708a1ff0265abad4becfe2563da2555f52c11de127faabe0e512ab257014` |
| Saved edit requesting absence | `226b110a35e03f23611dc9cdf877e14ed45ce43ea6c8a7f2d14791eab9817156` |

The absent result matches the preceding camera-only producer byte for byte. An accepted empty input with JSON whitespace emits the canonical two bytes `{}`. Formatting of the member JSON does not carry configuration semantics. Nine additional fresh replays passed in 116.546 seconds. Fourteen invalid requests returned their expected errors without publishing a candidate.

## Limits

The experiment covers an absent pair or two present empty objects. Configured designs with variants or populated table and rule payloads remain unsupported. Named cameras and parameters retain their existing research scope. Graphics, selection, visibility, active viewport, appearance and procedural material state remain open. The strict version-2 read-only contract remains in effect. Native Fusion verification is pending.
