# Downstream constructor state and enable gate, SOLIDWORKS 2026

The exact native source binds the final constructor prefix and enable predicate. The standalone `-DownstreamIdData` save caller remains open after the scoped search below.

Task `B04-SW2026-DOWNSTREAM-ID-DATA` belongs to `/root/flag_ownership` in PR #121. To close the save question, identify the caller that creates or selects the configuration stream, establishes its store archive and context, and reaches the direct serializer. [Ordinary body grammar](DownstreamIdArchiveGrammar2026.md) · [Standalone read map](DownstreamStandaloneMaps2026.md)

## Exact build and bounds

The accompanying [numeric record](DownstreamConstructorEnable2026.json) contains 11 complete original-PE owners, all chained unwind fragments, 11 reviewed instruction windows and eight selected import identities. Addresses are preferred-image virtual addresses. No vendor instructions or decompiled listings are included.

| Image | Preferred base | SHA-256 |
| --- | --- | --- |
| `sldmodu.dll` | `0x4b140000` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `slduiu.dll` | `0x48ea0000` | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` |

The model constructor is `[0x4b51d470,0x4b51d979)`, 1,289 bytes, SHA-256 `fd224a6416e02509930606bfb89c7838c18f8ee7c039632158b216240ba30f2f`. It installs table `0x4ce16e78`, the actual downstream serializer table established by the preceding grammar record. Incoming `RDX` is the model owner, retained and finally assigned to runtime `+0x6d0`.

## Final constructor prefix

Early stores initialize most words to zero. The complete tail overwrites several of them. Reading only the prefix would yield the wrong final state.

| Runtime member | Initial store | Final rule | Meaning and limit |
| --- | --- | --- | --- |
| `f08` | `1` | `1` | Shared downstream next-ID seed |
| `f0c` | `0` | Current native file-version getter | Calls `moVersionManager_c::get()`, then static `getCurrentFileVerion()` |
| `f10` | `0` | `su_getFullDateCode()` | Imported full-date-code producer. Numeric return and generation rule remain open. |
| `f14` | `0` | `0` | Word meaning remains unclassified |
| `f18` | `0` | `0` | Word meaning remains unclassified |
| `f1c` | `0` | `101` | Exact constructor value. Later meaning remains open. |
| `f20` | `0` | `101` | Exact constructor value. Later meaning remains open. |
| `f28` | Runtime i64 zero | `su_CTime(1990,1,1,0,0,0,-1)` | Local-calendar construction |

The overwrite window is `[0x4b51d8bf,0x4b51d923)`. Stores at `0x4b51d8d2`, `0x4b51d8db`, `0x4b51d8de`, `0x4b51d8e5` and `0x4b51d91f` assign those final prefix values. `getCurrentFileVerion` preserves the spelling of the actual exported name.

Selected other fresh state is an empty native `CString` at `f30`, zero key `f38`, null optional entity-ID vector pointer `f40`, and null begin/end/capacity triples for `f48/f60/f78/f90/fa8`. The owner assignment replaces its earlier null store. The final owner/key registration branch requires both `f38 != 0` and a nonnull owner. The constructor skips that branch with its fresh zero key.

Runtime `f28` is eight bytes, but its existing ordinary archive encoding is **four bytes**. The [clock ownership record](DrawingSourceEpochOwnership2026.md) and preceding downstream grammar distinguish that encoding from runtime storage. Do not emit an i64 or substitute a captured epoch.

These are constructor facts, not populated/save defaults. Topology traversal, updates and reconstruction can change the object after construction.

## Native enable gate

Complete `isEnabled` is `[0x4b535b40,0x4b535b71)`, 49 bytes, SHA-256 `351af361c971572027b60d75e1f3d9175d13cacd382e94d402a687c8b31a9ab9`. Its normalized result is:

`bool(SldSession_c::App()->virtual+0x550() || global_i32[0x4db56810])`

The application call runs first. Its concrete virtual target and semantic name remain unresolved.

Initializer `[0x4b164cd0,0x4b164cec)`, 28 bytes, SHA-256 `ed615a4034514479db25e71abd17e8b807e4822b94ea4cb6d75dea5b152487f0`, assigns that global from `ut_IsDefinedInDumpOpts(L"_ENABLE_DOWNSTREAM_IDS")`. The exact option vocabulary is evidence, not a proposed configuration change. The global lies beyond its section's raw file-backed extent. No raw DWORD or actual runtime flag value is claimed. No application configuration, option, license or process was inspected or changed.

## Caller search and retained boundary

Two selected direct references in `sldmodu` use the exact UTF-16 suffix. They are `0x4b5861db` in the first read owner and `0x4b586416` in the second explicit-configuration read owner. The search found zero exact suffixes in the selected UI image. It checked named downstream imports in the UI, MFC, application, archive, assembly and part modules. Indirect and unresolved ordinal calls remain open.

A model-member byte-pattern search produced ten load sites in eight unwind-backed owners plus the leaf getter. At `0x4b87433e` the apparent candidate loads the receiver's table. It reads table slot `+0x1348` at `0x4b874341` and invokes that virtual method at `0x4b87434e`.

The already bound part/assembly condition-`0x80` branch remains the concrete store-related boundary: enabled, presence determined by the actual downstream pointer and adding-new-configuration state, then direct body serialization without an outer object tag. It does not identify a standalone stream save.

`createOrUpdateDownstreamIdData` at `[0x4b5788b0,0x4b57895c)`, SHA-256 `00c14e9d74fab61e983edf5cc55595f4d513072bd370b6c7538b26f169eeffd6`, checks enabled, lightweight/model state, rollback and the selected model-state branch before creating or updating runtime data. Its dispatch is not an archived-save witness. The bounded UI `isEnabled` caller likewise supplies no independently established standalone save identity.

Negative searches do not prove that the save route is absent. The next exact boundary is the configuration-save owner that obtains the downstream storage/archive and invokes the direct body with known store context and maps. A dedicated disclosed standalone saved control and complete reached-class replay are still required. Existing read-map and grammar deliveries remain unchanged.

## Confidence and acceptance

Original-PE inspection confirmed the constructor assignments, enable predicate, selected import identities and the virtual receiver above. This evidence has zero native runs and zero hidden-input reads. The application slot meaning, standalone save route, loadability, usability and held-out acceptance remain open.

The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) state: “The first is success under every criterion on this page.” “The second is the end of the available context.” This bounded handoff records progress, not CAD completion. The [loader phase](../../Playbook/LoaderAnalysis.md) governs the remaining caller and field work.
