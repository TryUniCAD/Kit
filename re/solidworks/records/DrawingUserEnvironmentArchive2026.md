# Drawing user environments in SOLIDWORKS 2026

Both actual originals enter the environment and still fail closed at the missing embedded method layout `uiSplitterInfo_c.Serialize`. The environment and secondary splitter bodies are incomplete. The ordinary drawing environment has a different wire body from the part/assembly environment: it omits the first splitter at `f10`. This reader tranche reuses all remaining shared fields behind the existing ordinary drawing-context guard. It adds no saved username, viewport row, presentation default, constructor, or writer capability. Original complete-source and held-out writer rejection remain unchanged.

Task: PR121 ordinary drawing environment dependency. Owner: `flag_ownership`; delivery PR: #121. Dependency: [line-font reader](DrawingLineFontArchive2026.md). Exit: actual native serializer and embedded-owner binding, bounded document-kind selection, frozen drawing-only field rule, independent prior-profile replay, and exact original parser result or next boundary. Complete drawing semantics and native acceptance stay separate.

## Actual owner and context

The [JSON proof](DrawingUserEnvironmentArchive2026.json) records original module hashes, primary tables, RTTI, runtime descriptors, complete exception-directory closures, import identities, and leaf boundaries. No vendor instructions or decompiled listings are included.

| Module, build `34.5.2.0604` | SHA-256                                                            |
| --------------------------- | ------------------------------------------------------------------ |
| `slduiu.dll`                | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` |
| `sldappu.dll`               | `50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf` |
| `slddrwu.dll`               | `61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47` |
| `doccplu.dll`               | `ad0c266a966381defe9a68c11b76dc318acc6a9f6ac428d5aa253049df87ddd8` |

`uiUserModelEnv_c` has actual primary `0x4a65e7b0`, serializer slot `+0x28` target `0x497d5ee0`, direct `su_CObject`/`CObject` RTTI parents, versioned schema `0x80000001`, and object size 464. Its complete serializer `[0x497d5ee0,0x497d6229)` is 841 bytes, SHA-256 `617b627aa472a12ed2a23455804c84da65420b8f6e7bf87efc805eae03e7611d`.

The receiver used for document-kind selection is the `SldModelContext_c` at registered helper `+0x38`. It is distinct from the model and UI document's primary receiver. The existing [storage/helper evidence](DrawingEdgeReferenceArchive2026.md) binds the actual cold helper. At `doccplu!0x180024aa9`, storage obtains `uiBaseDoc_c::ModelContext`; it passes the result as constructor argument `R8` at `0x180024ab9`. The exact accessor `sldappu!0x458e6970` returns document `+0x4d8` or null for a null receiver. The UI helper constructor writes the supplied context to `+0x38` at `0x496f56c2`.

The cold `uiBaseDoc_c` constructor allocates its base context, calls the exact context constructor at `0x458e46d1`, and stores it in document `+0x4d8` at `0x458e46db`. The complete 33-byte `BaseDocModelContext_c` constructor `[0x458ecdd0,0x458ecdf1)`, SHA-256 `e1cac7b361865fb24f5687215e6f2707a39bd50f676cc1b0e64f4d78e309589c`, installs table `0x45f0a878` and binds context `+0x08` to the supplied UI document. The actual `ModelDocModelContext_c` table `0x4a65d908` inherits the same part/assembly predicate implementations through bound UI import thunks.

For both these bound context tables, virtual `+0x80` is `BaseDocModelContext_c::isPartDoc`, target `0x458eee50`; `+0x88` is `isAssemblyDoc`, target `0x458eec90`. Each complete function is 33 bytes. They dispatch through the linked UI document's `+0x1250` and `+0x1258`, respectively. The actual drawing primary `0x3e1d6b78` binds both slots to `uiModelDoc_c` imports resolving to the complete three-byte zero leaf `slduiu!0x48ee4c00`. Thus both predicates are false for the selected ordinary drawing document.

The environment stores its first splitter only when one of those predicates succeeds, at `0x497d5fa8`/`0x497d5fb8`, with embedded serialization at `0x497d5fcc`. The read branch applies the same tests at `0x497d6066`/`0x497d6076`, with embedded serialization at `0x497d608a`. The drawing therefore omits this field in both directions. Unknown substituted contexts and the null-helper/archive fallback are not modeled or claimed to preserve this result. No universal callback or owner-preservation claim is made.

## Current drawing field order

For exact version 19000 and the ordinary non-database drawing context:

| Order | Key                            | Encoding                                                     |
| ----: | ------------------------------ | ------------------------------------------------------------ |
|     1 | `f08`                          | CString                                                      |
|     2 | `f1b0`, `f1b4`                 | Two `i32` words                                              |
|     3 | `fe0`                          | Embedded `uiSplitterInfo_c.Serialize`, without an object tag |
|     4 | `f1b8`, `f1bc`, `f1c0`, `f1c4` | Four `i32` words                                             |

Store emits all current fields. Read gates are `>=0x388` for the first two integers, `>=0x515` for the secondary splitter, `>=0x8e6` for `f1b8/f1bc`, `>=0xf56` for `f1c0`, and `>=0x1ff1` for `f1c4`. All are active at 19000. The ordinary `su_CObject` base contributes no own bytes. No legacy or database path is admitted.

The shared [part/assembly environment layout](../../../src/convert/adapters/solidworks/Archive/Definition/Fields/DocEnvironmentFields.py) is unchanged. The [drawing rule](../../../src/convert/adapters/solidworks/Drawing/Definition/Linked/Fields/EnvironmentFields.py) excludes only its direct `f10` operation. Nested splitter `f10` header words and every secondary cell remain present. The existing drawing guard rejects other owner kinds and special contexts. See [the separate first-splitter gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/Qualification/DrawingEnvironmentsOmitPrimarySplitter.md).

## Embedded splitter and raw/runtime distinctions

The actual splitter primary `0x4a65e720` binds slot `+0x28` to `0x497d5b00`. The environment constructor calls the concrete splitter constructor `0x497d5600` for both embedded members; that constructor installs this table. The complete splitter serializer `[0x497d5b00,0x497d5ed7)` is 983 bytes, SHA-256 `dee8484e884bbb8fd19a4dc22095ec5c9df7e35835c0d0b7cfd92057261eebd9`.

Its current body writes eight `u16` header words, `f08,f0c,f10,f14,f18,f1c,f20,f24`. It then visits `f08` rows and `f0c` columns in row order. Every cell contains two embedded transform bodies `xa,xb`, two `u16` words `a,b`, one `f64` word `c`, and CString `d`. The imported native transform methods are the existing `sldmgu!mgXform_c::save/restore` owners. No new object tag is inserted around either transform or splitter.

Current read gates are `>=0x45d` for cell `b`, `>=0x1b6` for `c`, and `>=0xbdb` for `d`. All are active here. The native reader zero-extends header shorts into runtime integer fields. It also changes cell `b==0xffff` to runtime zero at `0x497d5dff–0x497d5e12`. The raw codec retains the source word rather than executing that repair. A settings-dependent legacy `+0xc8` cache update is restricted to versions at most `0xd48` and is excluded at 19000.

The existing shared splitter field rule and count/transform evaluation are reused unchanged. Arbitrary oversized native grids, transform allocation and UI application semantics are not qualified by this raw grammar. All decoded strings, dimensions, scalars and transforms remain source wire inputs; no captured view or username becomes a production constant.

## Evidence boundary

The three SDK paths pass AST, Black, Ruff, scoped strict Mypy, scoped strict Pyright, steering, and the recorded-payload static scan. The first candidate is retained for its initial Black line-wrap failure; the corrected candidate has the same AST and no field-rule change. The worker ran no SDK probe, codec, local test suite, vendor application, or VM operation. The frozen corrected source closure contains 4,351 files. Root independently passed all 43 prior-profile workers on the corrected exact source. Both actual originals preserve source immutability and stop at `uiSplitterInfo_c.Serialize`, a missing embedded-method layout rather than a runtime schema failure. The drawing sparse layout did not inherit that shared key simply by reusing the containing environment tuple. Neither environment nor secondary splitter completion is credited. The [custody receipt](../measurements/2026/DrawingUserEnvironmentReader01.json) retains both results and the previous genuine rejections. The explicit shared splitter linkage requires its separate source proof and replay.

Native identity, selected current field grammar, and the bounded context/document dispatch are confirmed static facts. Whole actual Definition parity, source-semantic projection, fresh environment construction, native usability, and held-out writer acceptance require separate evidence. The original writer and its failed complete-source verdict remain fixed.

The mandatory stopping conditions remain “The first is success under every criterion on this page.” and “The second is the end of the available context.” Missing grammar remains work.
