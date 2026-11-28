# Attached note depth and the native planar setter

Task `B04-SW2026-DRAWINGS`, owner `assembly_occurrence`, delivery PR #121. The native setter's **conditional in-plane offset rule is confirmed by exact-build source**. The disclosed native lifecycle now verifies the expected Front-view note depth, including two independent Z-only requests. The full attachment-to-view cache provenance and live planar-mode predicate remain partial. Root owns native execution and integration.

Dependencies are the [native correspondence proof](DrawingEdgeCorrespondence2026.md), [note attachment owners](DrawingNoteAttachmentOwners2026.md), exact registered 2026 API metadata and the unchanged part/view/annotation lifecycle guards. Exit requires controlled original and independently generated geometry to preserve the full note attachment, coordinates, edit/rebuild, save and fresh reopen. Hidden, production and downstream-cache qualification remain separate.

## Preserved native stage

The preceding trial SHA-256 is `bf759fd068dcc988f34c7f81c46d262bc822682788dfc8abc102cfbbe31cb302`; terminal result SHA-256 is `ec4f7fd0edf20c15ad6c493f5a2529de61dbadf23f0dfe0293ba8ccaa87b397e`. Both full control verdicts remain false and the generated lane was skipped.

Each original control proved drawing→part→drawing native edge identity, its reverse round trip and exact membership in the actual part body's twelve-edge inventory. Both then accepted `SetAttachedEntities` and `SetPosition2(x,y,0)`. The next `GetPosition` returned `(0.09541000000000001,0.08763,0.0035) m`. Original X/Y assertions passed exactly; only index 2 failed against zero. No note edit/save/fresh reopen followed. The before/after raw record hashes remain `b25d9d9bb63a53ff1838415d7752a09adeb057ab2cce31cfef848ba8c55b3aaa` and `1ac968c293ec75dbb44a95d280495bbe3b5015e0375e8edd5acef945aa4f86e5`.

The actual/frozen transform has scale **one** and translation Z `-0.0035 m`. The selected cap has model Z `0.007 m`; transforming it gives `0.0035 m`. Half-depth is a numerical coincidence of this centered view, not evidence of scale `0.5`. Absolute model depth, requested sheet Z and transformed attachment depth are distinct owners.

## Exact native proof

The [numeric source record](DrawingAnnotationDepthSources2026.json) binds fifteen complete functions or explicitly bounded leaves, 4,395 bytes, thirteen vtable cells and the real imported Z setter. It binds original `sldapiu.dll` SHA-256 `97bc3d859637c8b420108a1a3ebd4262580fa45d05c761874df7658fad49b6c2` and `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Raw images and private listings stay outside the checkout.

| Boundary             | Exact route                                                                                        | Independently authored finding                                                                                         |
| -------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Registered API       | `auAnnotation_c::XDispatch` vtable `0x4321b5d8`, slots `+112/+904`                                 | Actual `GetPosition` and `SetPosition2` entries are `0x42aaef80` and `0x42ab5c30`                                      |
| API core             | `0x42abaaf0`, `0x42abdac0`                                                                         | Getter returns three coordinates; setter retains all three requested inputs and dispatches by the actual display owner |
| Ordinary note getter | `moDisplayNote` `+0x3b0 → 0x4be6d3f0 → +0x4c0 → 0x4c7fb480`                                        | Reconstructs text point from actual attachment, note frame and in-plane direction/distance                             |
| Ordinary note setter | `+0x3b8 → 0x4b347fb0 → +0x3c0 → 0x4c80cf70`, then `+0x340 → 0x4c80a520 → +0x4c8 → 0x4c80e830`      | Forms requested-minus-current translation, then computes requested-minus-attachment in the actual note frame           |
| Planar restriction   | `0x4c80e8b2` calls note `+0x380 → 0x4c807e00`; `0x4c80e8c4` calls the real `mgVector.set_z` import | When the predicate is true, the local offset Z is forced to zero before direction and distance are stored              |
| Predicate scope      | `+0x868 → 0x4b35cf20` reads `f644`; other subclass predicate is separate                           | This record does not rename or fit the live mode value as a generic constant                                           |

A dimension-only API transform branch is explicitly separate from an ordinary note. `getAttachLocation` at `0x4ba699e0` reads the actual display attachment point/cache owner; no saved point supplies a constructor default. Static proof of the entire live attachment-to-view cache calculation remains open. The constant-cap projection is therefore an explicit source-bound hypothesis for the next measurement, not a fully classified generic field rule.

## Current public API contract

The exact registered capture SHA-256 is `195f6c97fdb1f233897714040c9c664e6c58afefd934e30b4991e55e5b9134cc`, from a zero-CAD library query. It binds `GetPosition` DISPID 8/slot112, `SetPosition2` DISPID91/slot904, `GetPlane` DISPID92/slot912, actual view transforms and MathTransform arrays.

The official 2026 [getter](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAnnotation~GetPosition.html) returns three coordinates for the note's text origin in the drawing sheet frame. The [setter](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAnnotation~SetPosition2.html) permits native placement restrictions; a true return does not promise that all requested coordinates survived. [GetPlane](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAnnotation~GetPlane.html) returns only nine rotation values, not a translated plane origin. [Transform ArrayData](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks.IMathTransform~ArrayData.html) separates nine rotation, three translation and one scale values.

## Orthogonal frozen retry

The original cases, authored text, X/Y and requested Z=0 stay untouched. A separate prediction uses both selected cap endpoints and the complete explicit Front unit-scale transform. In this admitted profile, `Z_expected = Z_edge × scale + translation_z`; both endpoint depths must agree. The prediction is recomputed from the actual independently checked transform/edge before the note is measured.

The control prediction is `0.0035 m`; the independent generated child's prediction is `0.00715 m`, computed from its own `0.0143 m` depth and `-0.00715 m` transform translation. No measured note value feeds either calculation. Original X/Y and the existing `2e-9 m` position tolerance remain exact. The nine actual plane rotation values and requested/expected/observed positions are retained separately.

Two additional requests vary only Z to `depth/3` and `-2×depth/7`, keeping the original initial X/Y and text. The hypothesis requires the same independently predicted constrained depth after both requests. A mismatch fails visibly; it does not expand tolerances, ignore a coordinate or calibrate from the first returned position. Original text/position edits, attachment identity, persistent references, rebuild, save and fresh reopen follow unchanged. The actual drawing edge remains the annotation entity.

## Replay and limits

Use [PinAnnotationDepth01.py](../../tooling/sw2026/drawing_edges/PinAnnotationDepth01.py) with the licensed originals outside the checkout and the numeric knowledge file. Two independent runs reproduced receipt SHA-256 `f71c087bafae51c937ec72ddeff72cd007264384ec7c6907476aaea9b39d99b0`. No vendor instruction ran and no disassembler session was opened.

[FreezeAnnotationDepthRetry01.py](../../tooling/sw2026/drawing_edges/FreezeAnnotationDepthRetry01.py) requires the failed predecessor, exact API capture and this source pin. The resulting trial SHA-256 is `2c2ac4aa9a09a170c9667abc8d81d6cf5c25a4f6192cf436ef7380f14869adf7`; serial recipe SHA-256 is `d47fd1cde17014be7341d77d8c566cd461d99069596c16c3fe4a400b8a0c492b`. Root executes the six-process lifecycle.

Two fresh host verifies passed. Five modified metadata/source/tool/zero-expectation/wrong-cap packets were refused before native progress. All original case fields and sixteen unaffected packet files remain exact. This lane made zero VM/COM calls, hidden reads or shared source edits. The retry uses the same control and generated inputs and predicts each position before querying the application.

## Native lifecycle

Six distinct SOLIDWORKS processes complete the bracketed open, edit, save and fresh reopen. All six opens return 0 errors and 0 warnings, and all three saves return true with zero errors and warnings. Both controls preserve the same drawing-edge identity through reopen with depth `0.0035 m`. The generated linked pair preserves its distinct computed depth `0.00715 m` and its own persistent edge reference. Both additional Z-only requests agree with the independent cap-depth predictions. [Lifecycle receipt](../measurements/2026/DrawingAttachedEdgeNative01.json)

The application creates the attached note after opening the drawing. This evidence covers disclosed application persistence. Typed archive text placement, generated note encoding, downstream-cache consumption and held-out qualification remain open.
