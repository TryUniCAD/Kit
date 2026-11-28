# Ordinary drawing Definition grammar in SOLIDWORKS 2026

The [locked drawing cohort](../v2026/heldout/DrawingSourceLock01.json) contains three disclosed single-sheet drawings and two sealed sources. The [Definition process](../../tooling/sw2026/serial/CheckDrawingDefinitions.py) verifies the disclosed documents and native readback receipts by hash, then decodes and re-encodes `Contents/Definition` and `Header2` with the shared archive registry. The [measurement receipt](../measurements/2026/DrawingDefinitionCheck01.json) captures six exact stream comparisons, 78 numeric checks, and zero tail bytes. It records the source lock digest independently of the earlier authoring attempt.

| Disclosed source | Definition bytes | Definition next map index | Header2 bytes | Header2 next map index |
| --- | ---: | ---: | ---: | ---: |
| `D00EmptySheet` | 28,950 | 212 | 907 | 34 |
| `D01FrontView` | 37,250 | 331 | 1,721 | 51 |
| `D02MovedFrontView` | 37,260 | 331 | 1,731 | 51 |

Run the process from the checkout with the oracle's disclosed source directory available. The process opens the three named disclosed cases and their two phase receipts. It hashes the native payloads and compares exact stream bytes in memory.

```text
PYTHONPATH=src python re/tooling/sw2026/serial/CheckDrawingDefinitions.py /path/to/disclosed-sources
```

## Definition framing

On pinned `slduiu.dll` SHA-256 `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7`, `uiModelDoc_c::Serialize` begins at `0x497011e0`. It stores the five prefix integers and the document CLSID before `0x4970137d`, which stores the embedded drawing model through virtual predicate `+0x1260`. The subsequent call at `0x497013ac` serializes its distinct `uoSketch` pointer. `uoSketch` writes the owning profile feature ID followed by a transform at `0x49f6ee60`. `uiUserModelEnv_c` saves the first splitter only for part or assembly at `0x497d5fa8` and `0x497d5fb8`. It stores the second splitter in the drawing too.

`uiDrawingDoc_c` is implemented in pinned `slddrwu.dll` SHA-256 `61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47`. Its primary vtable `0x3e1d6b78` binds `+0x1008` to `0x3debc450`. Once the shared `uiModelDoc_c` archive and the current drawing partition route return, the 2026 Definition trailer contains `u16 0x0daf`, `i32 f16c8` and `i32 f16dc`. The serializer's write sequence starts at `0x3debc9ed`. All three measured sources consume the trailer exactly. REA with Hopper confirmed the derived method and its common serializer call under evidence `ev_50e48af2aa6b1a2e226caaa1051057c915359ae0ea712e45cc880694ae252573`. The task-owned Hopper document is closed.

The drawing CLSID `83a33d34-27c5-11ce-bfd4-00400513bb57` selects an embedded `moDrawing_c` at archive version 19000. The model serializes `moHeader_c` inline through `sldmodu.dll` `0x4c17beea` and reads it at `0x4c17c456`. Config streams for parts and assemblies prebind their header objects. `moModel_c::SerializeLWData` checks the drawing predicate `+0x1b0` at `0x4c22ee5d`, bypassing its face visualization properties. The shared model's lightweight and resolved data are both inline in this drawing Definition.

## Sheet and view ownership

The model's concept node list contains the document sheet and standard drawing folders. `moDrawing_c.f1430` resolves to the same `moDrSheet` object in that list. The sheet's concept owns the sheet plane, sketch, detail folder, and optional `moAbsoluteView`. The linked drawing child uses one directory entry reached three ways through `moHeader_c.f30`, `moDrView.f5d8` (an internal reference) and `moDrwCompPropMgr_c` (a model reference). The view's `moReferenceInternal_c.f3c0` carries the child configuration. The external directory entry's optional configuration remains unset in the measured examples.

| Wire owner | Measured interpretation |
| --- | --- |
| `moDrSheet.f39c`, `f3c0` | Paper-size and sheet-format enums |
| `moDrSheet.f3f8`, `f400` | Sheet scale numerator and denominator |
| `moDrSheet.f3f0`, `f3e8` | Paper width and height in metres |
| `moAbsoluteView.f1018` | Base view orientation name |
| `moDrView.f778` | Position in sheet coordinates, metres |
| `moDrView.f780`, `f788` | View scale numerator and denominator |
| `moDrView.f5e0` | Model-to-view transform |
| `moDrView.f6d8` through `f6f0` | Sheet-space outline, min X, min Y, max X, max Y |
| `Header2.moHeader_c.bbox` | Centre, maximum, minimum and radius derived from the view bounds |

`moDrView::Serialize` sets condition `0x40` at `0x4c958f87` and restores it at `0x4c95cb24`. The view's nested `moAtomFeature_c` omits the `f3d0` presence word for this context. The same class on the sheet continues using the normal context. The two views check the condition through an exact stream round trip and the COM measurements. [View archive context](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingViewsSetArchiveContext.md)

The three sources establish typed reads for one stock paper sheet with no sheet format, with zero views or one ordinary front view. The current Definition reader fails when it reaches unclassified drawing fields. `Contents/DisplayLists`, `Contents/VBLists`, drawing keyword/property fields, other view families and native writer construction require separate qualification. [Adjacent release qualification](AdjacentReleaseQualification.md)
