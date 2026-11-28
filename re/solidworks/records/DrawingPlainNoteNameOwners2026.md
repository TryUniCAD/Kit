# Plain drawing note name ownership, SOLIDWORKS 2026

Task: `B04-SW2026-DRAWING-PLAIN-NOTE-CONSTRUCTION`; owner: `flag_ownership`; delivery: PR #121. This is a source-only checkpoint. It changes no SDK behavior and establishes no generated-note, native lifecycle, held-out or public admission. The exact original-PE identities, complete function extents, import aliases and table cells are in the [numeric ledger](DrawingPlainNoteNameOwners2026.json).

## Registered entry points and actual owners

The independently hashed registered type metadata binds `IAnnotation.GetName` to no arguments, `VT_BSTR`, DISPID 21 and byte slot `0xd8`. In pinned `sldapiu.dll`, table `0x4321b5d8` selects `0x42aad990`; its core is `0x42ab7770`. This core special-cases modeled display dimensions. The ordinary note takes the other branch and invokes its actual display virtual `+0xf8`.

The constructor-bound `moDisplayNote_c` table `0x4d22f060` selects `moDisplayItem::name` at `0x4ba6e120`. It resolves the actual local detail data through virtual `+0x6b0` and asks that data for virtual `+0x88`. The actual `moNoteData_c` table `0x4d22e360` binds `+0x88` to `moNode::name` at `0x4c03e5c0`. This accessor returns the CString at actual `f18+0x08`, or a shared empty CString if the holder is null.

Registered `INote.GetName` has DISPID 44 and byte slot `0x190`; actual table `0x43278648` selects `0x42d82600`. This dispatch obtains its actual display through the API wrapper and invokes the same `+0xf8`. Intermediate API wrapper construction is not generalized here.

## Distinct persisted and allocated fields

| Owner | Role proved by current code |
| --- | --- |
| `moNoteData_c.f18.f08` | Callable note name returned by the registered consumers |
| `moNoteData_c.f20` | Separate CString written/read by `moNode::Serialize`; it is not automatically an alias for the callable name |
| `moNoteData_c.f08` | Node identity domain, distinct from naming and display allocation |
| `moDisplayNote_c.f58` | Display-object identifier; actual insertion/getter uses the model's `fd44` counter |
| Actual model `f90` | Concept name-manager object; owns basename counters and actual-graph miss lookup |

The complete current `moNode::Serialize` at `[0x4c179cf0,0x4c17a322)` contains the separate tagged `f18` owner and CString `f20` store/load operations. No values were taken from a saved note. Earlier quick wording that called the `f20` CString the callable name is superseded by this accessor/serializer distinction; prior frozen records remain immutable.

## Ordinary commit allocation

The already pinned detail-folder insertion sets the actual display owner and calls display `+0x108`. This delegates to actual detail data `+0x508`, bound to `moDetailItem::autoName` at `[0x4ba2e5e0,0x4ba2e712)`. It renames only when the current callable name is empty, the actual data owner exists and is a detail folder, and that folder resolves an actual model. Existing names are preserved.

The basename comes from data virtual `+0x530`, whose actual implementation loads resource ID `0x2d2c`. Its carrier, localized text and locale are not established by this checkpoint. The native algorithm calls `assignNextAutoNameId(base,0)` on actual model `f90`, formats the returned integer using the native `%d` vocabulary, appends it to the basename, and invokes `0x4b555250` with the actual resulting string. That helper allocates or updates the `f18` holder and its CString. It does not write `f20`.

The actual name manager first looks up the basename counter. On a miss it invokes its concrete virtual-zero implementation, which constructs a real-owner feature walker with result initialized to zero. Its callback asks actual nodes to compare their names and update the maximum suffix. Therefore an initially empty map does not justify a zero result if the owner graph already has names. Recursive traversal completeness, suffix parser edge domains and unusual numeric names remain open. No English prefix or universal first suffix is supplied as a saved default.

## Verification and retained limits

Independent static metadata replay verified three exact modules, 29 complete functions, six instruction ranges, one data range, ten imports and 13 actual table cells. A separate LLVM decode verified every selected range endpoint. The first selected constructor window ended inside the next instruction; its false boundary result is retained. The corrected range covers only the real table address-load and store, with all 29 whole-function hashes unchanged.

The stageable [receipt](../measurements/2026/DrawingPlainNoteNameSource01.json) records zero CAD/VM calls, zero SDK/schema/codec execution and no tests, saved CAD payloads or sealed inputs. This explains which modeled owner controls a callable name. It does not qualify first-open note rendering, text placement, the ordinary `GenericText.f170` producer, localized naming, or a public writer.
