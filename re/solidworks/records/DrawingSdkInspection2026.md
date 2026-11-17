# SDK inspection of ordinary SOLIDWORKS 2026 drawings

The SDK inspects version 4 containers with model archive version 19000. It resolves the document type from the drawing CLSID, schema-one `moDrawing_c` declaration and drawing Definition trailer. A separate map walk decodes the entire `Header2` stream and validates its drawing self entry. The layout reader joins the sheet and view indexes with that header's external file directory. An external part link retains its saved path and selected configuration. The SDK opens the drawing alone.

For a single model view, `Header2.moHeader_c.bbox` contains the paper position and outline. The layout reader verifies a planar box with the recorded centre and independently derived sphere radius. Empty drawings carry neither a model link nor view bounds. `KeyWords` supplies the sheet and view names and sheet scale. The sheet-format and model-view lists in `ISolidWorksInformation.xml` supply dimensions and redundant ownership indexes. The measured view name and configuration match the source [authoring lock](../v2026/heldout/DrawingSourceLock01.json).

`open_document(source, strict=False)` returns `CadDocument.drawing` with that layout. The diagnostic `slddrw.layout_inspection` identifies the remaining view scale, orientation, model-to-sheet transform, annotation, styling and display geometry work. The typed research Definition reader measures the first three of those fields separately. `CadDocument.drawing` defaults to absent for existing model documents, and their JSON omits the new field.

Run the process check against the disclosed oracle directory:

```text
PYTHONPATH=src python re/tooling/sw2026/serial/CheckSdkDrawingLayout.py /path/to/disclosed-sources
```

The [process receipt](../measurements/2026/DrawingSdkLayoutCheck01.json) records three successful native layout reads and the resulting compact interchange JSON digests. Local checks matched the previous SDK output for the example part and the existing neutral assembly. The command-line `decode --partial` route returned the same active view-bearing sheet through the regular SDK adapter.

## Reuse in the exact native reader

The public archive cursor uses the shared tag, string, count and object-map primitives. The `Header2` decoder admits eight declared object classes and the shared file definition and bbox members. All ten rules are independently typed and none is marked provisional by the research registry. Its class table uses the exact archive version and class schema. Extension to an adjacent release requires the corresponding [qualification procedure](AdjacentReleaseQualification.md).

The drawing model object in `Definition` reaches 166 typed schema methods in the empty control and 198 in the two model-view controls. The complete stream reaches 186 and 218 respectively. The qualified `moDrSheet` and `moAbsoluteView` rules can move beside the shared graph reader after their concrete archive dependencies are ported. The ten currently provisional methods include `moLayerMask_c`, `moLayerMgr_c`, `suUIntArray.Serialize`, `su_CMapStringToString` and six external-reference or object-collection methods. The model archive retains its drawing condition and directory ownership checks through [the current Definition grammar](DrawingDefinitionGrammar2026.md).

## Display-list and view-bucket owners

`slddrwu.dll` SHA-256 `61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47` stores a presence long, two UI transforms and a nested `uiDrawingVBData_c` at `uiDrawingDisplayListObject_c::Serialize` `0x3dec30d0`. The nested serializer `0x3dec49c0` reads a counted maps section, unit/exclusion strings, line styles, font manager, layer manager, an integer array, sheet buckets, view buckets and detail state flags. A pinned readback of the initial fields matched the same four style class declarations and reached the layer manager at offset 2997 in all three disclosed controls. REA/Hopper evidence `ev_f73043f9e65ccf0e10a4c30ed5d92824ea71a1efc0322414f85a9edf0a38a684` and `ev_dde2d35519b959d41502e496dd8bcc0e1558e221ef08c208548e60b7f67b1660` locate the native owner and restore helpers. The task-owned Hopper session is closed.

The nested array allocates `uiDrawingSheetBucket_c` and `uiDrawingViewBucket_c`, with respective serializer entries `0x3dec4390` and `0x3dec5680`. Their inline graphics payloads are dispatched through the loaded `uiViewBucket_c` path. The current SDK layout does not interpret that route. `Contents/VBLists` carries a leading bucket count. It is empty in the disclosed sheet and contains a `uiViewBucket_c` declaration at offset 4 plus light, visual-property and tessellation classes in both disclosed part views. The pinned `slduiu.dll` writer confirms the bucket serializer at `0x49f6c0a0`.

The restored UI path reads `shouldHaveDisplayList` at `0x3dec5271` and also considers view-only state, multithreaded loading and document flags. These checks establish load-path conditions for the persisted display data. Required stream membership and acceptable empty cache values remain to be measured with independent one-variable oracles. Use bracketing native controls and separate vendor-saved experimental copies for each omit or reset hypothesis. Require clean resolved open, rebuild and view edits, then verify restored view geometry after fresh reopen and re-save. Cache experiments never qualify generated output. [Source oracle](../v2026/heldout/DrawingSourceLock01.json)
