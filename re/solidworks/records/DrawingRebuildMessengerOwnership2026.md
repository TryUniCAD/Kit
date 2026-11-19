# Drawing rebuild messenger ownership, SOLIDWORKS 2026

The ordinary drawing rebuild source reaches a session messenger virtual callback. Sixteen read-only snapshots across four fresh processes identify the same installed target for native and generated drawings. The rendering defect remains open.

Task: DRAWING-NOTES-C10, PR #121. Owner: `flag_ownership`; root owns the native oracle, integration and publication. Dependencies are the disclosed plain-note controls, exact 2026 modules and the unchanged owned COM lifecycle. The exit condition for this observer is four healthy distinct owned processes with exact session identity and complete pointer ownership observations before and after rebuilding. Finding a matching target does not close the rendering defect.

## Source-bound aperture

All addresses below are preferred VAs, tied to the full module hashes in [the numeric source record](DrawingRebuildMessengerOwnershipNative2026.json). The target is AMD64 SOLIDWORKS 2026 SP05.2, file-version words `34,5,2,604`.

| Boundary | Exact rule |
| --- | --- |
| Public ForceRebuild3 wrapper | `sldappu [0x45677c30,0x45677d1b)` delegates virtual `+0x1660` |
| Actual model dispatch | `slduiu [0x491c1700,0x491c17e9)` reaches primary drawing virtual `+0x230` |
| Drawing delegate | `slddrwu [0x3df9c900,0x3df9ca39)` reaches `[0x3df423b0,0x3df429fb)` on the ordinary branch |
| Ordinary caller selection | At `0x3df427d1`, `R8D=1`, `R9D=1`; the callee `[0x3df436d0,0x3df43f2d)` retains incoming `R9D` in `R12D` |
| Graphics callback | With `R12D != 0`, `0x3df43e81` calls the actual `SldSession_c::SldGrMessenger` import; `0x3df43e8d` invokes its returned object's virtual slot `+0x10` |
| Session leaf | Export `?SldGrMessenger@SldSession_c@@SAPEAVSldGrMessenger_c@@XZ`, `[0x3198a1d0,0x3198a1d8)`, RVA `0xa1d0` |
| Session image | SHA-256 `c53d42d0b7bcfd9abf78cfd71ca6f71645cb8da16ea29c155f63172eaa17f421`, preferred base `0x31980000`, 229464 file bytes |
| Runtime pointer cell | Loaded getter VA plus `7 + signed rel32 at getter+3` gives loaded session base plus `0x32a30` |
| Setter/default distinction | Setter `[0x3198a9d0,0x3198a9e6)` publishes the supplied nonnull pointer, or selects session object RVA `0x31028` for null input |

The separate `R12D == 0` branch uses a detail-items interface and slot `+0x30`. Palette/task-pane callbacks elsewhere in the function are separate owners. The observer does not infer the target module from these neighboring paths, and it leaves every native application guard intact.

## Read-only observation method

`InspectMessengerOwnership.py` opens four fresh drawings through the existing versioned COM controller: pristine control, disclosed native note source, the exact existing grid-off-both generated candidate, pristine control. Each input is opened read-only. The observer records the ordered sheet/tree/note state and document preference switches with the prior unchanged helpers.

Four pointer snapshots are taken per process: after open, immediately before `ForceRebuild3(False)`, immediately after it returns, and after `GraphicsRedraw2`. The observer verifies the on-disk session hash, exact export RVA, complete getter-body hash and the matching eight live getter bytes. It reads the global pointer, vtable and slot `+0x10`, then rereads those three pointer cells. Unstable or inaccessible reads fail closed and preserve partial metadata.

The new process handle requests only `0x410`, `PROCESS_QUERY_INFORMATION | PROCESS_VM_READ`. PID ownership and creation FILETIME are checked against the existing controller's retained lifetime identity before reading. No debug attachment, breakpoints, remote calls, memory writes, privilege adjustment or termination rights are used. This follows the documented [ReadProcessMemory rights and bounded-read contract](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-readprocessmemory) and [GetModuleInformation access rights](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getmoduleinformation). The unchanged COM controller separately retains its existing synchronization handle.

The target must fall in one uniquely loaded module's executable section. The report preserves its actual module path/name, loaded base, target RVA, machine, version and complete on-disk digest. It also resolves the vtable owner. The module disk digest is not a hash of remote executable contents. The pointer reads are sequential, not atomic, and observing the registered callback does not prove that it executed.

## Scope and custody

The preparation receipt binds the exact 18-file private packet. It contains 11 Python tools: two new independently authored observers and nine byte-identical established helpers. The three input CAD files remain private and are copied without changing any byte. The original basename `Disclosed01.SLDDRW` is retained for both note drawings in separate directories.

The active observer calls no save, bitmap-export, text-insertion, text-edit or settings-write API. It closes only its own drawing without saving, exits only its task-owned application and closes its own query/read handle. It writes observer JSON only. Existing helper modules contain other authoring entrypoints which this method does not invoke.

The previous disclosed memory diagnostic remains immutable, SHA-256 `9857530b8c2eccb14f567a107381edd6556736bef7812b11be22f3f69922d5f1`: native source and pristine controls retained raster changes, while the generated candidate lost them after rebuild. This packet performs no new raster measurement and does not change that result. Neither target equality nor a stable messenger pointer is treated as a rendering pass.

Local verification is limited to static AST parsing, file/hash reconciliation and original PE metadata. No Windows or CAD execution, local tests, sealed-input reads, shared edits or new Hopper sessions occurred. The root-owned runtime observation is recorded below. See [the change entry](../../../Documentation/Changes/Solidworks/Inspection/Drawings/Notes/DrawingRebuildMessengerObserver.md).

## Static replay and corrected metadata

The original PE replay passed four image pins, seven complete-function spans, two instruction windows, one import and two vtable cells. Verifier SHA-256 is `8580bf461e0d2c146f5b93414b991c1d466d9f77a6acc36c08f12cbcbb318fa9`. Packet01 stopped during static provenance replay because its correctly attributed sldappu function had no module-list pin. Packet02 corrects only that metadata and preserves both observer sources exactly. The first packet and failure receipt remain immutable. Neither attempt ran Windows or CAD.

## Actual installed target

The [read-only receipt](../measurements/2026/DrawingRebuildMessengerOwnership01.json) passes all four independent guest processes with two healthy pristine brackets and no file or preference changes. In all sixteen snapshots the registered target is `sldgraphicsuiu.dll` at RVA `0xd1e40` and its owner vtable is at RVA `0x166c40`. The three pointer cells remain stable on reread in every snapshot. The native source and generated drawing therefore select the same registered target before and after rebuild. The measurement observes pointer ownership and leaves actual invocation and document-specific work to the callback trace.

The complete module digest is `3948ce26833d053f9d4d0a8b4f8b1b9ed90662f4324aca2f4d002c7f3166edbf` for 2,071,128 on-disk AMD64 bytes. The read-only acquisition verified that exact identity on guest and host. Licensed images remain outside the checkout. Raw observation SHA-256 `2753a8d3fe258179119f13911d44a848511d468f9eda972549c39535cedefc2b`.
