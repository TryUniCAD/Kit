# Native correspondence between drawing and part edges

Task `B04-SW2026-DRAWINGS`, owner `assembly_occurrence`, delivery PR #121. This independently bounded observer retry follows the [part-edge body predicate](DrawingPartEdgeBodyOwnership2026.md). It preserves that failed native packet and every earlier observer failure. No drawing/part input, writer byte or semantic source intent changes. Root owns the native oracle and integration.

## Preserved cross-context failure

The preceding trial SHA-256 remains `47457fa53cf507373ab5a8a083897e89c486f11ae29b8eefbf164cbf8323c4bf`; terminal result SHA-256 is `848a20948ae30baa8a092a3ad9ec3caadf27082896f4a7d75b680c0483be7ed6`. Its verdict is false, with two distinct original-control processes, unchanged inputs and no generated phase.

Both original drawings opened/rebuilt cleanly and retained the exact projected model, path/hash, configuration, camera-facing cap and unique edge checks. The four self/repeat comparisons were one: part body self, repeated part-body retrieval, drawing edge body self and drawing edge self. The raw drawing-edge body versus the underlying part body was zero in both controls. The observer stopped at that assertion, before body-edge enumeration or annotation creation. The before/after raw record hashes are `5c53cee3eb78d83342de26abb00dec4af7ce8d906e5f2e1caf7c2e58c94f8f2f` and `97c27087f91aae356f737dff13bdc511617466a948b51f69882047f3704b9c64`.

These are partial healthy geometry observations and failed full controls. They refute a direct cross-domain body-identity assumption. They do not establish a geometry defect or allow coordinates to replace native ownership.

## Current 2026 API contract

The official 2026 pages contain populated `helpContentData.helpText` in their page data even when the rendered search-tool preview shows only navigation. This lane retained the original responses privately, verified the 2026 page titles and separately hashed their help text. No vendor example/listing is included in the stageable source.

| Operation                                    | Direction and role                                                                                  | Official 2026 source                                                                                                                                                                  |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IView.GetCorrespondingEntity`               | Part/assembly entity to this drawing view entity                                                    | [Entity mapping](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IView~GetCorrespondingEntity.html)                  |
| `IModelDocExtension.GetCorrespondingEntity2` | Drawing/assembly entity to the underlying part/subassembly entity                                   | [Underlying entity](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDocExtension~GetCorrespondingEntity2.html) |
| `IView.GetCorresponding`                     | General part/assembly object to this view, including persistent objects beyond topological entities | [General mapping](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IView~GetCorresponding.html)                       |

The official [2026 example](https://help.solidworks.com/2026/english/api/sldworksapi/Get_Corresponding_Entities_Between_Parts_and_Views_Example_VBNET.htm) invokes the reverse entity operation on the **actual part's extension**. It uses the view object for the forward entity operation. `IView.GetCorresponding` is a forward general-object API, not the reverse edge operation.

The exact zero-CAD installed metadata capture SHA-256 is `3c02263dc1d85eb15c1446537b4aa8376cdddde715544f7cf6ef662c3ac79b81`; capture tool SHA-256 is `4cfde281387575e4cfefb825a4a391f589a6944e11984d584427159ab8254afa`. Both interfaces report no missing methods, library `34.0`, the same pinned wrapper, and zero CAD objects/documents/processes. Each method takes one input dispatch and returns dispatch.

| Owner and member                             | DISPID | Vtable byte offset |
| -------------------------------------------- | -----: | -----------------: |
| `IView.GetCorresponding`                     |    445 |               3816 |
| `IView.GetCorrespondingEntity`               |    446 |               3824 |
| `IModelDocExtension.GetCorresponding2`       |    303 |               2600 |
| `IModelDocExtension.GetCorrespondingEntity2` |    304 |               2608 |

## New predicate, same annotation domain

The added [correspondence helper](../../tooling/sw2026/drawing_edges/DrawingEdgeCorrespondence01.py) uses the actual referenced child and actual model view already admitted by the unchanged path/configuration/cap guards. It requires a non-null reverse edge, repeated reverse mapping, non-null forward edge and reverse round trip. Analytic endpoints must remain exact. Self/repeat identities and the forward-versus-original drawing edge and round-trip-versus-part edge must each report supported same-object code one within their own domain.

The existing body proof then calls `GetBody` on that **mapped part edge**, requires it to equal the actual underlying part's sole live body, and requires exactly one matching edge in that body's twelve-edge inventory. Its original four self/repeat controls remain mandatory. The raw drawing-body/part-body code remains recorded, accepts only supported equality codes, and no longer claims same-domain owner identity.

The selected entity returned for annotation creation stays the original drawing-view edge. Existing view selection, attachment object identity, non-dangling checks, persistent-reference owner, edit/rebuild, save and fresh-reopen predicates remain exact. No model edge is substituted into a drawing annotation. Missing correspondence, unsupported identity, foreign bodies, ambiguous membership or endpoint mismatch still refuses the control; there is no geometry-only or general-object fallback.

## Reproduction and evidence boundary

[CaptureDrawingCorrespondenceApi01.py](../../tooling/sw2026/drawing_edges/CaptureDrawingCorrespondenceApi01.py) performs only the installed type-library query. [FreezeDrawingCorrespondenceRetry01.py](../../tooling/sw2026/drawing_edges/FreezeDrawingCorrespondenceRetry01.py) requires the exact failed predecessor plus new metadata and creates an unused private successor.

```sh
python -B re/tooling/sw2026/drawing_edges/FreezeDrawingCorrespondenceRetry01.py --source-packet /frozen/BodyOwnerPacket --correspondence-metadata /declared/CorrespondenceApi.json --output /unused/CorrespondencePacket --guest-root '\\Mac\Home\Documents\Research\CorrespondencePacket' --guest-python 'C:\verified\python.exe'
python -B /unused/CorrespondencePacket/Tools/InspectDrawingEdgeQualification01.py verify /unused/CorrespondencePacket/Trial.json --sha256 TRIAL_SHA256
```

Frozen successor trial SHA-256 is `bf759fd068dcc988f34c7f81c46d262bc822682788dfc8abc102cfbbe31cb302`; recipe SHA-256 is `2f227ea2ede145da93e9e28539abdf7c566b40ce58bf5782dd2e3b812ec16a17`. Root alone executes the unchanged six-process control-before/generated/control-after lifecycle. An initial control failure keeps the generated lane closed and still schedules the trailing control.

Two fresh host verifies passed. Independently changed correspondence metadata, tool and wrong-cap inputs were refused before native progress. Both case dictionaries and thirteen unaffected packet files are byte-identical. Existing function changes are limited to the owner proof/call and observer metadata/profile admission. Six owned Python files pass syntax/AST and comment/docstring checks. The current lane made zero native calls, hidden reads or shared checkout writes and opened no disassembler session.

Both native controls in the first correspondence retry establish the drawing-to-part edge round trip and exact membership in the actual underlying body. The remaining position assertion fails at Z and blocks the generated lane in that retry. [Controlled correspondence receipt](../measurements/2026/DrawingEdgeCorrespondenceNative01.json)

The subsequent depth-aware method completes the correspondence and attachment lifecycle for both controls and one generated linked pair. Cache consumption and writer qualification remain open. [Independent depth comparison](DrawingAttachedNoteDepth2026.md#native-lifecycle)
