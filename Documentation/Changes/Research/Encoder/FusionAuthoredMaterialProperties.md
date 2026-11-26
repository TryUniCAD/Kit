# Authored material properties in a Fusion cuboid

This research procedure generates a cuboid from a typed material request. It extends the [saved configuration request](FusionSavedConfigEnvelope.md) with a material family, structural mechanics, optional thermal properties, finish and component default assignment. The body links a physical asset and its associated appearance. Kit derives the package and its identities from the requested semantics.

## Use

Run the commands from a checkout with Python 3.14 and the checkout SDK on `PYTHONPATH`. Generate from an explicit JSON request and an unused output path.

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -B re/Fusion/SavedMaterialProperties/GenerateSavedCuboid.py Request.json Candidate.f3d
python -B re/Fusion/SavedMaterialProperties/PrepareRequest.py Candidate.f3d Readback.json
```

The wrapper keeps the preceding `configuration_request`. Its nested cuboid establishes the material label, density and RGBA. `material_properties` specifies the structural class and type, mechanics, thermal and finish data, and whether the same physical asset is the component default. The rich properties do not replace the camera, parameter or empty configuration bindings.

Use the `Basic` structural class with `Generic` type, an opaque finish and `thermal: null`. Use `Metal` with `Metal` type, a metallic finish, isotropic mechanics and explicit thermal properties. Moduli and strengths use pascals. Conductivity uses watts per metre-kelvin, heat capacity uses joules per kilogram-kelvin, and expansion uses inverse kelvins. Structural and thermal density, conductivity and heat capacity are independently stored. See the [complete explicit material cases](../../../../tests/Convert/Api/Fusion/SavedMaterials/RichMatInputs.py).

## Verification

All four tracked compatibility cases passed in 58.24 seconds. The two positive cases generated from persisted JSON with the original archive absent. Independent SDK readback checked the linked material and optional component default. A fresh preparation reproduced the request including its camera and configuration data. The two known saved appearance families refused preparation with the explicit alias diagnostic.

| Authored candidate | Generated archive SHA-256 |
| --- | --- |
| Basic material, body assignment | `d6e7f6fc0d87f0a8076f70abd57913a98c03c521d69f8e311fa4ea04bc348d7c` |
| Metal material, body and component assignment | `3091716b8bf48b55ac08db6f4012dcded2ef21bbc48cea8aa9ee12a6643efe0c` |

Eight independent fresh replays passed in 120.365 seconds. They reproduced exact archive bytes and verified deliberate changes to physical and thermal density, modulus, thermal conductivity, directional expansion and roughness. The CLI refused 20 invalid requests and the four original saved sources. Each refusal left its destination absent.

A package with one unused appearance survived strict readback and failed material preparation with the ownership diagnostic. A package with typed resources survived the lower codec and failed at the earlier strict public JSON boundary.

## Limits

The scope covers independently authored material semantics. The saved source controls carry a legacy appearance alias and a separate modern physical appearance aspect. They also retain texture-mapping layers. Those dependencies require explicit modeling before saved source preparation can admit them. A controlled typed change to legacy glossiness did not affect the modern finish or public material, confirming that the legacy values require their own representation. See the [saved material ownership gotcha](../../../Gotchas/Conversion/Fusion/Materials/FusionSavedMaterialOwners.md).

The procedure does not qualify whole saved-source admission, populated configurations, native Fusion acceptance, previews, graphics, visibility or selection. The strict version-2 read-only contract continues to apply.
