# Source-owned translated FreeCAD box stock

Task `B04-SW2026-FCSTD/placed-stock`, owner `/root/release_path`, delivery PR #121. This internal preparer extends the [origin box stock projection](SdkFreecadPrimitiveStock2026.md). It depends on the original FreeCAD placement and shape owners, the existing SOLIDWORKS signed offset datum and the native local point-fix relation. The current exit consists of deterministic construction and linked host archive readback. Native lifecycle, exact public evidence and complete transfer of the original input remain open. [Guarded receipt](../measurements/2026/SdkFreecadPlacedStock01.json)

| Immutable source | Stock subset | Authored origin in mm | Size in mm |
| --- | --- | --- | --- |
| FreeCAD 1.1.4 `ParametricControl.FCStd` | All actual primitive geometry, one `Specimen` and one solid | 4.25, 6.125, −2.25 | 17.375 × 13.625 × 9.75 |
| Legacy C151-P01 | Translated `Box001` only | 181.8, 0, 0 | 160 × 400 × 5 |
| FreeCAD 1.1 C057-P01 | Rotated `Box001` refusal | 2000, 6000, 0 | 200 × 500 × 100 |

The source planner verifies the actual retained primitive, exact dimension values and aliases, zero attachment and empty expression state. The newer layout has an explicit current attachment engine and an independently owned `ShapeMaterial` UUID. The planner validates its type without claiming transfer of the material. It derives world bounds from the source placement, then corroborates the eight already-placed OCCT vertices, twelve line carriers and six outward planes of the actual bound Shape. A source Shape carries no bytes into the SOLIDWORKS writer.

The SOLIDWORKS construction uses `moFaceRefPlnData_c` with its independent driving distance for the nonzero normal displacement. The relative sketch plane uses the real generated datum reference and frame. The four orthogonal contour relations and the [native logical point fixation](CircleCenterFixation2026.md) keep the actual first corner at the independent planar coordinates. Two point-pair values retain the source Length and Width aliases. The boss has its own Height alias and a forward blind end. Local placement changes the coordinates and support owners while preserving driver allocation and the common part streams.

Both generated files pass typed Config, CMgr and Resolved framing with the actual linked atom-free model, exact self path, three independent driver aliases and the selected contour corner. The proof rebuilds the six-faced solid analytically from the read-back owners and compares all six planar loops, twelve edges and eight corners to the source. It also checks volume, area and derived centroid, and refuses a deliberately retargeted fixed-point handle. No hidden cached Parasolid geometry is present.

The translated C151 edge subtraction produces a Length residual of `2.84e-14` mm. Converting the normal translation from mm to metres and back changes the standalone bound by one binary64 step. The host geometry comparison uses `1e-10` mm for corners, and the dimension comparison uses `1e-12` relative tolerance. The candidate digests remain exact.

C151's original companion box remains outside its selected-stock construction. The standalone projects its sole real solid and retains the original logical body owner. Its remaining source document properties, presentation and assigned material still require separate proof. The physical oblique case's angle is about a non-principal axis. The proof normalizes the stored axis and independently derives all eight world corners with Rodrigues' formula. The signed parallel-plane route refuses the rotation. [Source placement gotcha](../../../Documentation/Gotchas/Conversion/Freecad/Primitives/BoxShapeAlreadyCarriesPlacement.md)

Both intact sources continue to refuse public SDK writing. The standalone's strict public reader expects the current circular offset grammar and refuses the changed profile. C151 design-only reading recovers the live names. Full public read refuses because the unqualified fixed-corner variant has no retained geometry cache. The linked archive verifier runs separately and leaves these public boundaries intact.

Run the host proof with the disclosed source inventory and the existing standalone. The optional candidate directory must be new and outside the repository. Keep candidate bytes outside Git.

```sh
python3.14 -I -B re/tooling/sw2026/freecad_census/primitive_stock/ProvePlacedStock.py \
  --inventory /absolute/path/PublicFcstdWriterCensus01/VerifiedInputs01.json \
  --standalone /absolute/path/FreeCADRuntime114/DisclosedSources01/ParametricControl.FCStd
```

For a later controlled native comparison, use the declared Windows locators in the receipt. Check the after-rebuild world bounds, signed reference plane, fixed in-plane corner and every live alias. Edit each stock dimension independently with the first corner held fixed, then check updated geometry, save and reopen in a fresh process between healthy controls. This host evidence adds zero native, held-out or FCStd corpus acceptance.
