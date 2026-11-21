# Fresh note text and metric ownership in SOLIDWORKS 2026

This source-only checkpoint distinguishes note text construction, last-newline handling, and glyph layout. It adds no writer and does not qualify zero metrics as valid saved note data. The [numeric record](DrawingNoteFreshText2026.json) pins 36 complete original functions, 19 instruction windows, one small format-vocabulary range, 20 imports and six concrete virtual cells across the licensed 34.5.2.0604 AMD64 model, utility and UI images. The existing five-file [raw note retention result](DrawingNoteTextDependencies2026.md) remains independent. Normal drawing semantic admission stays closed.

Task: B04-SW2026-DRAWING-NOTE-GRAMMAR. Owner: PR121 flag_ownership. Delivery: PR #121. Dependencies: the complete typed note reader, actual note-data/text ownership, the generated drawing graph and a root-owned native oracle. Exit: a full generated note must render on first open, retain actual text/format/attachment semantics, and survive save and fresh reopen with healthy controls and independent typed readback. That exit has not been measured here.

## The load flag is a last-newline rule

The exact exported `moGenericText_c::isUseLastNewLine` leaf at `[0x4b35de20,0x4b35de2c)` returns `(f160 >> 1) & 1`. The current loader consumes the saved `f160` word and then sets mask `0x2` at `0x4bed920e`. Its actual owner is last-newline handling. It is not the glyph-layout dirty predicate.

The distinct mask `0x1` is owned by `setBoxNeedsUpdated` at `[0x4bef0950,0x4bef097e)`. True sets that mask and invalidates token caches; false clears only that mask. The concrete generic text virtual `+0xd8` targets `[0x4bee98b0,0x4bee98c8)`, which also sets mask `0x1`. Setting a real text format reaches this virtual after copying the input format. No whole flag word from a save is needed to establish either rule.

Both `getBoxInfo` at `[0x4bee35b0,0x4bee3629)` and `updateBoxInfo` at `[0x4bef57e0,0x4bef583f)` recompute when mask `0x1` or the process override is nonzero. Otherwise they refresh the head table without recomputing the glyph metrics. After the recomputation call they clear mask `0x1`. A raw saved word whose only relevant bit is `0x2` therefore does not itself prove that glyph layout will run.

## Fresh constructor state has its own owner

The actual `moGenericText_c` constructor `[0x4bed3d30,0x4bed3ed3)` first calls the complete `moDimText_c` constructor. A nonnull explicitly supplied `utCharFormat_c` gives `f10=1` and a fresh copy at `f18`; the null argument leaves `f10=0` and `f18=null`. Those null states do not identify the effective document note style. The normal UI resolves the actual model's effective format through `moDimText_c::getTextFormat`.

Generic text initializes `f160=1`, creates a fresh paragraph and parses the supplied string through `0x4beec180` into an actual `moGenTextDataList_c`. Parsing calls `setString` and marks the box dirty. The complete constructors later enable the [separate border default](DrawingPlainNoteTextBorder2026.md). These constructor operations do not establish a general saved flag word or a complete neutral rich-text grammar.

The shared spaceholder constructor casts three input doubles to the `f32` triple at `f20/f24/f28`, initializes `f2c=0`, sets `f30=1`, and clears `f34/f38`. The character deserialization factory supplies zero for the triple and initializes an empty unsigned UTF-16 unit. The actual character object also has an unsaved runtime CString holder at `f48`. Constructor zeros are distinct from glyph metrics populated after layout. A discovery candidate must still build real text tokens and ownership; the empty deserialization object does not represent arbitrary nonempty text.

The new paragraph is independently constructed from alignment, two spacings and the bullet/number kind. For the generic constructor's supplied zero arguments, the complete source gives `f18=.01`, `f58=f60=.001`, numeric marker format `$$.`, `f6c=-1`, and the remaining documented scalar zero states. These values come from the exact constructor and its marker vocabulary, not from a saved note. Other paragraph modes and later native edits stay separate.

## Actual note rendering reaches the box gate

The complete exported `uiDocDrawMan_c::idrawOrProcessNote` owner is `[0x49c2f560,0x49c3813a)`. It obtains the actual note text using display virtual `+0x458` at `0x49c2f6e3`. The actual note cell targets `0x4c7f9e10`; the generic text predicate is its concrete `+0x88` virtual. On the generic branch, calls at `0x49c3232b` and `0x49c32361` enter the 65-byte bridge at `0x49588cf0`, then the complete 66-byte tail dispatcher at `0x49588510`. The dispatcher reaches `uiModelView_c::drawGenText` when its mode argument is nonzero or actual display-item data is present. It returns otherwise.

`drawGenText` is the complete `[0x49578ee0,0x4957a130)` function. It applies text, view-scale and display-data guards, resolves the effective format, and calls `uiDocDrawMan_c::getGenTextBoxInfo` at `0x495794fc`. The latter complete 166-byte function supplies the actual model format and device context to `moGenericText_c::getBoxInfo` through the independently named import at `0x495883a7`. The common render call follows at `0x49579c85`.

This is a note-specific static call chain before rendering. It does not observe which branch ran during a fresh native open. Loaded display-list shortcuts, unavailable device contexts, alternate note content and hidden or suppressed notes must not inherit an unconditional regeneration claim.

## Populated metrics are derived font output

The selected metric path proceeds through `0x4bef5610`, `0x4beecc70`, the actual character virtual `+0x148`, and `[0x4bef62b0,0x4bef6516)`. The character worker fetches metrics through `[0x4bedc120,0x4bedc43f)`, scales and adjusts them from the effective format, writes `f20/f24/f28` and `f2c`, then clears `f30`.

Independent native accessors identify the embedded triple as height, width and base height. Descent is the `f32` subtraction of height minus base height, widened on return. Current wire representation is three `f32` values.

The font setup helper calls `ut_SetFont` with its native `720` setting. It reads outline metrics and falls back to `GetTextMetricsW`. Width calculation uses `GetTextExtentPoint32W` or the actual glyph fallback path, with an optional ABC-width adjustment. Font availability, language, shaping state, character spacing, fit modes and the effective character format participate. This packet does not replace them with a captured width table or claim an equivalent portable font engine.

## Controlled next observation

Use independently authored plain text and an explicit complete format, with no property links, symbols, table, stacked text or unexplained token type. Build the complete note graph before serialization. Preserve the constructor-derived dirty mask and actual ordinary token dirty state. Do not patch saved bytes, drop text, or infer mask `0x1` from the last-newline load fixup.

Measure the exact displayed text, actual text-format owner, inherited text position and separate absolute attachment point before rebuild. Require visible nonempty rendering bounds, clean diagnostics, save, and a fresh-process reopen. Complete typed readback must preserve Definition bytes/maps/aliases and report the actual resulting flags, line metrics and per-glyph metrics separately from the authored inputs. The root owns this experiment and its controls. All native, portable-metric, C10 and public-writer claims remain pending.

## Verification and custody

The [static verification receipt](../measurements/2026/DrawingNoteFreshTextSource01.json) replays only original PE hashes, complete exception-table owners, selected instruction/data spans, imports and virtual cells. It executes no SDK, schema, codec, test or vendor routine. REA reported no active target with retained cleanup pending; this lane opened no target and changed no foreign session. Vendor binaries and listings remain external. No disclosed archive or sealed payload was read for these constructor rules. The earlier 28-path raw-reader delivery remains immutable.
