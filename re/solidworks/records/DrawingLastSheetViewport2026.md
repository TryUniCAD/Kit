# Drawing sheet pan and zoom ownership

Task `B04-SW2026-DRAWING-NOTES-C10`, root-owned oracle and integration, delivery PR #121. This construction component supplies the planar viewport on an ordinary unlinked drawing with one plain note. It uses the already validated [shared view input](ThroughAllSourceView2026.md) and typed drawing graph.

The [native ledger](DrawingLastSheetViewport2026.json) binds exact SP05.2 images, six function spans and ten import cells. `moDrSheet::getLastOrientation` returns zero for an absent pointer at `+0x430` and copies the actual transform when present. The setter allocates then assigns that transform. The 2026 serializer writes one presence byte and the embedded transform when present. The current load uses the same owner. `uiDrawingView::updateToNewSheet` calls that getter and then `uiModelView::setPanZoomXform` at `0x3df62c6f` when the getter succeeds. The separate `+0x418` slot is the border profile and carries the profile operator. It is absent in all six inspected disclosed states.

All five inspected states with an owned last orientation store the same transform in the active sheet and Definition UI `faf0`. Four native original and edited states retain the same installation pan and zoom. The generated first-save derivative owns an identity pan/zoom transform. The initial generated file has no sheet transform and keeps identity in UI `faf0`. These states come from the disclosed [typed field inventory](DrawingPlainNotePresentation2026.md).

The internal constructor accepts optional typed planar `ViewInput`. Its orientation is identity and its shift is in the sheet plane. The shared factory derives the pan/zoom transform from authored translation and positive scale. The sheet owns one embedded value and the Definition UI owns a distinct copy. The default recipe retains its earlier exact bytes.

The [guarded construction receipt](../measurements/2026/DrawingSheetViewportConstruction01.json) covers six fresh workers. Two independent pan/zoom choices grow Definition by 34 bytes each. The third positive reproduces the prior complete container exactly. All six other streams stay byte-identical and the Definition map counter stays 169. Both authored poses survive the complete typed Definition read and re-emit. Input file reads during generation are zero. Out-of-plane pan, zero zoom and unknown input fields refuse before output.

The [readonly viewport observer](../../tooling/sw2026/drawing_notes/ObserveNoteViewportInput01.py) freezes the two authored poses, identity default and three native control phases at `b775d4b86642c2544e6a963278556ec48e5b8fbd432a759e13afb556b3fada52`. The recipe checks the actual camera and note geometry before and after rebuild. The construction check qualifies the archive fields. Rendered parity still requires its own native evidence.

[Change entry](../../../Documentation/Changes/Solidworks/Construction/Drawings/SolidworksDrawingSheetViewport.md) · [Gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/Sheet/SheetLastOrientationOwnsPanZoom.md)

## Interrupted first native trial

The [interruption receipt](../measurements/2026/DrawingSheetViewportInterrupted01.json) records clean pristine, disclosed native and default generated phases. The first authored camera candidate opens with status `[0,0]`. Automation loses the drawing interface at `GetFirstView` before measuring the camera. Its owned process remains alive and prevents the second candidate and trailing pristine control from starting. The exact process is verified by executable digest and creation identity before being stopped. No SOLIDWORKS process remains afterward.

The incomplete bracket establishes no native verdict for either authored camera. The guarded archive construction and prior complete viewport comparisons retain their own separate evidence. The existing [drawing COM gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Drawings/DrawingActiveViewProbeCanLoseCom.md) describes controlled recovery.

The retry freezes the exact same three generated files at trial SHA-256 `14120a7c97cad5c110c3ade56a0a3ed3712b0f5305949f9b0780f7249f2410d7`. Its observer reads the initial live camera before drawing traversal or redraw. Each `phase --role` invocation starts and closes one owned application. The second authored camera goes first so the first interrupted input cannot hide it. A separate two-process readback verifies that integer and floating-point spellings of an equal zoom produce identical archives.

## Measured native camera restoration

The [retry](../measurements/2026/DrawingSheetViewportNative01.json) completes all six fresh guest processes. There are zero open errors or warnings, three healthy controls, and no recovery or settings writes. The generated identity view and both independently authored pan and zoom values are exact on initial open and survive rebuild. The note and all measured sheet/tree fields stay intact. Both generated authored-camera images equal the pristine blank frame byte for byte. The native note source has a distinct rendered image.

This establishes scoped native camera restoration and leaves source/presentation acceptance open. The native verdict attaches to the exact two generated camera forms and unchanged note state. Raw invocation SHA-256 `8fc9038c44d00739ed8e80a1032cf59fcdde81c819c874a06c94dd913d0e0f20`.
