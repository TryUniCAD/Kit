# Drawing line-font records in SOLIDWORKS 2026

Both actual originals advance through line-font objects and still reject `uiUserModelEnv_c` schema one. This separate reader tranche admits `uiLFConfig_c` schema one through the existing shared font fields in ordinary version-19000 drawing Definition. It adds no field layout, font vocabulary, width default, constructor, or writer capability. The original complete-source and held-out writer rejection remains unchanged.

Task: PR121 ordinary drawing line-font dependency. Owner: `flag_ownership`; delivery PR: #121. Dependency: [line-style reader](DrawingLineStyleArchive2026.md). Exit: complete concrete native binding and current read/store order, frozen minimal linkage, independent prior-profile replay, and the exact original parser result or next boundary. A class codec does not qualify complete drawing semantics or vendor usability.

## Native owner and exact body

All addresses refer to `sldmfcu.dll`, version `34.5.2.0604`, SHA-256 `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`. The [JSON proof](DrawingLineFontArchive2026.json) binds original-image spans, RTTI, runtime descriptor, imports, and complete exception-directory function closures. The leaf predicate is bounded by both reachable returns rather than trailing alignment bytes.

The actual primary table `0x3cc719c0` has serializer `0x3c7a7760` in slot `+0x28`. RTTI derives directly from `su_CObject` and `CObject`. The descriptor at `0x3ce6cfd0` has versioned schema `0x80000001` and object size 32. The ordinary non-database object base contributes no own bytes, as independently established in [the common archive evidence](MaterialDisplayArchive2026.md).

| Function                         | Complete half-open extent | Bytes | SHA-256                                                            |
| -------------------------------- | ------------------------- | ----: | ------------------------------------------------------------------ |
| Line-font serializer             | `[0x3c7a7760,0x3c7a782b)` |   203 | `916eeff0928a3c5518cbfffa70d890be0f14f332d049a7e5ab8c37c10f1cd614` |
| Embedded width serializer        | `[0x3c84a9e0,0x3c84aadb)` |   251 | `5327ffc9c4850eecdadd8bf8bc689ee86d87eeb03da5ec41e3234872b82ff791` |
| Width runtime cache update       | `[0x3c84ab40,0x3c84ac9d)` |   349 | `e8a03afb203d9b3397df7c973e5723129c029b03a76bc503f38e6233295a996f` |
| Read-only custom-width predicate | `[0x3c84aca0,0x3c84acb5)` |    21 | `7eef88f6b45fe844fce4d297bc8ba0be3b1df4ae00054c811f0e5b7e15dfff37` |

## Current raw wire order

| Order | Owner and key   | Encoding       | Native store / read         |
| ----: | --------------- | -------------- | --------------------------- |
|     1 | Font `f08`      | CString        | `0x3c7a77a4` / `0x3c7a77cb` |
|     2 | Width `f10.f06` | `i16`          | `0x3c84aa1e` / `0x3c84aaac` |
|     3 | Width `f10.f00` | `f32`          | `0x3c84aa2b` / `0x3c84aab8` |
|     4 | Font `f18`      | `i16` raw word | `0x3c7a77c3` / `0x3c7a77ff` |

The native font reader sign-extends the final short into runtime `i32@+0x18`; the store writes its low 16 bits through the unsigned-short overload. The shared signed-short raw representation preserves those same wire bits. This does not establish a semantic font-cap domain for arbitrary values.

The actual width receiver is the embedded object at font `+0x10`. Store passes restore type zero and force zero; read passes restore type two and force zero. The width reader selects the modern short-plus-float grammar when force is nonzero or effective version is at least `0x0f41`. For older versions with force zero, restore types one, two, and three read a char, short, or int respectively into the runtime short; other restore types read no width field. Those legacy branches do not read the modern float. The font reader separately reads its final short only from version `0x0c9f`; the older branch sets runtime zero without a wire word. Store always emits the modern fields. Only exact version 19000 is admitted here.

The effective-version helper `[0x3c777130,0x3c777167)`, SHA-256 `ad0107c7ead279cd5b1bf68d9c01b5b641a70d4ba45c956675b6f04fc6b99236`, independently matches the existing current-build evidence. A zero native helper version can consult version-manager state; this reader does not infer that every such state is 19000.

## Runtime cache is separate from raw values

After modern width reads, `0x3c84aac1` calls the cache updater. Its only direct writes to the original width receiver are the unpersisted short at `+0x04`: clear at `0x3c84ab6e`, then a computed print-weight index at `0x3c84ac71`. The only called function receiving that original receiver is the complete read-only predicate. Subsequent print-data calls receive a separate stack-local object. No serialized `f00` or `f06` store occurs in that bounded receiver dataflow.

The predicate tests the carry flag from comparing zero with the stored float, followed by width code ten. For finite floats this corresponds to positive width with code ten. Unordered comparisons also set carry if the instruction completes; exception masking and pathological NaN inputs have not been measured or qualified. The [comparison gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/Qualification/WidthPredicateUsesUnorderedCompareFlags.md) retains that distinction. Neither the cache policy nor a guessed mathematical predicate is added to the raw codec.

The [existing SDK font rules](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Config/FontFields.py) already encode this field order and are inherited in drawing layouts. Only concrete `uiLFConfig_c` schema one is added to [the linked drawing admission](../../../src/convert/adapters/solidworks/Drawing/Definition/Linked/FrontSchemas.py). All values come from the source wire. No font assignment or saved row is selected.

## Qualification boundary

The drawing profile keeps its exact version and ordinary-context guards. Existing part/assembly layouts, scalar semantics, aliases, map allocation, framing, public adapter registration, and original frozen drawing construction remain unchanged.

The single SDK path passes AST, Black, Ruff, scoped strict Mypy, scoped strict Pyright, steering, and the recorded-payload static scan. The worker ran no SDK probe, codec, local test suite, vendor application, or VM operation. The corrected source closure contains 4,350 files and is literally source-identical to the first line-font candidate; only metadata corrects the unordered-comparison shorthand. Root independently passed all 43 prior-profile workers on the first candidate, and both worker and root verified exact source identity with the corrected candidate. Both actual original probes use the corrected manifest, preserve source immutability, and now fail closed at `uiUserModelEnv_c` schema one. The [custody receipt](../measurements/2026/DrawingLineFontReader01.json) binds both results and preserves the proof-only correction and previous genuine failures.

Concrete dispatch and selected current raw grammar are confirmed static facts. Whole actual Definition parity, full neutral drawing projection, font/display construction, native usability, and held-out writer acceptance require their separate evidence. Missing grammar remains work.

The mandatory stopping conditions remain “The first is success under every criterion on this page.” and “The second is the end of the available context.”
