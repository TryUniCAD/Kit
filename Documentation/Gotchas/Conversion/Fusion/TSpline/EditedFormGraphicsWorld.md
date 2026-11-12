# Edited Form documents store an unsupported graphics world

## Expectation

A Form document saved after a control-point edit has the same parts as the Form document before the edit. Kit can then read and re-emit it like the other local Form archives.

## Actual behavior

Three archives from the T-spline edit captures stop in the OGS graphics reader. Their `OGS.BlobFolder/OGS/DefaultScene/world` member contains a group whose world kind is 2. The graphics codec knows world kinds 0, 1 and 3, so `ReadDocument` raises `ValueError("Unsupported custom graphics world")`.

| Archive | World kind | Result |
| --- | --- | --- |
| `re/Fusion/LocalOracle/TSpline/BoxEdited.f3d` | 2 | `ValueError` |
| `re/Fusion/LocalOracle/TSpline/PlaneEdited.f3d` | 2 | `ValueError` |
| `re/Fusion/LocalOracle/TSpline/SymmetricBoxEdited.f3d` | 2 | `ValueError` |

The other 29 local Form archives pass the full read, emit and byte comparison. A research script disabled only the graphics reader for the three edited archives. `ReadDocument` then read each archive with one Form, one body and one snapshot, and the Form joins passed.

## Workaround

Do not treat the error as a Form or T-spline decode failure. Report the archive as unsupported until the world kind 2 layout is decoded with evidence. Do not skip the graphics member during re-emission, because the result would then not be byte-identical.

## Evidence

- [Form round trip](../../../../../re/Fusion/Reconstruction/FormDocuments/RoundTrip.json)
- [Edited world isolation](../../../../../re/Fusion/Reconstruction/FormDocuments/EditedWorlds.json)
- [Graphics cache omission](../FusionGraphicsCacheOmission.md)
- [Form document change entry](../../../../Changes/Fusion/TSpline/FusionFormDocuments.md)
