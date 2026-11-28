# Preserve Fusion face material journal attributes

The Fusion journal codec reads and emits
`NEUTRON_Material_attrib_def` as a typed application attribute.
It keeps the UUID spelling and validates both directions of its live
face-ownership chain. The UUID binds to the Design body's typed
`faceVisualMaterialByAttrTagID` map. A map entry and the styled
graphics face should resolve the same Protein asset.

Run the existing journal and native-color CLI integration checks.

```text
python -m pytest -q tests/Convert/Formats/FusionCodec/Brep/Journal tests/Convert/Formats/FusionCodec/Documents/Reading/JournalPartTests.py tests/Convert/Integration/Fusion/NativeCutColorCliTests.py
```

Fusion 2706.1.17's plain, top-red and side-red cuboids and an independent
historical cut control retained byte-identical journal output and complete
typed archive readback. The two colored cuboids retained the attribute
through typed JSON. Mutations with a body owner, missing owner or
non-reciprocal previous link refused. All 17 focused integration cases
passed on Windows Python 3.14.6.

Public strict decode still refuses the native Design reference class
`BFB592FE-03DD-4DAA-A4AC-14D02ABB672A`, and public writing remains
read-only for the saved cuboid route. See the [measured face
relationships](../../../../re/Fusion/SavedCuboidRoundTrip/DisplayOrderContrast.md#face-assignment-observations)
and [API identity gotcha](../../../Gotchas/Conversion/Fusion/Api/FaceAppearanceSourceIdentity.md).
