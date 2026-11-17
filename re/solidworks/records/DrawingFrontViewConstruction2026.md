# SOLIDWORKS 2026 ordinary front drawing view construction

The source-only projection and object constructors cover one ordinary `*Front` view at explicit 1:1 view scale on the generated unformatted ANSI A sheet, referring to a forward blind, XY-aligned rectangular prism. Two independently authored requests round-trip the typed reference and sketch support subgraph. The complete populated drawing still requires its view-state fields and projected-edge maps. [Locked disclosed sources](../v2026/heldout/DrawingSourceLock01.json) · [Construction measurements](../measurements/2026/GeneratedFrontViewGraph01.json)

All image addresses below refer to the pinned SOLIDWORKS `34.5.2.0604` file `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The named orientation constructor is `moAbsoluteView` at `0x4b744590`. Its own fields follow the `moDrView` serializer at `0x4c958dc0`. The common construction path begins at `0x4c986b70`. [View archive context](DrawingDefinitionGrammar2026.md)

## Projection values

| Wire owners | Rule for this profile | Evidence |
| --- | --- | --- |
| `f5e0`, `f778`, `f780/f788`, `f1018` | Identity orientation with translation equal to requested sheet position minus child model centre. View position and independent 1:1 ratio are authored. | Named view factory `0x4b744590`, custom scale setter `0x4c9b80d0`, `moveViewAbsolute` at `0x4c9b0080` |
| `f600`, `f648`, internal reference `f370` | Child-local body box and centre derived from the generated sketch's placed vertices and extrusion extent. | `setCachedModelBBox` at `0x4c9b5600`, `setRefPoint` at `0x4c9b6da0`, measured child-local coordinates |
| `f718..f730`, `f738..f750` | Raw XY extents use requested centre plus or minus the corresponding child half extents. | `moveViewAbsolute` at `0x4c9b0080`, `setModelGeometryOnlyBox` at `0x4c9b6710`, both disclosed positions reproduce the stored doubles |
| `f6d8..f6f0`, `moHeader_c.bbox` | Expand the raw XY extents by `0.02 × min(paper width, paper height)` on each side. Header centre is the view position with Z zero. The radius is the half diagonal of the expanded rectangle. | `getDrViewBorderMargin` at `0x4c9cd630`, expanding the rectangle at `0x4c9a6eaa–0x4c9a6ebc`, both disclosed headers reproduce all ten numeric fields |

The margin depends on the paper dimensions. The raw rectangle centre follows the view itself, independently of the model's coordinate origin or the sheet scale. The disclosed files have a 5:1 sheet and a 1:1 explicitly scaled view. Evaluating the box from the view centre and half extents also reproduces the native rounding at both placements. [Bounds arithmetic gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingViewBoundsUseCentre.md)

## Object graph

- The view's `f5d8` owns `moReferenceInternal_c`. At `0x4c98777f` the view constructor calls the internal constructor at `0x4bbb74c0`, assigns the result to `f5d8` at `0x4c987789`, and sets the real configuration at `0x4c98779a`. The reference retains the generated child box and has one `moExtFeature_c` pointing back to it and to the containing drawing file.
- The component-property manager owns a separate unnamed `moReferenceModel_c`. Its registration path calls the constructor at `0x4c97110c`, selects the existing reference's configuration at `0x4c971122` and removes the extra file connection at `0x4c971133`. Thus the one directory entry has one connection even though two records refer to it. The manager owns an allocated empty property array in the measured profile.
- The directory uses the actual generated part identity with no selected configuration. Each reference stores the actual generated part configuration. File and update stamps use the existing ordinary generated-part rules. The disclosed controls carry counters from a native-loaded child, so the standalone prototype starts from the generated child's actual state. This still needs a native open and save measurement. [Shared file and reference rules](OrdinaryOccurrenceConstruction2026.md)
- Each view owns a detail folder, a sheet-plane/profile pair and a model-plane/profile pair in that order. Their persistent IDs are allocated with the detail folder before the view itself, and the two pairs after the view. `createProfileFeature` at `0x4c9952b0` selects a drawing plane via `0x4c2d40d0`, passes the drawing self component from `0x4c9953ad` and sets sketch transforms at `0x4c99557f`. The drawing plane uses the sheet position, +Z and its inverse translation. The absolute plane uses the child box centre, +Z and its inverse translation. Its display origin is the upper left of the default reference rectangle at that centre.
- Both sketches bind a component-plane handle before the plane receives a persistent ID. The inline plane pointer resolves to the actual allocated plane. The model-side profile's disclosed save has small transform recomposition differences from its plane at the floating-point word level, consistent with the `mgXform_c` product and inverse in the sketch update path `0x4c0e53ff–0x4c0e5418`. The generated empty profiles use the current plane transforms. [Shared sketch support rule](DrawingEmptySheetObjects2026.md)

## Verification boundary

`DrawingFrontGraphProcess.py` accepts a JSON object containing a `drawing` blank-sheet request, a `part` generated part request with a file identity, and a `view` with `name`, `orientation`, two sheet coordinates in `position`, `scale`, and `supports`. The five support names are `detail`, `sheet_plane`, `sheet_profile`, `model_plane` and `model_profile`. The process generates the part and drawing base from stdin. It writes, reads and re-encodes a test archive with the drawing and view owners prebound, using view condition `0x40` for the support nodes. It verifies the imported file identity, both plane-pointer aliases, the external-feature backlink and the manager ownership.

```sh
uv run --isolated --frozen --extra dev --python 3.11 python -B \
  re/tooling/sw2026/DrawingFrontGraphProcess.py < /private/authored-front-view.json
```

The two guarded requests varied part dimensions, authored names and view positions. Their support graphs each consumed 4,755 bytes with next map index 67 and next persistent ID 16, with two distinct hashes and zero runtime input reads. This process constructs a subgraph and reports `native_acceptance: false`.

The full view serializer stores additional presentation and update state. In both disclosed files drawing `f1570` has one model/configuration key and four `moEdgeRef_c` rows. The `addNodeIDtoEdgeRefMap` method at `0x4c98bc70` gets the stored key through `getModelName_ConfigID` at `0x4c98bcab` and accesses the owning drawing's map at `0x4c98bcdb`. Each measured row has one extrusion-end surface and three sketch-entity surface identities. The generated source needs the precise topology enumeration, reference state and cache ownership before the populated Definition can claim complete construction. The current blank save trial and sealed drawing sources remain separate from these results.
