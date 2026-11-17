# SDK drawing sheet own-field serialization

The SDK now emits the ordinary `moDrSheet` own-field body through its shared typed executor. This is an internal codec boundary. It does not construct an entire drawing, enable a public writer or establish new native acceptance.

Task `pr121-sdk-drawing-sheet-fields` is owned by `configuration_header` in PR #121. Root owns the vendor oracle and broader writer integration. Dependencies are the disclosed 2026 Definition grammar, independently authored drawing requests and existing SDK object/map/scalar codecs. The bounded exit is exact generated stream parity, public readback, preserved aliases, zero runtime input access and explicit unsupported-mode rejection. Broader B04-SW2026/B07 and CAD acceptance remain unfinished; no readiness register changes are implied.

## Exact dependency gap

The research `builders.DrawingDocument._definitions` still constructs and stores the complete `uiDrawingDoc_c` graph through its research registry. The public SDK `Drawing.Definition.ReadConcept` uses a separate immutable read grammar, skips the five-long UI prefix and CLSID, and stops after the resolved concept before the remaining Definition tail. It has no complete SDK drawing stream writer or semantic graph factory.

The research `Core.Obj` already subclasses SDK `ArchiveNode`. Object identity, concrete descriptors and archive maps are therefore shared. The missing first boundary was a drawing-specific `NativeField` layout that the existing `BodyWriter` could consume. The three new modules under `Drawing/Definition/Writing` supply the entire sheet own-field method after its inherited `moModelFeature_c` body. They do not repeat the inherited fields or change the public reader grammar.

## Source authority

All native addresses refer to original SOLIDWORKS 2026 SP05.2 `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`.

The runtime class descriptor is `0x4d2774b8`; its serializer is `[0x4c957120,0x4c958c70)`, code SHA-256 `e7721710576d43653b4839815644edef489fc33f974b6571ec1170af7bde0b60`. Its current-version inherited call at `0x4c95728b` targets `moModelFeature_c::Serialize` at `0x4bb19290`. The own store branch begins at `0x4c9572a4`; it writes `f3f8`, `f400`, `f39c`, `f3c0`, `f3e8`, `f3f0` in that order. These facts agree with the recovered [Definition grammar](DrawingDefinitionGrammar2026.md), [sheet construction](DrawingEmptySheetConstruction2026.md) and the existing SDK `ConceptShapes["moDrSheet"]` read rules.

The ink-list store computes `(end - begin) >> 3` at `0x4c958a93–0x4c958aa1`, writes the count at `0x4c958aa8`, then serializes pointer elements at `0x4c958ac6` and advances by eight at `0x4c958acb`. The SDK derives that count from actual rows. The new ordinary profile rejects nonempty ink rows because their feature construction and full element semantics are not qualified here.

No vendor binary, instruction bytes or proprietary listing is added to the checkout. This step reused the retained REA-backed grammar and a bounded direct LLVM check of the pinned original image. No Hopper target or CAD process was opened.

## Owned fields and value provenance

The schema declares field names, widths and order. It contains no captured field values, stream offsets, document lengths, saved rows or byte programs. Values come from the supplied typed node, whose construction remains separately owned.

| Own-field group | Value ownership |
| --- | --- |
| `f3f8/f400` | Authored sheet scale numerator and denominator |
| `f39c/f3c0/f3e8/f3f0` | Paper/format vocabulary and dimensions computed by the caller's sheet model |
| Three presence flags and `f408/f468/f418` | Explicit graph presence and actual referenced objects; missing flags are rejected |
| `f3b0/f420/f428`, `f448/f3d8/f474` | Completed caller graph's typed sheet state; no new default is supplied by the codec |
| `f3b8/f3d0` | Authored format/property-view text encoded by the shared CString codec |
| `f3c8/f438/f390` | Actual caller-owned format, collection and detail-folder references |
| `has_f430/f430` | Explicit optional transform and existing typed geometry grammar |
| `has_f450/f368_marker` | Qualified ordinary branch requires zero and `0xffff`; other states reject before output |
| `f4a8/f4b0/f4b8/f4c0`, `f4c8/f4cc` | Zone margins/counts derived by the caller from paper and units |
| `f4d0/f4d4/f4d8/f4e0` | Typed zone/state fields from the completed caller graph |
| `f4f0` | Typed caller time value using the current unsigned 32-bit archive rule |
| `n_ink_views/ink_views` | Count derived from the actual ordered rows; only the empty ordinary branch is admitted |

The serializer requires archive version 19000, concrete `moDrSheet` schema one and the ordinary zero-condition context. Older releases, alternate schemas, filtered contexts, unknown annotation branches, nonempty ink lists and absent native presence flags fail closed. The caller must provide the inherited archive map and a valid typed object writer. The inherited profile and detail-folder aliases remain references to their actual graph nodes; the new `suObList` receives the next computed map slot.

## Component and process proof

The [sanitized receipt](../measurements/2026/SdkDrawingSheetWrite01.json) records four independent requests, each run in two fresh isolated interpreters: two blank sheets and two Front views linked to separately generated 22.7×15.9×5.3 mm and 31.4×9.8×8.6 mm rectangular children. No saved CAD specimen, original locked input or trial output was opened. Each process independently constructs both a research-serialized graph and an SDK-sheet-serialized graph, requires complete logical-stream equality, builds the container and reads it through the public drawing API.

All eight successful processes passed, with sixteen independent graph constructions and zero runtime input-file access attempts. The public reader confirmed paper dimensions, authored scales/text, child configuration/view placement and live profile/detail-folder aliases. The entire generated drawing stream set and linked part stream set are unchanged. Sheet own bodies vary from 190/192 to 796 bytes when independently authored Unicode text changes; there is no fixed-length payload.

The Front bundle legitimately emits its sheet twice: once for the initial blank graph and again after adding the view. The process receipt retains both SDK calls. It does not miscount preliminary construction as another delivered output. The ordinary blank continues its map from 98 to 99 while emitting the new empty list; references to already serialized children retain identity.

Seven additional complete-process requests reject an older archive version, nonzero context, alternate schema, annotation presence, nonempty annotation state, nonempty ink list and missing profile-presence flag. Rejection occurs before this SDK body appends bytes or grows the map and returns no successful container output. These are real component/process checks, not tests of isolated helpers.

Ten new SDK/integration Python files pass targeted steering and Black checks. The donor scan reports no recorded payloads in 3,456 `src` files. No local unit tests or native oracle ran. Source and input hashes are recorded in the receipt; root retains commit, CI and vendor-run ownership.

Targeted Mypy reports no issues; Pyright reports zero code diagnostics but identifies three preexisting unrecognized project settings in the local tool configuration. Those messages are retained separately in the receipt. `BodyUsage.completed` remains false at this internal body boundary because the caller, rather than this helper, owns completion of the enclosing stream.

## Remaining construction boundary

The full SDK drawing writer still needs semantic root/support construction, complete model light/resolved state, inline header handoff, UI prefix and suffix, metadata/index ownership and a closed stream/container composition entry point. Those components must reuse the already proved rules and pass their own held-out native acceptance. This codec does not imply that decoded layout data alone can reconstruct an entire editable drawing.

See the [SDK usage guide](../../../Documentation/Reference/Research/Solidworks/DrawingSheetWriting.md), [change entry](../../../Documentation/Changes/Solidworks/Inspection/Drawings/Linked/SolidworksDrawingSheetFieldWriter.md) and [presence/map gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingSheetFieldsNeedTheirArchiveContext.md).
