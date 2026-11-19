# Drawing document display flags in SOLIDWORKS 2026

Status: **three exact owner rules bound; note raster eligibility and full source acceptance remain open**

PR #121 task `DRAWING-NOTES-C10`, owner `/root/flag_ownership`. Root owns native execution, product changes and publication. This source-only tranche changes no SDK code or writer. It depends on the prior [note owner inventory](DrawingPlainNotePresentation2026.md), typed Definition/header fields and the root's disclosed registered API/diagnostic capture. The exit remains faithful source conversion with independent native, rendering and held-out evidence.

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), full [playbook](../../Playbook/README.md) and loader/writer chapters apply. No hidden source, VM, CAD process, shared source or foreign analysis session was touched. No local tests were run.

The [numeric source packet](DrawingDocumentDisplayFlagsNative2026.json) binds five exact 2026 modules, twenty-five complete native function/leaf extents, fifteen field windows, thirteen data windows, eighteen imports and five concrete vtable cells. Its independent data-only PE replay passes. Original code/listings remain outside the checkout. The [sanitized observation](../measurements/2026/DrawingDocumentDisplayFlags01.json) keeps the host and native cohorts separate.

## Three independent settings

| Registered public selector | Actual native query | Actual wire owner | Authored operation |
| --- | --- | --- | --- |
| `swDisplayAnnotations=31` | document `getDetailMask(0)` | `fad8_0`, bit 0 | Set/clear mask `0x00000001`, preserve other bits |
| `swDisplayAllAnnotations=197` | document `getDetailMask(29)` | `fad8_0`, bit 29 | Set/clear mask `0x20000000`, preserve other bits |
| `swGridDisplay=57` | document `getDisplayGrid()` | `fad4`, bit 0 | Set/clear mask `0x01`, preserve other bits |

These are document settings. `IAnnotation.Visible` is a separate per-annotation state. None of these values alone proves that the renderer drew note pixels. The bit indices are native field knowledge; they are not copied saved flag words. An internal constructor experiment can express three independently chosen neutral booleans without reusing any complete source word.

The existing `ModelDefSettings.FlagIndices` can already express the two detail-mask indices independently. The grid flag is a separate owner and is not in that 64-bit preference list. The pinned `MakeDefHead` hardcodes `fad4=3`; that includes grid bit zero. This record does not silently change that constructor policy.

## Exact API and source route

Root's installed major-34 API capture is `PlainNoteAnsiPresentation01/GridApi01.json`, SHA-256 `cd722497b42b3def5cc057b264220bca207e4de28972e12b6d77a3453aa9341f`. `IModelDocExtension.GetUserPreferenceToggle` has two signed integer inputs, a Boolean result, DISPID 158 and byte slot 1336 (`0x538`). It also records `IAnnotation.Visible` and the Automation `INote.GetExtent`; these are distinct interfaces.

Public wrapper `[0x456a9790,0x456a98a0)` delegates its actual contained interface's slot `+0x538`. The concrete `XDispatch@auModelDocExt_c` table is `0x4326cc78`; its `+0x538` cell `0x4326d1b0` selects `[0x42d21020,0x42d211a8)`. The primary C++ `auModelDocExt_c` table is not this registered COM table and cannot be indexed with the registered interface offset.

The dispatch checks an options-provider before its legacy fallback. For ordinary type-zero compiled initialization, `[0x42f5e2a0,0x42f5e650)` registers only selectors 425 through 435. The first provider factory `[0x42f60540,0x42f60548)` merely returns its compiled provider pointer. Thus selectors 31, 57 and 197 use the fallback in this ordinary registry. A nonnull replacement provider has a distinct actual `+0x88` call and is not ignored or declared equivalent here. Arbitrary foreign registrations remain outside this bounded rule.

Fallback call `0x42d2114c`, through `sldapiu` IAT `0x430361b0`, reaches `auModelDoc::iGetUserPreferenceToggle [0x492937d0,0x49296e2a)`. Its compressed selector tables give:

| Selector | Compression cell / index | Target-RVA cell | Actual branch |
| --- | --- | --- | --- |
| 31 | `0x49296768`, 7 | `0x4929669c` | `0x49293c3c`: actual document slot `+0x11c8`, argument 0 |
| 57 | `0x49296782`, 33 | `0x49296704` | `0x49293eab`: actual document slot `+0x12f0` |
| 197 | `0x492968e5`, 7 | `0x49296804` | `0x49294a09` → `[0x4993b060,0x4993b06f)`: slot `+0x11c8`, argument 29 |

Concrete drawing table `0x3e1d6b78` binds `+0x11c8` through thunk `0x3e0b100e` and IAT `0x3e13bdc0` to `uiModelDoc::getDetailMask [0x497872a0,0x497872ae)`. That leaf passes the actual pointer at document `+0xad8` to `utBitSet::isBitSet [0x3cfcdb40,0x3cfcdb85)`. The latter computes word index `bit//32` and mask `1<<(bit&31)`. Both requested bits are therefore in low word zero. The runtime pointer itself is not the serialized flag value.

## Archive and save behavior

`uiModelDoc::Serialize [0x497011e0,0x49704a43)` copies the current `+0xad8` bitset, writes data index zero through the signed 32-bit operator at `0x49701609`, then data index one at `0x49701626`. Current load installs those words with `utBitSet::setData(0,word)` at `0x49702356` and `(1,word)` at `0x497023f7`. The SDK names the preserved bit patterns `fad8_0` and `fad8_1`.

The save path can merge a secondary runtime bitset, so a raw whole-word preservation claim would be too broad. Its common compiled mask indices are `17,42,20,18,21,32,19,15,28,24,46,56`. Neither requested annotation bit is in this mask. Additional indices `29,10,2,34` are added only for a non-drawing document. The actual drawing table's `+0x1260` selects `[0x3dd588c0,0x3dd588c6)`, which returns one, skipping that addition. The selected drawing save merge therefore preserves bits zero and 29 from the current document bitset. Part/assembly overlay behavior is not generalized from this rule.

For grid, the same serializer reads actual document `+0xad4` low byte at `0x4970147e` and writes it through the byte operator at `0x49701488`. Load reads a byte at `0x497022f5`, zero-extends and installs a runtime dword at `0x49702300`. Getter `[0x497872b0,0x497872d1)` first invokes actual sketch slot `+0xfb8`, then returns `ad4&1`. Setter `[0x497b9280,0x497b929f)` changes only that bit. The other bits are preserved and are not renamed here.

The drawing's `+0x12f0` resolves through thunk `0x3e0b0a14`, IAT `0x3e13b5c8`, to that getter. Grid worker `[0x4989c5b0,0x4989cfc7)` checks the actual slot at `0x4989ce51`; zero skips the `renderGridLines` call at `0x4989cf06`. Its preceding valid-sketch, profile, unit, spacing and view gates remain part of the route. This source rule explains a grid-enabled state, not the absence of note pixels.

## Disclosed comparisons and pending boundary

The four prior disclosed original/edited graph inventories all have grid off and both annotation bits set. The earlier generated initial and native-saved graph inventories have grid on and both annotation bits clear. All untouched bits remain recorded independently; no complete source mask is proposed as a generator default.

The root's separate four-process live diagnostic, SHA-256 `5b69c1d0363161cb0ec7798ba265e1379ff82db9eb0a6a60e7080c180018309a`, measures both annotation switches true/grid false in the source and two healthy pristine controls. Its separate ANSI generated candidate reports both annotation switches false/grid true, unchanged through rebuild. This diagnostic's candidate is not identified with the earlier ISO candidate merely because those three states agree. The receipt retains the separate job identity and both cohorts' custody.

The diagnostic collects these states; it does not qualify the candidate's raster. A matched authored-switch matrix must keep controls healthy, preserve exact notes/tree/position and compare actual pixel content. Even a correct switch readback can leave a display-eligibility, wrapper registration, sheet lookup or layout-cache defect. Those are distinct remaining source and measurement boundaries. Complete original conversion, public writer admission and held-out qualification remain false.
