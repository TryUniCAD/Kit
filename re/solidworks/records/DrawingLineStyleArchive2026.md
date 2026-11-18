# Drawing line-style records in SOLIDWORKS 2026

Both actual originals advance through line-style objects and still reject `uiLFConfig_c` schema one. The preceding line-style failures and their four completed edge bodies each remain retained. This separate tranche reuses the complete existing SDK line-style field rule. It does not infer a style pattern, display default, font assignment, or writer policy.

Task: PR121 ordinary drawing line-style dependency. Owner: `flag_ownership`; delivery PR: #121. Dependency: [end-face ID reader](DrawingEndFaceIdArchive2026.md). Exit: independently bound actual native dispatch and current wire order, a frozen minimal drawing linkage, prior-profile replay, and the exact original parser outcome or next boundary. Native and held-out writer acceptance remain separate.

## Actual native owner

The module is `sldmfcu.dll` SHA-256 `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`, version `34.5.2.0604`. The [JSON proof](DrawingLineStyleArchive2026.json) records the original module, actual primary table, RTTI, descriptor, and complete exception-directory function closure.

The actual `moLineStyle_c` primary is `0x3cc758e8`; its `+0x28` serializer is `0x3c7fa820`. RTTI derives directly from `su_CObject` and `CObject`. The runtime descriptor has versioned schema `0x80000001`, so current concrete wire schema is one.

The complete serializer `[0x3c7fa820,0x3c7fa934)` is 276 bytes, SHA-256 `23a24b72a2f549ebb8cfb0b0cfa4650e7de5ca88c4d388ddc73715091589252c`. This independently matches the already published [pattern proof](RadialPatternSemantics2026.json) and actual table binding in [style construction](RadialStyleConstruction2026.json). Their constructor/display defaults are not transferred into this reader.

## Field order

For the ordinary non-database version-19000 stream, `su_CObject` contributes no own bytes and the line-style serializer has no additional context or version-selected fields. Its complete body is:

| Order | Field | Encoding |
| ---: | --- | --- |
| 1 | `f08` | CString |
| 2 | `f10` | CString |
| 3 | `nseg` | `u16` |
| 4 | `f18` | Exactly `nseg` ordered rows, each `seg:f64` |
| 5 | `f20` | `u8` |

The [existing SDK rule](../../../src/convert/adapters/solidworks/Archive/Definition/Fields/DocStyleFields.py) already encodes those fields. The drawing profile imports only its `moLineStyle_c` entry and admits concrete schema one. The unrelated BOM rule in that same mapping is not admitted. No shared field layout changes.

Strings, ordered segment values, and the flag byte remain source wire inputs. They are not matched to a table of saved patterns, reordered, or converted into a generated display policy. The existing `u16` encoder rejects a modeled list longer than 65,535 entries; pathological oversized native lists and arbitrary segment semantics are outside this proof.

## Scope and verification

The drawing route retains its exact ordinary version and helper-mode guards. The existing part/assembly paths, aliases, framing, field evaluators, constructors, and frozen original drawing writer remain unchanged. This is a raw codec linkage, not a claim that the original drawing semantic gap is solved.

The two SDK paths pass AST, Black, Ruff, scoped strict Mypy, scoped strict Pyright, steering, and the recorded-payload static scan. The worker ran no product probe, local test suite, vendor code, or VM operation. The exact source closure contains 4,350 files. Root independently passed all 43 prior-profile workers on the exact frozen source. Both actual original probes preserve source immutability and still reject at `uiLFConfig_c` schema one. The [receipt](../measurements/2026/DrawingLineStyleReader01.json) binds both new results and preserves earlier failures.

The preceding real failures and four completed edge-body events per original remain retained. Full original Definition parity, source semantic completeness, native usability, and held-out writer acceptance remain unclaimed pending their own evidence.

Confidence: concrete native identity and the selected raw field grammar are confirmed static facts. New original stream closure, display/constructor semantics, full neutral drawing projection, and native acceptance remain partial or unmeasured.

The governing stopping conditions remain exact: “The first is success under every criterion on this page.” and “The second is the end of the available context.” Missing grammar remains work.
