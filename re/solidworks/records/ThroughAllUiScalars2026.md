# Ordinary part UI scalars and environment count

Four source-owned Definition scalars now reconstruct through explicit typed inputs on disclosed D01/D02. Actual per-user splitter/window construction remains unfinished, so complete-source, public and native acceptance stay closed.

Task: `B04-SW2026-EXTRUDE-THROUGHALL`. Owner: PR #121 root / configuration-header lane. Delivery PR: #121. Dependency: the frozen line-presentation component and preceding source configuration, members, camera and empty-manager layers. Component exit: source scalar parity, new semantic combinations, unchanged older bytes and fail-closed checks. Full-source exit still requires per-user environment, remaining CMgr ownership and controlled original-source acceptance.

## Field ownership

| Wire field | Actual native owner | Generative input/rule |
|---|---|---|
| `fad0:u16` | Active Brep view's `uiBaseView_c+0x170`, named `hlrDisplayQualityType` | Explicit quality code zero/one; no guessed high/draft label |
| `fad4:u8` | Document grid word `+0xad4` | Constructor seed three, independently chosen grid bit zero: `2 | int(DisplayGrid)` |
| `fb00:u16` | Confirmed default-context type at `+0xb00` | Derived part type one from actual part validator |
| `fb04:u16` | Default context's command-group selection at `+0xb04` | Semantic `features` maps to declared resource ID `38284`; explicit cleared group maps to zero |
| `nenv:u16` | Number of typed objects in environment array `faf8` | Computed by the existing collection writer; source audit verifies declared count, actual rows and concrete owners |

The four-word component requires current schema-one `uiPartDoc_c`, archive version 19000 and the measured display-mode code `facc=3`. It refuses other quality values, grid bits, unconfirmed/other context types, drawing or unknown command groups, malformed counts, aliases, null/wrong environment owners and other schemas. Existing raw codecs and public registrations are unchanged.

## Pinned implementation

The [numeric native packet](PartUiScalarConstruction2026.json) pins five original modules, eighteen operand ranges, complete relevant functions, the actual part primary/RTTI and selected import thunks. It contains no vendor bytes or listings. Its independent PE reproduction is byte-identical.

### HLR quality and grid

At `slduiu!0x4970142d` the serializer obtains the active Brep view, reads view `+0x170` at `0x49701432` and updates document `+0xad0` at `0x49701438`. It writes the low unsigned16 at `0x49701478`. The independent `sldappu!uiBaseView_c::hlrDisplayQuality` alias at `0x456fa890` reads that exact member. Setter `[0x459a1270,0x459a1297)` saves previous quality at `+0x174`, obeys runtime lock `+0x228`, and maps sentinel `65535` to zero. The bounded component refuses the sentinel and other unqualified values rather than relying on normalization. It does not model live lock state.

Grid reuses the [already proved document toggle](DrawingDocumentDisplayFlags2026.md): constructor stores three, the named setter changes only bit zero, and the common serializer writes the low byte. The other stored bit is retained from constructor knowledge. This does not transfer the drawing-specific annotation-mask save merge to parts; the existing source detail-mask input remains unchanged.

### Default context and Features

Named getter `[0x49786f80,0x49787040)` and setter `[0x497b9060,0x497b9132)` bind context type, command group and a third runtime flags value at `+0xb00/+0xb04/+0xb08`. Virtual `+0x12c8` is `isEditingSelf`, not a document-kind predicate. When false, these methods can delegate through the actual edit-target `ModelContext.Document`; the bounded standalone part profile does not generalize that path. The third runtime argument is not an additional adjacent wire word.

Current store copies the first two members to locals, invokes document virtual `+0x2ed0` at `0x497018f9`, then emits their low unsigned16 values. Current load zero-extends both words and invokes the same confirmation hook at `0x497033d4`.

The actual part constructor installs primary `0x3349e068`, whose `+0x2ed0` selects `uiPartDoc_c::iConfirmDocContextModes [0x3338bcd0,0x3338bce3)`. If context type is not one, it sets type one and clears the group. Type one preserves the group. Thus fresh constructor `0/0` words and saved confirmed `1/0` are separate states. Older default output is preserved; the new component explicitly requests the confirmed source context.

The exact installed English `sldresu` resource `38284` is the Features command group, while adjacent `38283` is Drawings. Both lie in string block 2393, language 1033, slots twelve/eleven; the packet pins the original module and payload hash. Native `updateContextToolbar` passes the actual group through the named `uiToolBarManager_c::setContextToolbarMode` import. The Features ID is native vocabulary derived from this owner/resource route, not a saved numeric seed. Localized caption text is not emitted, and no installed resource is loaded by the SDK constructor.

### Environment count and real remaining gap

Native store first creates an empty array wrapper if `+0xaf8` is null. It looks up current-user environment data. If actual `isOpenedHidden` is false and the separate document `+0x3d0` equals zero, it creates/captures a current-user environment or updates an existing one. The semantic name of that separate `+0x3d0` gate is not established here.

After that capture pass, store emits zero for a null buffer, otherwise low unsigned16 of `amDynamicArrayCount(buffer)`, then all corresponding typed object tags. The bound count leaf at `sldmgu!0x31deec50` reads signed32 at `buffer-16`. This is collection length, neither a presence bit nor an unconditional one. The typed writer already computes it from actual rows and rejects oversized counts.

Load consumes the declared unsigned16 loop. It can discard nulls and entries already found by the environment-name finder before live insertion; additional path-dependent compatibility handling remains separate. Raw typed readback does not execute these UI filters. The on-disk count therefore does not universally predict post-load live array size or active-window selection.

Part environments serialize both primary `f10` and secondary `fe0` splitters. [Drawing environments](DrawingUserEnvironmentArchive2026.md) omit the first splitter through their separate context predicates. That drawing profile cannot seed a part environment.

`CountPartEnvs` audits the typed wire collection and concrete class/schema only. It does not project or reconstruct the two splitter/window bodies. Both disclosed sources have count one, while this partial fresh composition retains the earlier zero-row constructor. The source envelope and unchanged complete-source refusal keep that discrepancy explicit. No saved username, splitter row or window value enters the constructor.

## Actual host result

The [92-process receipt](../measurements/2026/ThroughAllUiScalars01.json) records both disclosed source cases, eight independently chosen quality/grid/group combinations, seventy independent fragment re-emissions and forty-eight SDK refusals. Every four-word source value matches exactly, and the previous six owner fragments, line tables, cameras and empty managers remain exact. Old callers preserve full Definition bytes; two old complete-container/public-reader pairs match. Scoped Black, Ruff, strict Mypy/Pyright, steering and donor checks pass. All guarded constructors/readbacks record zero runtime file access.

The [post-build inventory](ThroughAllUiScalarOwners2026.json) leaves exactly `faf8` and `nenv` as two Definition frontier markers, plus twenty-nine CMgr frontiers. Their nested fields are not counted individually by these frontier totals. All original held-outs and D03 remain unopened in this tranche. Native launches, new complete native outputs and source/public admission are zero/false. These facts are a component checkpoint, not complete conversion or visible UI acceptance.
