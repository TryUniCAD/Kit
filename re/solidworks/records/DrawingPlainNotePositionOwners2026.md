# Plain drawing note position owners, SOLIDWORKS 2026

Task: `B04-SW2026-DRAWING-PLAIN-NOTE-CONSTRUCTION`; owner: `flag_ownership`; delivery: PR #121. This is a bounded source checkpoint with independently hashed disclosed data-only observations. It does not qualify a generated note or a public drawing writer. Exact original binary identities, complete functions, transfer spans, import names and actual vtable aliases are in the [numeric ledger](DrawingPlainNotePositionOwners2026.json).

## Actual registered getters

Installed registered type metadata binds `IAnnotation.GetPosition` to DISPID 8, byte slot `0x70`, no arguments and a Variant result. Actual `auAnnotation_c::XDispatch` table `0x4321b5d8` selects `[0x42aaef80,0x42aaf1a4)`, which invokes core `[0x42abaaf0,0x42abad35)`. The core resolves the actual modeled display, tests the real `moDisplayDim_c` class, and takes a distinct branch for notes.

The note branch invokes actual display `+0x3b0`, bound by the constructor's `moDisplayNote_c` table `0x4d22f060` to `[0x4be6d3f0,0x4be6d447)`. This method invokes the note's actual `+0x4c0`, bound to `[0x4c7fb480,0x4c7fb644)`. Registered `INote.GetTextPoint2`, DISPID 107 and byte slot `0x3b8`, reaches this same `+0x4c0` through `[0x42d85500,0x42d856de)` and `[0x42d92350,0x42d923bf)`.

The public getters therefore converge on the display's derived text point. They do not fetch the stored `moDimText_c.f38` point.

## Selected ordinary point rule

Let `F` be the actual transform returned by note virtual `+0x370`, `A` the point from `getAttachLocation(0)`, `V` the actual `f628` vector and `d` the actual `f630` distance. For this concrete ordinary note the actual `+0x9a0` stacked-note predicate is false. The selected getter computes:

`P = ((A * F) + (V * d)) * inverse(F)`

The operator roles are bound by the model's actual imports from `sldmgu.dll`. In the identity-frame case this reduces to `P = A + V*d`. It does not use a captured absolute point, the note data name or the glyph cache as a substitute.

`A` is an actual display cache owner. `[0x4ba699e0,0x4ba69a58)` uses `display.f290` if the `f298` array is absent, has count at most one, or lacks the selected row. A valid row zero is used only when the actual count exceeds one, and supplies row `f08`. The method does not read the separate absolute-point attachment directly. A single array row is not enough to select that branch.

The returned `F` is identity if `display.f3e0 & 0x1000000` is set. Otherwise the ordinary non-stacked branch copies actual `f2a0`. When an actual model and a qualifying active visible annotation view exist, nonzero annotation-view rotation adjusts the returned transform. No general zero-rotation assumption is introduced. Fresh identity presentation and absence of that qualifying view must be established independently by the caller.

## Actual setter chain and distance production

Registered `IAnnotation.SetPosition2` is DISPID 91, byte slot `0x388`, three `VT_R8` arguments and `VT_BOOL` result. Its dispatch `[0x42ab5c30,0x42ab5d41)` invokes core `[0x42abdac0,0x42abddfa)` with flag one. The helper at `[0x42abad40,0x42abadef)` has an actual display-dimension class guard, so its dimension transform branch does not apply to the plain note.

The selected note route invokes `+0x3b8`. Actual target `[0x4b347fb0,0x4b347fba)` tails `+0x3c0`, bound to `[0x4c80cf70,0x4c80d08b)`. It reads the current actual point through `+0x3b0`, forms a requested-minus-current translation, obtains the actual frame and invokes `+0x340`. The latter target `[0x4c80a520,0x4c80a5a3)` reads `+0x4c0`, applies the supplied transform and passes the resulting requested point to actual `+0x4c8` at `[0x4c80e830,0x4c80e9da)`.

That final point setter uses the actual cached attachment and actual frame to form `Q = (requested-A)*F` as a vector transform. Its actual `+0x380` predicate controls whether local `Q.z` is zeroed. For concrete ordinary notes this predicate is `!f644`: `+0x9a0` is false and actual `+0x868` directly returns `f644`. The independently pinned null-attachment constructor leaves `f644=1`, so that constructor does not itself select the local-z rewrite. No unrelated exported alias is used to invent a semantic name for `f644`.

When the native `mgVector::isNotNull` predicate and the selected non-mirrored eligibility permit, the setter normalizes `Q` into actual `f628`. It always computes `sqrt(Q.sqlen())` and invokes `+0x3f8`, whose concrete `[0x4c80e480,0x4c80e489)` directly stores that double in `f630`. Zero displacement retains the existing direction and stores distance zero. The selected placement methods also change `f64c` from one to two when it is exactly one. General mirrored-view, stacked, attached and annotation-view policies remain explicit exclusions.

Current `moDisplayNote_c::Serialize` separately emits `f628` as an embedded three-double vector and `f630` as a double. They are active for current 19000; the prior grammar records the version-509 read gate and nonfinite load repairs. Runtime pointers and those inline wire values retain their different representations. The low-level distance leaf has no range check; the nonnegative norm is a property of this selected point-setter path.

## Independent disclosed evidence and retained failures

The independently hashed `PlainPositionFields01.json` reports four disclosed original/edited rows, zero position residual for `f290+f628*f630`, and distance equal to the independently computed norm within floating representation. Its source hashes and exact numerical distances are retained in the ledger. These are evidence rows, never writer inputs.

The two root-owned diagnostic retries are also bound by exact hashes. Both use four fresh processes with healthy controls, zero saves and no parameter edits. In the first, generated Unicode text matched while name was empty and position zero. In the second, the explicit actual name holder made the public name nonempty, but both `GetPosition` and `GetTextPoint2` remained zero before and after rebuild. Both reports explicitly retain `native_acceptance=false`. The generated requested point was nonzero; this checkpoint does not recast either trial as a success.

Static replay verified two exact modules, 22 complete functions, 14 decoded ranges, 21 imports and 16 concrete vtable cells. All selected instruction endpoints passed a separate LLVM decode. This lane made no CAD/VM call, decoded no saved CAD payload, ran no SDK/schema/codec or tests, and changed no shared source. The [sanitized receipt](../measurements/2026/DrawingPlainNotePositionSource01.json) keeps these scopes separate. The next native check belongs to root's independently generated, distance-complete note and full edit/save/fresh-reopen measurement; glyph metrics and the ordinary text backlink producer remain open.
