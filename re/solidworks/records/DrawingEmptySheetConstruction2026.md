# SOLIDWORKS 2026 empty drawing sheet construction

The first construction boundary is an ANSI A landscape sheet without an external sheet format. The [sheet builder](../../tooling/sw2026/builders/DrawingSheet.py) accepts a paper size, sheet name, positive integral scale numerator and denominator, document length unit and property-view name. It computes the paper fields and the two sketch coordinate frames. The [index builder](../../tooling/sw2026/builders/DrawingMetadata.py) publishes the sheet identity and geometry in `KeyWords` and `ISolidWorksInformation.xml` from those same inputs. These are partial research builders for the sheet and its indexes. A native file requires the rest of the Definition graph and an independently qualified stream set.

## Sheet values and coordinates

All model addresses in this table are from `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The `sldmfcu.dll` SHA-256 is `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`.

| Field or role | Classification | Rule and evidence |
| --- | --- | --- |
| Name and `f3f8/f400` | Authored, confirmed readback | Sheet name and selected scale numerator and denominator. `moDrSheet::updateSketchScale` loads both at `0x4c9d7c11–0x4c9d7c48`. D00 is 1:1, D01 and D02 are 5:1. |
| `f39c/f3e8/f3f0` | Derived from paper selection, confirmed readback | ANSI A landscape paper code 0, width 11 inches, height 8.5 inches. The native reset at `0x4c9d06c3` initializes the code and loads SI dimensions at `0x4c9d06d7–0x4c9d06f7`. |
| `f3c0/f3b8` | Enumerated format state, confirmed readback | The unformatted sheet has `swDwgTemplateNone` value 13 and template name `*.drt`. The latter is the native string at `0x4d27b440`, used by the fresh sheet reset at `0x4c9d071f`. |
| `f3d0` | Authored, confirmed readback | The property view name. `setPropertyViewName` and `getPropertyViewName` own the name. The disclosed profile uses the explicit name `Default`. |
| `f4a8/f4b0/f4b8/f4c0` | Derived, binary rule and three controls | `setDefaultZones` chooses margins from its document length unit and clamps each pair to half the sheet axis minus 0.005 m. Metric base margin is 0.01 m and imperial is 0.5 inch. The width pair is `f4a8/f4b0` and the height pair is `f4b8/f4c0`. Code at `0x4c9d3191–0x4c9d31fb`. |
| `f4c8/f4cc` | Derived, binary rule and three controls | The native rows at `0x4db092e0` (metric) and `0x4db09290` (imperial) contain axis thresholds and zone counts. The loop at `0x4c9d3260–0x4c9d3327` starts each count at 1 and selects a row when the axis is at least its threshold and below the next threshold minus `1e-8` m. Axes below 0.01 m disable default margins and both counts stay at 1. |
| Zone mode `f4d8` | Derived state, binary rule | The default-zone setter initializes the mode to 1 at `0x4c9d30ef`. The disclosed template carries mode 0 with the same computed dimensions and zone counts. The construction calls for the explicit default mode. |
| `moRefPlane_c.f6f8.f20`, `moProfileFeature_c.pd_ff0` | Derived, binary rule and independent scale values | Both transforms use the reciprocal sheet ratio for the ordinary sheet. The profile update at `0x4c9d7c34–0x4c9d7c74` constructs the scale transform from `1/(f3f8/f400)`. The two 5:1 sheets store 0.2. |
| `uoSketch.f80` | Derived, confirmed readback | The distinct UI sketch uses the forward sheet scale. Its profile ID is allocated by the native graph owner. The disclosed sheets store 1 and 5, with identity rotation and translation. |

The unit predicate is `sldmfcu!moLengthUserUnits_c::IsMetric` at `0x3c753ef0`. It reads the length unit enum and dispatches through the table at `0x3c753f24`. Metric codes are 0, 1, 2, 6, 7 and 8. The three disclosed sheets use millimetres and therefore evaluate the metric zone rule despite their ANSI A paper dimensions. The generated index check independently uses both millimetres and inches.

The drawing info writer at `slddrwu!0x3ded4af0` calls the sheet-format helper `0x3dee7110`, which iterates actual sheets, calls `getPaperSizeByDimensions` and records measured dimensions alongside scale and template state. The two generated index sets carry different names, IDs, units and ratios and pass the current SDK property parsers. [Pinned native readback and generated indexes](../measurements/2026/DrawingSheetFields01.json)

## Required object ownership

The `moDrawing_c` constructor at `0x4c96b480` allocates a `moDrSheet` with the drawing as owner and binds the active sheet pointer at `0x4c96b914`. `addSheet` at `0x4c9717d0` adds the sheet to the drawing concept and registers its actual persistent ID. The ordinary sheet constructor and reset at `0x4c9c6970` and `0x4c9d0650` establish the sheet-owned stock graph:

- The first child is a default sketch support plane, created at `0x4c2d3fe0`. This is `moAbsoluteRefPlnData_c`, with origin at the coordinate origin. Its explicit plane subtype differs from a part's principal reference plane.
- The second child is an empty profile sketch. The reset obtains the drawing's self component at `0x4c9d0842` and calls the common `createProfileFeature` at `0x4c9d0856`. The pointer at `f408` aliases that child. A component-plane wrapper points to the actual plane object.
- The third child is a `moDetailFolder_c` pointer constructed at `0x4c9d07f5`, later added to the concept list. The pointer at `f390` aliases that child.
- The UI document carries a separate `uoSketch` with the profile's persistent ID and the forward transform.

A fresh allocator must respect that creation order separately from archive visitation order. The six drawing folders precede the sheet in the persisted concept. Two template-independent folder roles remain unnumbered in the disclosed files. The model and inline header share the self file, profile references use the actual sheet plane, and the model's active pointer resolves to the same sheet object. [Definition ownership and checked archive order](DrawingDefinitionGrammar2026.md)

## Stream obligations

The disclosed controls have 29 streams. That inventory establishes presence. The storage dispatch and one-variable vendor tests determine which cached streams can be omitted.

| Streams | Current classification |
| --- | --- |
| `Header2`, `Contents/Definition`, `_MO_VERSION_19000/History` | Typed graph and current-version lanes. The model header is inline in Definition. Reuse the shared header and history field constructors. The drawing self entry owns native document kind 4 and no selected model configuration. |
| `_MO_VERSION_19000/Biography`, `ModelStamps` | Shared historical record and derived stamps. The disclosed stamp stream contains creation time, model update stamp and body change stamp. |
| `swXmlContents/KeyWords`, `docProps/ISolidWorksInformation.xml` | Generated sheet indexes now available. Qualify the reduced property inventory in the vendor before using it in a native file. |
| `Contents/DisplayLists`, `Contents/VBLists`, `_DL_VERSION_19000/DLUpdateStamp` | Derived UI state. The vendor accepted each single omission from the disclosed blank and restored it on save. |
| `SheetPreviews/SheetNames` | Derived preview index. The vendor accepted this single omission from the disclosed blank and regenerated its 22 bytes on save. |
| `Preview`, `PreviewPNG`, `Images/Sheet_0` | Remaining preview payloads. Their omission and regeneration still need measurement on this drawing lane. |
| `Contents/CusProps`, `swXmlContents/CustomProperties`, `docProps/app.xml`, `docProps/core.xml`, `docProps/custom.xml`, `docProps/OpenTime.xml`, `[Content_Types].xml`, `_rels/.rels` | Property and package metadata. Additional native read dependencies remain to be traced. |
| `Contents/OleItems`, `OleItemInformation/OLE_Item_Data`, `Contents/3DExperienceExchange2`, `Contents/eModelLic`, `DWG/DWG_HEADER`, `SwDocContentMgr/SwDocContentMgrInfo`, `ThirdPtyStore/VisualStates_DisplayPane` | Auxiliary document capabilities and integration state. Avoid substituting fixed captured data. Determine reader defaults or generate structured neutral values only when their domains are classified. |

The [empty manager construction](DrawingEmptyManagers2026.md) supplies drawing flags, the draw property manager, layer mask and sketch-block manager from the generated graph. The sheet's standard support nodes, drawing-specific UI state and optional visual state still require work.

The [cache diagnostic preparer](../../tooling/sw2026/PrepareDrawingCache.py) accepts the disclosed oracle directory and an unused private directory outside the checkout. It verifies the D00 bytes and their two native source receipts. It creates an unchanged drawing, a fully repacked control, and separate omissions of `Contents/DisplayLists`, `Contents/VBLists`, `_DL_VERSION_19000/DLUpdateStamp` and `SheetPreviews/SheetNames`. Each retained logical stream remains byte-identical. The private packet records the file, input and tool hashes.

Run the [pinned oracle script](../../tooling/sw2026/InspectDrawingCache.py) with the packet and `--packet-sha256` on the measured Windows build. It requires unmodified bracketing controls and the repacked control. Each experiment checks resolved open, rebuild, active sheet tree, a 3:2 edit, save and fresh reopen. It watches for dialogs and rechecks input and tool hashes. [2026 sheet API](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISheet_members.html) · [Sheet scale edit parameters](https://help.solidworks.com/2020/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISheet~SetScale.html?format=P&value=)

The four single omissions passed on executable version `34.5.2.0604` across fourteen distinct processes, with healthy before and after controls and a healthy repacked control. All retained the ten-row native tree and the original sheet dimensions. The 3:2 edit rebuilt, saved and reopened with zero errors or warnings. Native saves restored all four omitted streams at sizes 3,249, 8, 6 and 22 bytes respectively. This measures independent cache omission in the disclosed blank drawing. Combined omission, populated drawings and generated file acceptance still require their own trials. [Sanitized omission receipt](../measurements/2026/DrawingCacheOmissions01.json)

Pass `--combined` to the preparer for a separate packet containing the same pristine and repacked controls plus a copy omitting all four display indexes together. Its native comparison and result are separate from the measured single omissions.
