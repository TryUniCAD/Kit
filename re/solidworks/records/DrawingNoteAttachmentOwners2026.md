# Drawing note attachment owners in SOLIDWORKS 2026

This source-only checkpoint closes the ordinary typed route from a view's displayed note to a type-checked component edge. It does not qualify notes, a new codec, a public drawing writer or generated downstream-cache consumption. The native edge trial has so far failed observer predicates before it created any note. All current saved-note type and alias claims therefore remain unmeasured.

The [numeric record](DrawingNoteAttachmentOwners2026.json) binds original sldmodu.dll SHA-256 569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e, exact runtime descriptors, schema words, serializer table cells, complete unwind owners, bounded leaf accessors and primitive imports. No vendor code, bytes, saved rows or listings are included. Retained private listings were used only to derive field rules.

## Live attachment identity

The view's f630 detail folder owns the f358 notes collection. Native addNote(display) at 4c98c180 passes that actual folder to the common detail-folder insertion routine. The folder getNotes accessor at 4b285b30 returns precisely f358. These owners belong to the inline drawing model in Contents/Definition; the ordinary drawing model's lightweight and resolved contents are not a separate child Config stream. [Definition framing](DrawingDefinitionGrammar2026.md)

A concrete moDisplayNote inherits moDisplayItem and moDisplayObject. Its actual f48 accessor returns a moCompNote. The latter serializes through moCompDetailItem, then adds no fields of its own. The component-detail base keeps the live detail-item reference at fe8, an alternate/fallback reference at ff8 and an i32 at f100. Its normal local branch stores real object tags; the separately guarded external-name branch stores names. Full topology or ownership must not be inferred from the displayed note's f48 alone.

The actual display virtuals +0x358 and +0x360 resolve the detail item through +0x6b0, not directly through f298. The iGetDetailItem implementation verifies the component-detail class and calls getDetailItem. That method can use ff8 in detailing, unloaded/lightweight or unresolved cases and marks its fallback state; for a loaded ordinary live item it uses the validated fe8. A bounded portable projection must preserve this distinction and require an independently resolved real child rather than emulate native filesystem resolution.

The selected detail item's f58 is the actual attachment-point list. Its exported getter and setter operate on that list, and moDetailItem's serializer writes its retained elements as an inline object array. A parametric point's non-dimension predicate is false, so that ordinary concrete class is retained by the store filter. Other attachment classes need their own predicate proof.

## From point to actual child edge

A moParametricPoint derives the abstract moAttachPoint. Its f118 is a typed moRefWrapper pointer, independently bound by the exported getter and store call at 4c273c6b. f108 and f110 are f64 values; the exported setParam binds f108. The base separately serializes its actual drawing-view context f50 plus point and flag fields. Archive conditions 1/2 and the optional view suppression branch alter framing and cannot be guessed from aliases.

The exported getEdge jumps to the complete owner [4b72a650,4b72a936). It checks that f118 is a moCurveRef, then checks that the wrapper's f58 is a real moCompEdge. That class check has its own original runtime-descriptor call. The ordinary branch validates the component reference, obtains its component/configuration transform and calls moCompEdge.getExactEdge. Temporary edge and general resolver fallbacks are separate paths. A successful fallback does not prove the intended exact child topology join.

This gives the bounded identity path: actual view and detail folder → displayed note → component detail item → selected live detail item → f58 attachment → parametric f118 wrapper → typed component edge → actual component/file/configuration and independently resolved complete child topology. Existing [reference wire](DownstreamLinkedReferenceCodec2026.md) and [linked resolver](DownstreamLinkedEdgeResolution2026.md) evidence must remain intact. A display ID, f70 transient cache or enumeration index cannot replace that join.

## Cached data is a separate owner

moDisplayItem's f298 is serialized through the generic optional suObArray helper. In the store preamble it obtains the actual live attachment through +0x358 and invokes that object's +0x218 with the corresponding cached entry. For the parametric-point table, +0x218 selects [4b72fe50,4b72fea5): it reads cached points, view and two parameters into the live point. The direction is cache-to-live at this step; it is not evidence that the cache is regenerated from the live graph there.

The concrete moAttachPointData serializer has point fields f08/f20, drawing-view f38 and f64 f40/f48. That prefix matches the fields consumed by the parametric sync. The exported getNoteAttachData spelling is not sufficient to assign that class—or moNoteData—to every generic array element. Actual saved object tags and aliases are still needed.

moNoteData independently has a moDetailItem base and typed text owner f98. The distinct moNote feature serializes an inline moDimText at f358; its constructor calls the moDimText constructor at that exact address. Treating the feature's inline text as the separate note-data owner would merge distinct records and break the graph. No text, style, visibility or note defaults are imported from a saved document.

## Minimum next evidence

Run the separately frozen, control-first edge annotation protocol. Once a complete pristine control creates, saves and freshly reopens the actual edge-bound note, retain the exact new native derivative. The host-only follow-up should inventory Definition object classes and spans, preserve actual aliases and parse/re-emit the complete reached graph before projecting one note. Corroborate the selected live/fallback item, generic cache type, actual view, wrapper component/file/configuration, actual edge topology and API persistent-reference result. Compare a second independent generated pair and negative owner/cache/type mismatches without using saved values as constructor inputs.

Until those observations exist, preserve unsupported note families and the current drawing guards. This packet introduces no code path, runtime read, note generator or production activation. No vendor process or new Hopper document was opened by this lane.
