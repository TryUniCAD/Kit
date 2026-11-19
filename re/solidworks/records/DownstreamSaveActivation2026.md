# Conditional downstream activation during document save, SOLIDWORKS 2026

The exact `uiModelDoc_c::saveDocument` path conditionally sets application downstream state to one immediately before the actual base-document save. This identifies a concrete save-time activation edge. It does **not** yet identify creation or writing of a standalone `-DownstreamIdData` stream.

Task `B04-SW2026-DOWNSTREAM-ID-DATA` belongs to `/root/flag_ownership` in PR #121. [Constructor state](DownstreamConstructorEnable2026.md) · [Standalone maps](DownstreamStandaloneMaps2026.md) The [numeric checkpoint](DownstreamSaveActivation2026.json) binds original images, six complete owners, selected windows, imports and the actual setter slot. No proprietary instruction bytes or listings are included.

## Exact original route

`slduiu.dll` SHA-256 is `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7`, preferred base `0x48ea0000`. Exact export `uiModelDoc_c::saveDocument(PCWSTR)` is `[0x497257a0,0x49725e64)`, 1,732 bytes, SHA-256 `95f4b2520be62beb3a4bda911b8b1b5ad49ecb37d1d0a105fa6e9bad3e6a93c8`. The full declared exception extent is used, rather than an adjacent export label.

After earlier save checks, the selected window `[0x49725b9a,0x49725bf7)` performs this conjunction in order:

1. Actual UI document virtual `+0x1250` returns nonzero. The [independently bound context vocabulary](DrawingUserEnvironmentArchive2026.md) identifies this document slot as `isPartDoc`.
2. `uiEnvironment_c::get()->getBOOL(RegKey_e(0x5f2), 0)` returns nonzero.
3. Actual document virtual `+0x1300`, the model getter, returns a nonnull model.
4. `moConcept_c::hasFeatForMsgpack` on that actual model returns true.

Only then does `0x49725bf1` call the imported `CAmApp::setEnableDownstreamIds` with `EDX=1` and `RCX=am_GetApp()`. This writes application runtime i32 `+0x464`. A failed conjunction skips this direct setter call and preserves the prior field value on the observed path. The complete direct caller has no second selected setter call restoring the previous value, but transitive restoration is not closed.

Internal setting `0x5f2` is bound numerically and by the actual typed `getBOOL` import. Its storage/resource name and meaning remain open. The zero argument is a **caller fallback**, not a measured actual preference or a freshly observed application default. No setting was read from an application, changed, or proposed as an experiment input.

At `0x49725c0d`, the next actual save call goes through IAT `0x4a468078` to `sldappu!uiBaseDoc_c::OnSaveDocument`, exact entry `0x458e71f0`. It receives the actual UI document and the original filename argument. The file serializer and stream path need separate source binding.

## Actual application setter and feature predicate

The actual `App_c` primary table `0x4a7a9460` binds setter slot `+0x558` at `0x4a7a99b8` to bridge `[0x4a26dc90,0x4a26dcaf)`, SHA-256 `ef2391b1a03fe5a63d7805aea77b87679b48b1b9380ef870d598537dd4d6c086`. It forwards the supplied integer through `am_GetApp` to the same exact application setter. The direct save call and virtual bridge are distinct caller forms.

`sldappu.dll` SHA-256 is `50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf`. Setter `[0x45822320,0x45822327)` stores the integer directly. Getter `[0x45813b80,0x45813b87)` returns it. No initial value follows from these accessors. The candidate found through a primary-table reference at `0x457d48c0` is exactly exported **`CAmApp::~CAmApp`**, `[0x457d48a0,0x457d5c81)`, not a constructor. It is refuted as fresh-default evidence.

`sldmodu.dll` SHA-256 is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Complete `hasFeatForMsgpack` is `[0x4bdac860,0x4bdac8e8)`, 136 bytes, SHA-256 `625b03181dc80b9eb46283fa4a21e78a97f819154f90cba5763e921e6aa1d603`. It returns false for a null/empty direct-child list at concept `+0x60`, otherwise walks actual children and succeeds if any child returns nonzero at virtual `+0x830`, `+0x5e8`, `+0xbe8` or `+0x838`. Concrete child predicate meanings are not newly bound. Do not infer that every ordinary part qualifies from this method's name.

## Scoped search and next exit

The selected named-import/direct-call search covered original app, UI, executable, MFC and model images. Only UI exposed the selected setter import and two selected IAT sites above. No same-image direct E8 setter call was found in app `.text`. That search does not close virtual, inlined, aliased or unresolved ordinal callers.

Next bind the actual `OnSaveDocument` route to its selected file serializer, then identify any concrete configuration stream creation/store and context. Separately bind application initialization and setting identity. An enabled runtime cache is not itself evidence of persisted stream creation, framing or native acceptance.

These are **confirmed static conditional edges**. Runtime preference values, constructor default, standalone save route and native/held-out acceptance remain **unmeasured/open**. No VM, CAD, COM, preference/license change, hidden input, saved CAD read, test, codec, schema or product execution occurred. The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) retain: “The first is success under every criterion on this page.” “The second is the end of the available context.” This bounded source checkpoint is not CAD completion.
