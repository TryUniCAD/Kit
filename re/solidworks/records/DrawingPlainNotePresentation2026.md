# SOLIDWORKS 2026 plain note presentation owners

Status: **complete disclosed typed inventory and bounded exact-build source ownership; full original-source conversion, rendered parity and held-out qualification remain unfinished**

Task `DRAWING-NOTES-C10`, owner `/root/flag_ownership`, delivery PR #121. The parent owns integration, native execution and admission. This additive evidence changes no SDK constructor, reader, public capability or frozen writer. It covers the two disclosed plain-note originals, their edited derivatives, and the independently generated initial/native-saved pair. No sealed design, VM, CAD process, test runner or foreign analysis session was accessed.

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), full [reverse-engineering playbook](../../Playbook/README.md), loader and writer-model chapters govern this record. Dependencies are the current typed Definition grammar, the already measured plain-note constructor/name/position rules, and the separate ANSI/default-view rules. The exit condition is faithful source projection and independently measured native/rendered/source comparison; neither a complete parse nor a note-only lifecycle satisfies it.

## Custody and method

The [data-only inventory](DrawingPlainNotePresentation2026.json) binds all six file hashes, every stream name/size/hash, all class counts, all duplicate-free owner rows, map counters/slots, the inspected source paths, and the private full field-graph hashes. It omits captured note text and vendor instructions. The [sanitized receipt](../measurements/2026/DrawingPlainNotePresentation01.json) binds the observation. The complete private source closure covers 3,684 loaded SDK source paths, SHA-256 `ef14c84cc8c1654d0c4da2273642904df033f4dcc6b5c23d8001fd17d6c04812`.

Owner identity is actual `ArchiveNode` or typed dataclass object identity, not an archive index or a matching class/name. Inline embedded formats remain owned field paths. Each actual owner is counted once; every incoming reference and every map alias is retained in the private full graph. IDs are local to each graph and are never joined across files. All six maps have zero objects detached from the root graph. The current inspection performs complete typed reads and field census; it does not execute a writer or establish a new byte round trip. The 23 inspected source hashes match that parse closure. The parent subsequently changed three composition modules for a separate trial; the producer descriptions here refer to the pinned earlier source, not those later live bytes.

| Sample | Definition bytes | Actual owners | Archive nodes | Typed records | Map counter | Streams |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Disclosed01 | 31,197 | 211 | 183 | 28 | 250 | 29 |
| Disclosed01Edit | 31,777 | 219 | 191 | 28 | 258 | 29 |
| Disclosed02 | 31,153 | 210 | 182 | 28 | 249 | 29 |
| Disclosed02Edit | 31,777 | 219 | 191 | 28 | 258 | 29 |
| GeneratedInitial | 27,770 | 126 | 114 | 12 | 176 | 7 |
| GeneratedEditedSaved | 29,248 | 149 | 136 | 13 | 201 | 28 |

All six parse completely with the existing ordinary version-19000 typed grammar. The optional named-front probe rejects all six at its sheet/view family gate; that is an intentionally different family and is not a plain-note semantic verdict. The normal strict blank route independently requires exactly seven generated streams and complete regeneration. The 29-stream source archives do not meet that declared constructor profile.

## Standard and actual effective note format

Two separate owners must survive:

| Owner | Four disclosed original/edited files | Generated initial | Generated native-saved |
| --- | --- | --- | --- |
| Actual model detail `fae0.f10` | `0` | `1` | `1` |
| Definition UI `fba8` class | `moANSI_c` | `moANSI_c` | `moISO_c` |
| Detail constructor state `f138` | `1` | `1` | `1` |
| Root and note font name | Century Gothic | Century Gothic | Century Gothic |
| Actual note format height | `.003175 m` | `.0035 m` | `.0035 m` |
| Actual note format line spacing | `.001 m` | `0` | `0` |
| Note style `f8/f10/f24/f5c` | `0/.00635/1/0` | `1/.00625/0/10` | `1/.00625/0/10` |
| Separate helper format fonts | Segoe UI | Century Gothic | Century Gothic |

All six actual `moGenericText_c` objects have kind `f10=21` and no own format `f18`. The effective format is the annotation-note format `model.fae0.f1f18.f418.f50`, subject to the runtime effective-detail override described below. The helper fonts at `fae0.f4d8.fc8` and `fae0.f4d8.f150.f08` are separate owners; observing Segoe UI there does not prove that the note renders in Segoe UI.

The [numeric native packet](DrawingPlainNotePresentationNative2026.json) binds two exact modules, twelve complete function/leaf spans, six field windows, two data windows, three imported operators and two concrete vtable cells. The independent metadata replay passes. No vendor code/listing is distributed.

- `moDisplayNote::getTextFormat [0x4c7cfd30,0x4c7cfd52)` obtains the actual text through concrete table `0x4d22f060` slot `+0x458`, then delegates to `moDimText::getTextFormat [0x4c854250,0x4c8547d8)`.
- With a valid actual model context, text kind 21 selects table cell `0x4c854790`, target `0x4c8545a0`, returning the pointer at effective detail `+0x2380`. This equals the independently owned `+0x1f18/+0x418/+0x50` field path.
- `moModel::getDetailDefs [0x4c01ffa0,0x4c01ffb4)` returns runtime `+0xae8` when nonnull, otherwise `+0xae0`. The archive census does not prove that the runtime override is absent. A native format observation must resolve that distinction.
- The actual default-document format predicate compares the text selector with display virtual `+0x988`; the concrete target `[0x4b6d8430,0x4b6d8436)` returns 21.
- `moDetailDefs::Serialize [0x3c857a40,0x3c85bb28)` stores detail `f10` through the signed 32-bit archive operator. The current load branch reads signed 32-bit at `0x3c857f83` and installs it at `0x3c857f8d`. Negative selectors alone select standard zero through `0x3c861500`; the measured nonnegative zero remains zero.
- Load helper `[0x3c861540,0x3c861620)` invokes the current standard defaults before later archived format fields are read, preserving/restoring five dimension sizes around that call. The runtime load initialization is distinct from raw wire retention.
- The exported standard getter is the direct `+0x10` leaf at `0x3c757f10`. The setter `[0x3c7dc360,0x3c7dc368)` stores nonnegative input and ignores negative input. Folded unrelated export labels do not replace these receiver-bound identities.

Only the listed fields/windows of the large serializer were newly interpreted here. Other standard modes and runtime format overrides are not admitted by this record.

## Concrete source-to-constructor boundary

`Core/DrawingWriting/MakeBlankWriteRecipe.py` chooses `MakePartStyle()` standard one, precision-four millimetres, and independently chooses a `moANSI_c` UI owner. `MakeBlankBuild → MakeDrawRoot → MakeDrawRefs` sends that style to `MakeDetails` and `MakeStdViews`. Both factories in the pinned inspected source admit standard one only. `InitDrawMut` installs the computed detail dictionary at the actual drawing `fae0`.

`ReadBlankStyle` reads the actual detail selector, root font name, line name, language, print widths, exclusions and labels into `StyleInput`. It does not carry format height, line spacing, separate helper fonts or the complete detail graph. `ReadBlankUi` separately reads the actual UI class. The existing `MakeAnsiDetails` operation is available independently; it constructs standard one and applies the complete native standard-zero defaults, retaining constructor `f138=1`. The pinned ordinary drawing factory does not route through it. That operation alone still cannot preserve the source spacing, independent helper fonts, units and other source settings.

The partial `ReadNoteDrawing` projection resolves actual sheet → detail folder → display → component → note data → generic text ownership and preserves text/position. It is not a full presentation or auxiliary-stream representation. The strict original-source mapper must preserve each additional owner or refuse it explicitly. Replacing only `f10`, replacing only the UI class, or installing the complete source dictionary as a template is not an acceptable solution.

## Ten actual named views

The comparison uses the existing native formulas in [standard-view construction](StandardViewsConstruction2026.md), not fitted matrices. `MakeStdViews(1)` supplies the one/two branch; only index nine changes for the independently computed zero-or-other branch.

All four disclosed files have IDs 0–9 and names `*Full Sheet`, followed by nine `Unused` entries. Both transforms are identity, primary matrix presence is zero, translations and flags are zero, and scale is one. They match **neither** canonical part-view branch. Across all ten primary matrices, maximum coefficient residual is `2.0` for either branch. At index nine the residual is `0.7071067811865487` against zero-or-other and `0.35355339051216605` against one/two.

Generated initial has `*Normal To`, `*Front`, `*Back`, `*Left`, `*Right`, `*Top`, `*Bottom`, `*Isometric`, `*Trimetric`, `*Dimetric`, with exactly zero residual against `MakeStdViews(1)`. Its native-saved derivative uses the drawing names `*Full Sheet/Unused` but retains every one/two matrix unchanged. Both generated states differ from the zero-or-other index-nine branch by `0.35355339067438263`.

Saved names, saved selector and transform agreement do not prove runtime initialization order, effective override state or the constructor that originally ran. Drawing names also do not imply identity transforms. The actual drawing constructor/refresh owner remains a separate source lane.

## Remaining owners and limits

- Sources have forty `uiLFConfig_c`, seven `moLineStyle_c`, and nine log/stamp pairs; generated initial and saved have no line-font configurations/styles and one log/stamp pair. All actual owners, aliases and fields remain in the private inventory.
- Sources have ten separate length-unit objects. The primary millimetre unit uses precision two, format `.1/4/8`, and a separately allocated inch dual. Generated initial has one primary length object, precision four, format `.01/10/1`, with no dual. Native saving adds dual objects without making the primary source settings equal. The independently proven dual constructor does not establish primary-format parity.
- Source text flags are `0x70402`; generated initial uses `0x70001` and its native-saved derivative `0x70002`. Initial glyph metrics are zero and native saving populates them. Actual source line heights are about `.004175`, versus the generated saved `.0045256945`. Widths also depend on the intentionally different text inputs and cannot be treated as defects without matched text.
- The stream inventory is complete, but stream meaning and regenerated-cache behavior are not inferred from presence or size. Source property, UI environment, preview, line-font, biography/history and auxiliary package owners remain explicit. A raw typed Definition is not a complete source-document conversion.
- The original-source task is bounded by enumerable known owners rather than an unknown runtime class, but it is broader than the proven text/name/position graph. Full-source admission remains false.

## Prebound rendering measurement

The existing `re/tooling/sw2026/InspectView.py` records real `SaveBMP(...,960,720)` calls and immutable input/output hashes. Its complete harness is part-specific: it requires a solid body and reorients to isometric. Reuse only the measured capture call inside a drawing-specific observer. Preserve the actual sheet and drawing framing. Successful BMP creation is not visible-note acceptance.

Before an executable drawing measurement, bind the installed 2026 Automation declarations for `INote.GetExtent`, `IAnnotation.Visible`, `GetDisplayData`, `GetTextFormat`, `GetUseDocTextFormat` and `IModelDoc2.SaveBMP`. Use visible documents, an actual sheet-view annotation traversal, independently measured sheet/viewport mapping and bounded redraw readiness. Require finite ordered extent bounds and a genuinely nonempty matched note region in the BMP, with independently calibrated source/control comparison and retained images for review. Text/name/position, visibility enum, display data and pixels are separate outcomes.

The current [2026 visibility enumeration](https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swAnnotationVisibilityState_e.html) defines visible as one and retains distinct hidden/half-hidden states. The [2023 Visible contract](https://help.solidworks.com/2023/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IAnnotation~Visible.html) also explains that the property cannot by itself establish actual screen visibility through hidden layers or suppressed owners. The latter is background documentation, not an independently rebound 2026 interface. Exact 2026 GetExtent/SaveBMP help retrieval returned only a web shell in this investigation; registered method/signature capture remains required. No unsupported `IGetExtent` pointer API is proposed for out-of-process Python.

The immutable comparison must fail when a note enumerates but its image region is empty, or when source and candidate presentation differs. No new source acceptance, rendered parity or held-out result is claimed here.
