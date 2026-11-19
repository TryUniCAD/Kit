# Plain drawing note auxiliary render owners in SOLIDWORKS 2026

This source-only checkpoint classifies three actual field differences while preserving the missing-viewport-text failure. `moNoteData_c.f68/n70` is indexed arrowhead storage, `moDisplayNote_c.f658` is a display-text cache, and `moDisplayNote_c.f768` bit 6 is the named `changeBoxStyle` predicate. None of these findings establishes the actual cause of the empty generated viewport or qualifies a writer. Task `DRAWING-NOTES-C10`; owner `/root/flag_ownership`; delivery PR #121; dependencies are the existing exact note grammar and actual detail-item resolver; exit condition is a bounded source rule and independently verifiable numeric supply, with rendering and full source admission still open.

The [numeric source record](DrawingPlainNoteRenderOwnersNative2026.json) binds three original AMD64 SP05.2 build 34.5.2.604 images, 19 complete functions, 13 instruction windows, one static-initializer data cell, 12 imports and three actual vtable cells. The [six-state observation](../measurements/2026/DrawingPlainNoteRenderOwners01.json) pins only previously disclosed original, edited and generated states and the successful metadata replay. Licensed binaries and private disassembly remain external. No vendor bytes or listings, new CAD decode, native invocation, tests, schema change, public flag or writer change is included.

## Indexed arrowhead ownership

The actual `moDisplayNote_c` table is `0x4d22f060`. Its `+0x220` cell selects `0x4b27cbe0`, a complete false-returning leaf, so the ordinary non-dimension branch of `moDisplayItem_c::getArrowHead` applies. The complete getter is `[0x4ba697b0,0x4ba69888)`. It uses `+0x6b0` to resolve the real detail item through `[0x4ba6c100,0x4ba6c1c9)` and the existing component-detail resolver. In that resolved local owner it tail-calls `[0x4ba38220,0x4ba3823a)`: index below zero or at/above signed count `f70` returns `1`; a valid index reads the corresponding 32-bit element through runtime data pointer `f68`.

The exported `setArrowHead(arrowHeadStyles,index)` at `[0x4ba70bb0,0x4ba70c68)` resolves the same item. A nonnegative index calls `[0x4ba402e0,0x4ba402f3)`, which invokes actual `swccu!su_CUIntArray::SetAtGrow` on `detail+0x60`. Index `-1` applies the supplied style across the real attachment count; lower indices do nothing. The existing protected-display predicate remains part of the function. Ordinary note-dialog setup `[0x418ceba0,0x418cf8be)` calls the actual setter at `0x418ceef0` and `0x418cef31` with its supplied style. This is a source-bound producer, not a rule to import a saved style value.

The shared detail serializer `[0x4ba4ad40,0x4ba4b1c8)` writes signed 32-bit count followed by the same ordered 32-bit arrowhead values. Its load allocates through `SetAtGrow(detail+0x60,index,value)`. Only historical context versions below `0x384` or `0x395` remap the documented old values; version 19000 retains them. The separate `f58` is the attachment-point object array. `setAttachPoint` does not establish an arrowhead-array population rule.

All four disclosed native original/edited notes store one style `1`; both prior generated states store an empty array. Each has one actual attachment, and all six select arrowhead `1` for index zero under the proven getter rule. This equality closes the getter-level difference only. It does not prove that any untraced consumer ignores the stored count. It does exclude treating these integers as configuration membership or render-registration IDs.

## Display text cache and actual text

`moDisplayNote_c::getDisplayText` `[0x4c7f9f40,0x4c7f9f54)` copies the actual CString at `f658`; `setDisplayText` `[0x4c80d130,0x4c80d13e)` assigns the supplied CString. The current note serializer stores/loads this distinct cache at `0x4c9541d7` and `0x4c954b33`. The actual text owner still resolves through virtual `+0x458` to the note-data text object and its own `f08` string. The cache and actual owner must both be retained.

`uoNote_w::getDisplayText` `[0x4a06ef50,0x4a0711f2)` invokes the helper `[0x4a078760,0x4a0788c9)` before the cache test. The helper can select actual generic-text processing when the cache is empty. In the ordinary non-cell fallback the getter copies the actual text owner's `f08` at `0x4a06f182–0x4a06f18b`; the later test at `0x4a06f196` checks that actual string's emptiness. An empty `f658` is therefore not, by itself, a direct empty-output rejection in this getter. Table, custom-property, linked and embedded-text branches remain outside this narrow conclusion. `[0x4a072d20,0x4a072f92)` provides a concrete setter path from a supplied display result at `0x4a072d56`, with additional cell-dependent work kept distinct.

The four native original/edited notes' caches equal their actual text. The prior generated initial state has an empty cache; its saved derivative has a cache equal to the actual edited text. These data-only observations do not measure pixels and do not establish a constructor cache default or a general rendering fix.

## Named box-style predicate

Static initializer `[0x4b247060,0x4b24706c)` writes literal `0x40` to BSS mask `0x4db9c0c0`; original pointer cell `0x4cd80900` names that initializer. The BSS location itself has no original file payload and is not read as a saved constant. `changeBoxStyle` `[0x4c7f50d0,0x4c7f512f)` tests that mask against runtime `f768`. `setChangeBoxStyle` `[0x4c80ceb0,0x4c80cece)` ORs or clears only the same mask according to its argument.

The full copy owner `[0x4c7fd840,0x4c7fdf0d)` calls inherited `moDisplayItem_c::iCopy` and preserves the source's named predicate into the destination. This is a copy path, not an initialization or visibility proof. The original discovery basename `NoteInitTextBranch01` is retained privately, but the numeric ledger labels the actual role `NoteCopyFields01`. The earlier overlong setter discovery is also retained; only the corrected complete leaf bound is part of this packet.

The four source states have bit 6 set; the two prior generated states do not. No generic visibility or default-presentation meaning is inferred from this difference. Runtime `f768` is a qword, while its current wire grammar remains a signed chunk count followed by ordered u32 chunks. No new raw saved word is constructed or normalized here.

## Remaining diagnostic boundary

The parent has separately reported that every grid-off same-note variant, including both annotation switches enabled, still matches the empty pristine viewport bitmap. That later matrix is not hash-bound by this packet and receives no new acceptance credit here. The earlier document-switch receipt remains immutable.

The next useful observation is whether the actual note wrapper reaches the live drawing renderer and passes its own eligibility predicate, and what text the live `uoNote_w` getter returns there. Merely observing COM `Visible`, a correct text owner, an arrowhead-array count or `changeBoxStyle` does not establish rendered glyphs. `moGenericText_c.f160` bit 10, glyph layout, camera/zoom, active sheet/detail collection and actual renderer publication remain separate owners. Do not alter constructor flags or substitute a saved string to force a pixel result. The original full-source refusal, held-out custody and public writer gate remain unchanged.
