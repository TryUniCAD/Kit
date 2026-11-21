# Downstream build date and concrete enable receiver, SOLIDWORKS 2026

The original build's date-code **cache-miss path computes `2026306` from embedded build metadata**. It does not consult the live clock. The registered UI application's enable slot resolves to a mutable `CAmApp` i32 field, not a universal constant. Neither finding binds the still-open standalone save caller or establishes native acceptance.

Task `B04-SW2026-DOWNSTREAM-ID-DATA` belongs to `/root/flag_ownership` in PR #121. This is an additive static follow-up to [constructor/enable ownership](DownstreamConstructorEnable2026.md), [standalone maps](DownstreamStandaloneMaps2026.md) and the [direct body grammar](DownstreamIdArchiveGrammar2026.md). All three earlier private deliveries remain unchanged. The [numeric companion](DownstreamDateAndEnable2026.json) binds complete original extents, hashes, RTTI, table/object pointers, selected instruction windows and import identities. No vendor instructions, listings or complete embedded string are included.

## Original identities

| Image | Preferred base | SHA-256 |
| --- | --- | --- |
| `sldutu.dll` | `0x3cf80000` | `dbc147c10b658544e44a7c13d3ae656c26a0778e9241fe74d6ca9ecae8730933` |
| `sldsessionu.dll` | `0x31980000` | `c53d42d0b7bcfd9abf78cfd71ca6f71645cb8da16ea29c155f63172eaa17f421` |
| `slduiu.dll` | `0x48ea0000` | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` |
| `sldappu.dll` | `0x453f0000` | `50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf` |
| `mfc140u.dll` | `0x180000000` | `88beebf73667ab0d603355f54562aa9cf9316f4d585a40ec93430c6715ffc8d1` |

## Exact date-code producer

`su_getFullDateCode` is `[0x3d0107b0,0x3d0107e5)`, SHA-256 `f94d4ced8922d22b33a46acbb97d7337cde0a6bf4e65baca39f72aa03a8fe7eb`. Let `t` be the unsigned 32-bit result of `su_getTaggedDateCode`:

| Condition | Full-code result |
| --- | --- |
| `1 <= t < 9600` | `t + 2000000` |
| `9600 <= t <= 99999` | `t + 1900000` |
| Otherwise | `t` |

This corroborates the earlier [history utility rule](HistoryConstruction2026.md). Complete tagged producer `[0x3d014520,0x3d0145ab)` has SHA-256 `c3d522fb52757d409a4a4f729aa047e2480199304c44ee9e2c7c8084c2685208` and adds the missing input ownership:

1. Return the cache at `0x3d33d138` when it is nonzero.
2. Otherwise construct a Unicode `CString` from the narrow embedded build-metadata string at `0x3d319248`.
3. Remove trailing whitespace using the reached `iswspace` operation.
4. Take `Right(max(length - 14, 0))`, assign that substring and parse with `_wtol`.
5. Store and return the unsigned 32-bit result.

The pinned literal has 59 narrow characters: a 14-character discarded prefix, seven decimal characters and 38 trailing ASCII spaces. Its complete 60-byte original span, including terminator, has SHA-256 `6cbbca2a0fb5312ad3a2fcb0a9a7b781d8a5e78e9d25a5d7148cc8c5b0608bf8`. Successful conversion/substring/decimal parsing yields `t=2026306`. The full-code function returns that value directly from the original build metadata.

The cached word is not raw-file-backed. The selected direct RIP-relative DWORD search found two loads and the producer's one store. Indirect aliases and runtime overrides remain open. The cache-miss result is confirmed statically, while no actual live cache or returned value was measured. No calendar interpretation of the decimal code, future-release value or neutral provenance policy is inferred. Raw source replay retains the saved `f10` and history values. The computed value applies to the constructor cache-miss path.

## Framework identity and evidence limits

The typed operation meanings were checked against the exact framework implementations. The previously retained RuntimeView03 mapped export capture binds the effective AMD64-facing ordinals, avoiding the different raw ARM64 export addresses. Inventory SHA-256 is `6907f9bcf6255b0025193f04a4eb773d8914b1917fe5f169fc0539710fe8df1d`. The complete mapped-export capture SHA-256 is `f7ea2e7ba8bb9db475b41f53d1b5101a7f90e5c80497017f4a1b4c1b183b22e9`.

| Imported ordinal | Effective thunk RVA | ARM64EC body RVA | Selected operation |
| --- | --- | --- | --- |
| `290` | `0x6902f0` | `0x552180` | Construct a wide CString from a narrow input |
| `14039` | `0x6c44f0` | `0x350310` | Remove trailing whitespace |
| `12600` | `0x6beaa0` | `0x37f000` | Right substring with negative length clamped to zero |
| `1501` | `0x694e30` | `0x34a880` | String assignment |

Each 14-byte thunk has the previously bound fast-forward shape and an independently decoded relative target. Seven complete ARM64EC method/helper bodies and two complete import tail thunks are hashed from original bytes with ARM64 exception bounds. The reached conversion uses `MultiByteToWideChar`, and whitespace classification imports `iswspace`. The existing [framework count record](MfcCountArchive2026.md) supplies the shared CHPE/ISA background.

A private decoder view clears only six nonzero export-directory header bytes to work around LLVM's export parser. Body hashes use the unmodified original instruction bytes. Original bytes supply every body hash. No analysis-view identity is attributed to the original or to a loaded module. The existing mapped EAT evidence binds the entry dispatch. Helper-body mapped equality and fresh execution remain open.

## Concrete application enable slot

UI RTTI binds `App_c`, with a direct nonvirtual `SldApp_c` base at displacement zero, to primary table `0x4a7a9460`. Its complete-object locator is `0x4a935538`. Actual slot `+0x550` points to `[0x4a26ba60,0x4a26ba78)`, SHA-256 `f64925241dd770c8675cc8c0d6c97ca4435c7a4db222d3a4adcb4aa6e0b7b8f3`. That body calls `am_GetApp`, then tail-calls the exact export `CAmApp::isEnableDownstreamstreamIds`.

The getter `[0x45813b80,0x45813b87)` returns i32 `actual_CAmApp+0x464`. Its setter `[0x45822320,0x45822327)` stores incoming `EDX` there without Boolean normalization. The spelling with repeated `stream` belongs to the actual getter export. This is runtime application state, not a downstream persisted prefix field.

The selected registration window at `0x49e7f55d..0x49e7f56a` passes static object `0x4aef55c8` to `SldSession_c::setApp`. That object's original primary table word identifies the bound `App_c` table. The complete registration owner is hashed, but unrelated behavior in that owner is not claimed. This proves the concrete static registration route, not that a fresh application was run here.

`SldSession_c::App` returns the pointer stored at `0x319b2938`. `setApp(NULL)` instead stores fallback object `0x319b10e8`, table `0x31998ef8`, whose slot `+0x550` targets the complete three-byte zero-return leaf at `0x31986460`. The selected reset window actually passes null. No live pointer was inspected, and a raw initial pointer is not used as an application startup-state claim.

Under the bound UI registration, the preceding downstream predicate refines to:

`bool(actual_CAmApp.i32_at_0x464 || downstream_dump_option_global_i32_at_0x4db56810)`

When the bound fallback is selected, its application contribution is zero. Construction/configuration of `CAmApp+0x464` and selected runtime flag remain open.

## Remaining work and acceptance

The exact constructor date producer and concrete conditional receiver are **confirmed static** rules. Selected runtime flag value, new helper execution and actual standalone save caller are **partial/unmeasured**. The next save exit remains a source-bound configuration stream creation/context path reaching the direct serializer. No codec or writer changes, tests, saved CAD payload reads, hidden input, VM, CAD, COM, service action or REA/Hopper session occurred.

All fresh native, vendor-loadability, application-usability and held-out acceptance flags remain false/unmeasured. The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) retain both stopping statements: “The first is success under every criterion on this page.” “The second is the end of the available context.” This research checkpoint does not claim CAD completion.
