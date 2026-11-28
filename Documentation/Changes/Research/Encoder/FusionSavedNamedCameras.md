# Saved Fusion cuboid named cameras

The named-camera research commands project the ordered named views of a strict saved fixed-corner cuboid. They extend the [saved cuboid parameter request](FusionSavedParameterBindings.md) and generate a new cuboid snapshot and view graph from persisted JSON.

## Use

Run the commands from a checkout with Python 3.14 and the checkout SDK on `PYTHONPATH`. Choose new destination paths.

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -B re/Fusion/SavedCameras/PrepareRequest.py Original.f3d Request.json
python -B re/Fusion/SavedCameras/GenerateSavedCuboid.py Request.json Candidate.f3d
```

The wrapper contains `schema`, `scope`, the complete typed `cuboid` request, and the ordered `named_views`. Each view has a name, its modification flag and the 16 known camera values. Position, target and up use the stored coordinate values. The empty list explicitly requests no named views. View, collection and camera links use newly allocated identities.

## Verification

Both saved controls carry the same four named cameras. The saved edit and restore carry an empty roster. Fresh processes projected each control into JSON and generated candidates with the original archive absent. Complete lower typed re-emission and strict version-2 public JSON preserved the order, camera fields and signed zeros. An independent synthetic request exercised changed camera values and repeated byte-for-byte regeneration. The previously reserved geometry control was already known, and its camera records match the baseline exactly.

| Source or request | Views | Generated archive SHA-256 |
| --- | ---: | --- |
| Baseline control | 4 | `3086b3c14ccd5414ca35240914c52fef7b153bfe29dff70402bb439c1b4caa61` |
| Saved edit | 0 | `226b110a35e03f23611dc9cdf877e14ed45ce43ea6c8a7f2d14791eab9817156` |
| Saved restore | 0 | `fea1fab677e07fea410904ed698ced1cc8fe6cd5fa79afafbcedd69b633d96c1` |
| Previously reserved control | 4 | `f394fde7993e5edab188fe99294aa1ac540799d409bf51175ac89a60e3621136` |
| Explicit custom camera | 1 | `c87f88b0fda80a769c90aad8ab76c03f3d73fc7084c5faffe6abe7459e55a404` |

The source projection rejected shared cameras and populated active viewport state. Generation rejected invalid vectors, unsupported projection and modification flags, duplicate names, inexact float32 input, a nonfinite derived direction, and a view direction parallel to the up vector. Occupied destinations were preserved. All five named-camera compatibility cases passed in 57.57 seconds. Nine independent replays passed in 103.103 seconds and covered a reversed roster, a changed camera position, a single-view roster, and byte-identical repeats for both populated and empty rosters. Twenty independent invalid requests returned their expected errors and published no files in 52.992 seconds.

## Limits

The measured camera profile uses projection `1`, automatic focus and an unmodifiable named view. Depth of field and mirroring are disabled. The request keeps the stored camera values without normalizing vectors or interpreting their units. Active viewport, default home, scene orientation and renderer settings remain separate. Read the [named view and viewport gotcha](../../../Gotchas/Conversion/Fusion/Geometry/Snapshots/FusionNamedViewDefaults.md) for the distinction.

The previous cuboid parameter restrictions still apply. The experiment leaves whole saved-source admission, full appearance and material state, visibility, selection, configured designs and direct Fusion verification open. The strict version-2 read-only contract remains in effect.
