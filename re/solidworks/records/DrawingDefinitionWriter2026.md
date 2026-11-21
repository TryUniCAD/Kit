# Complete SDK blank drawing Definition codec

The internal SDK now emits and reads the entire `Contents/Definition` stream for the generated unformatted ANSI A blank-sheet profile. Four independently authored requests pass complete graph-to-wire-to-graph-to-identical-wire checks. This is an archive-codec boundary. The semantic drawing factory remains in research, public writing stays disabled, and this tranche has no new native-oracle acceptance.

Task: **B04-SW2026-DRAWPROPS / SDK blank Definition**. Owner: `/root/configuration_header`. Delivery: PR #121, with root owning staging, publication and the Windows oracle. Dependencies are the shared header, configuration and resolved layouts, the [frozen sheet writer](DrawingSheetWriter2026.md), and the already source-grounded drawing factories. The exit condition for this slice is complete current-version stream construction, exact independent readback, explicit rejection of unsupported graph profiles, zero runtime input-file access and unchanged public adapter admission. Complete neutral-document export and the broader CAD criteria remain open.

## Dependency gap and construction

The existing public `ReadConcept` intentionally stops after the model's resolved concept list. Its `moDrawing_c` rule is a prefix reader. It does not cover the remaining shared model state, drawing root suffix, UI state or trailer. Separately, the configuration layout's `Direct` action explicitly excludes inline drawing headers. Reusing either boundary unchanged cannot produce a complete drawing Definition.

The new [emission modules](../../../src/convert/adapters/solidworks/Drawing/Definition/Emission/) compose the following owners without changing those existing readers or configuration profiles:

| Owner | Encoding and classification | Source authority |
| --- | --- | --- |
| Five UI prefix fields | Five signed 32-bit values from the supplied UI owner | `slduiu!uiModelDoc_c::Serialize`, `0x497011e0` onward |
| Drawing CLSID | Document-kind vocabulary, `83a33d34-27c5-11ce-bfd4-00400513bb57`, Windows byte order | [Definition framing](DrawingDefinitionGrammar2026.md#definition-framing) |
| Root and inherited model bodies | Tagged `moDrawing_c`, then the existing lightweight and resolved model layouts | `sldmodu!0x4c95d340`; shared dispatch at `0x4c224e7b` and `0x4c224e8a` |
| Inline header | An ordinary tagged `moHeader_c` object using the active Definition map, replacing only the configuration-specific direct-binding action | Store at `0x4c17beea`, load at `0x4c17c456` |
| Header objects and identity | Existing canonical header field tables, typed strings, counted tuples and actual object aliases | Existing SDK `Header` codec and [header/model construction](ModelConstruction2026.md) |
| Sheet inherited and own fields | Existing shared inherited layouts followed by the unchanged `WriteSheetMut` own-field writer | [Sheet writer evidence](DrawingSheetWriter2026.md) |
| Detail folder | Inherited feature, ordered embedded object lists, transform, optional bucket selector and suffix state | [Sheet-support construction](DrawingEmptySheetObjects2026.md) and current drawing serializer grammar |
| Root tail, active sheet and managers | Actual sheet/property/layer/block owners, counted maps and typed suffix fields from the supplied graph | [Empty-manager construction](DrawingEmptyManagers2026.md) |
| UI sketch and helper owners | Actual profile ID, transform, drafting-standard runtime class, journal, typed options and counted UI collections | `uoSketch` at `0x49f6ee60`; [Definition grammar](DrawingDefinitionGrammar2026.md) |
| Drawing trailer | `u16` marker `0x0daf` followed by the two supplied signed 32-bit trailer fields | `slddrwu!0x3debc9ed` onward |
| Class tags, object tags, counts and final map counter | Computed by the existing shared executors from allocation and row order | Shared SDK archive primitives; all four generated cases end at index 131 |

The retained module identities are the exact 2026 authorities already recorded in those findings:

| Module | SHA-256 |
| --- | --- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `slduiu.dll` | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` |
| `slddrwu.dll` | `61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47` |
| `swccu.dll` | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |

This tranche reuses those retained source facts. It does not add a vendor binary, decompiled listing or new runtime trace.

## Typed graph boundary

`BlankGraph` carries the complete typed UI owner and explicit target version. `WriteBlankDef` validates the bounded graph before beginning its output, starts a new Definition map at 1, writes the UI prefix and CLSID, and emits the complete root and tail. It returns bytes, the computed map snapshot and actual grammar-usage evidence.

`ReadBlankDef` consumes those same owners through the shared field reader and canonical header reader. It rejects an unread tail and returns the complete typed graph, map and usage. `ReadBlankKids` accepts the shared codec's mutable rows and the construction bridge's immutable rows while preserving the actual ordered child nodes. The old prefix-only reader is unchanged.

Concrete header lists retain the header codec's tuple-of-nodes representation. Embedded body lists retain the shared field executor's row mappings. Both use the same object map. A second map for the inline header would break downstream references. [Inline-header gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingInlineHeadersNeedTheDefinitionMap.md)

The research [graph bridge](../../tooling/sw2026/serial/DrawingGraphBridge.py) projects independently constructed model fields into these existing typed representations. It evaluates live computed mappings, preserves node identity and turns authored strings into `CStringValue`. It reads no saved file and does not recover values from an emitted stream. The production codec imports no research builder or bridge.

The three fixed-width byte fields reached in the complete graph are typed owners, not opaque fallback spans: model `f784/f7a4` are the constructor's zero-initialized 16-byte members, and block-manager `f380` is the explicitly supplied independent UUID4 in Windows field order. Their sources are [model constructor state](ModelConstruction2026.md) and [block identity construction](DrawingEmptyManagers2026.md). No new payload constant is introduced by this codec.

## Admission boundary

The complete boundary admits version 19000, schema-one UI/drawing owners, one active unformatted ANSI A landscape sheet, its actual plane/profile/detail aliases, empty sketch geometry and empty layer/block/model-link maps. Ratios, names, property-view text, provenance, units, drafting vocabulary and the already modeled style fields come from the supplied graph. Zero-element layer-mask data has zero payload bytes by its declared count rule.

The guard rejects alternate versions or schemas, populated model-link/preview collections, sheet formats, broken support aliases, material payloads, wrong trailer markers, nonempty layer masks, detail buckets, sketch rows and missing native presence flags. Nonempty annotation and ink state is rejected by both full graph admission and the frozen sheet writer. Unknown concrete classes fail shared schema admission. Other malformed typed values fail the shared codecs; no enclosing stream is returned after an error.

## Executable proof

The [isolated process](../../tooling/sw2026/DrawingDefinitionProcess.py) constructs the canonical research graph and an independent fresh graph from the same new neutral request. Only the latter is projected into SDK owners. It requires:

1. Exact whole Definition bytes and final map counter.
2. Complete SDK read and re-emission with identical bytes and map.
3. A complete independent research read with no remaining bytes.
4. Identity of every logical stream in the generated container.
5. Public drawing readback and authored sheet metadata.
6. Zero guarded runtime input-file access and no public writer registration.

The final source freeze contains 32 code/test files and has SHA-256 `232f3f0f1dac63e9c110e271f24b24bac3b5b4177fbe3bd404d1e49f24d16c98`. The private final process receipt has SHA-256 `7fcef3e673fb8ae76a03de810a5f8a114db546881d625e3979d8c7cc25a006a3`. Source hashes are checked before and after the cohort.

| Fresh authored request | Definition bytes | Final map index | Variation |
| --- | ---: | ---: | --- |
| `WholeAlpha` | 23,857 | 131 | Independent names/provenance/UUID4 and 4:9 sheet scale |
| `WholeBeta` | 24,553 | 131 | Long Unicode property text and 11:3 scale |
| `WholeGamma` | 23,857 | 131 | Inch document units, imperial zones and 7:13 scale |
| `WholeDelta` | 23,856 | 131 | ISO drafting runtime vocabulary and 19:8 scale |

Each positive runs in two fresh processes with identical stdout. Twelve additional complete jobs exercise the rejected boundaries. All twenty processes pass their expected outcome. No original, previous native trial output, hidden input, Windows session or CAD runtime is opened. The earlier source01 run is retained privately as historical pre-guard evidence; the final source02 run adds the explicit reader admission guard and reproduces every prior positive byte and negative result.

The [sanitized receipt](../measurements/2026/SdkDrawingDefinition01.json) records exact source, input and output hashes. The focused integration modules are under `tests/Convert/Solidworks/Research/Drawing/Definition/`. Call `TestWholeDefs` and `TestDefGuards` through the normal complete integration suite. The private exact replay driver repeats all twenty processes from a separately supplied checkout after checking the frozen manifest.

Targeted steering, Black, Mypy and Pyright pass for all 30 production/test modules. The donor scan is clean across the observed 3,533 source files. Pyright also prints three existing unrecognized project-setting messages; these are not suppressed or counted as new codec diagnostics.

These checks establish complete serialization for the exercised graph profile. They do not establish a production neutral drawing factory, populated-view Definition writing, native edit/save/reopen for these new requests, arbitrary sheets, annotations or complete CAD conversion. Public writer admission and revision-bound native acceptance remain root-owned work.
