# Blank drawing save after FileSaveAsNotify

The generated blank produced event 7 and returned `[false, 1, 0]` from `SaveAs3`, leaving a zero-byte target. The three native lanes produced `[7, 9, 28]`, saved and reopened cleanly. All four lanes opened and rebuilt cleanly with ten tree rows. The runners used the same physical paths, seven fresh processes and immutable inputs. Native sheets used 1:1 scale and the generated sheet used 2:3. The measured reach ends at the event 7 callback inside `iDoSave`. [Native receipt](../measurements/2026/DrawingBlankSaveEventsNative01.json) · [Event observer](DrawingSaveEvents2026.md)

## Pinned native path

The accompanying JSON binds the analyzed AMD64 modules to SOLIDWORKS 2026 SP05.2, the measured `sldworks.exe` identity, the packet, the original observer, the raw receipt and its corrected evaluation. Addresses below are preferred PE virtual addresses. The JSON includes function extents from PE unwind records where present. [Machine-readable branch map](DrawingSavePostEventBranches2026.json)

| Stage | Pinned branch and source rule |
| --- | --- |
| Early save event | `doccplu!SolidStorage_c::iDoSave` calls document slot `+0x29e8` at `0x1800158bc`. The drawing vtable routes it to `slddrwu!0x3ded6100`, which uses the automation owner at `uiDrawingDoc_c+0x1778` and emits ordinal 7 at `0x3ddad303`. The automation vtable routes `FireEvent` to `slduiu!auModelDoc_c::iFireEventV`. The ordinary listener loop accumulates nonzero results at `0x492b03d7–0x492b03e0`. `iDoSave` stores the returned aggregate at `0x1800158d5`; a nonzero value at `0x180015966–0x18001596e` reaches cleanup and returns zero at `0x18001836a`. The observer's listener returned zero. The aggregate remains unmeasured. |
| Ordinary drawing dispatch | The zero-aggregate route bypasses the `prtdot`, `asmdot`, `drwdot` and `lytdot` checks at `0x1800159f1–0x180015a4f` for the matched `.SLDDRW` target. The document dispatch at `0x18001641f` calls `slduiu!uiModelDoc_c::OnSaveDocument`. Its native drawing edge through `+0x3080` at `0x496fdce0` reaches `slddrwu!0x3defb790`. This drawing fallback calls `uiModelDoc_c::saveDocument` at `0x3defcdbb`. The sheet-format `.slddrt` edge at `0x496fdc8a` checks the active sheet profile and belongs to a separate export route. |
| Document state and storage setup | `saveDocument` calls the original-path helper at `0x49725a87` when the live `OriginalFilePath` at `uiBaseDoc_c+0x2f8` is populated. The helper proceeds if the target differs from both live and original paths. Its original-document reopen can fail when either stored path matches the target. At `0x49725c0d`, `saveDocument` calls `sldappu!uiBaseDoc_c::OnSaveDocument`. The base requires a resolved storage pointer at `0x458e7322` and calls slot `+0x10` at `0x458e7333`. The target-opening and creation failures in `doccplu!SolidStorageBase_c::saveDoc` can throw before its `SaveToStorage` calls at `0x18001c64e` and `0x18001c669`. |
| Storage validity | Ordinary `SaveToStorage` wraps the destination IStorage or ZIP root at `0x18001d9dc` and calls `suFileStorage::isValid` at `0x18001d9fd`. A false result at `0x18001da05` raises a storage error through `0x18001e930`. The structured-storage and ZIP implementations test their live root pointer at `+0x80` in `sldmfcu!0x3c763c70`. The backend-free base returns zero at `0x3c7509d0`. |
| Callback eligibility | In `SaveToStorage`, a nonzero `getSaveDisplayListOnly` at `0x18001dd1d` or `getSaveOnlyQuickViewData` at `0x18001dd2d` jumps over properties and the third-party save to `0x18001e173`. The getters read live `uiBaseDoc_c+0x3dc` and `+0x3e0`, respectively. The ordinary `SaveDocumentProperties` call at `0x18001df56` discards its return and precedes the third-party call at `0x18001dfb5`. |
| Storage events | `Save3rdPartyData` can return before dispatch when the application current and final format versions differ and the previous-release feature is disabled (`0x18001f0d7–0x18001f0ea`). Both version values default to 19000 in this build. The runtime autosave field at `uiBaseDoc_c+0x3d0` selects ordinals 11 and 48 at `0x18001f444` and `0x18001f490` in place of normal 9 and 28. A `ThirdPty` substorage failure at `0x18001f2eb` skips the first notification and still reaches the store notification. |

The initial callback trace left the event aggregate, original path, destination storage pointer, preview modes and autosave state unmeasured for the generated lane. The subsequent matched software trace measures the event aggregate as zero in both the generated and reduced-native lane. The generated lane still produces event 7, error 1 and a zero-byte target. The downstream document dispatch, Definition serialization and commit entry remain to be located in the failing run. [Earlier save return edges](DrawingContainerSaveFraming2026.md#shared-save-return-edges) · [Matched native trace](../measurements/2026/DrawingBlankSaveAggregateSoftwareMatchedNative01.json)

### Exact software trace sites

REA with Hopper reproduced the instruction boundaries on the same
`doccplu.dll` hash. The new reduced-native software control measures the
aggregate at `0x180015966` as zero and completes native save and fresh
reopen. [Native software control](../measurements/2026/DrawingBlankSaveAggregateSoftwareNative01.json)

| Preferred address | State at the instruction |
| --- | --- |
| `0x180016421` | EAX holds the document save dispatch return from `0x18001641f`. The test at this address separates the zero path from the jump to `0x1800167ad`. |
| `0x18001da03` | EAX holds the storage virtual validity result. Zero jumps to the storage error at `0x18001e930`. |
| `0x18001dd1b`, `0x18001dd2b` | EAX holds each preview-only getter result immediately before its test. |
| `0x18001dfa7`, `0x18001dfb5` | The UI XML stream call precedes third-party dispatch within the ordinary storage path. |

`saveDoc` separates the file lock-bytes creation call at `0x18001c1c6`
from structured-storage creation at `0x18001c1fd`. That storage call
retries only result `0x80030002`, up to three total attempts. Other
nonzero returns go to the failure handling before the SaveToStorage
calls. A separate destination bind tests the lock-bytes result at
`0x18001c36d`. These are static branches. The generated route and its
return values require native measurement.

REA instruction evidence `ev_3fd0415507a116177b1c456b796654bb0deec89447362f1ddbc5fb35fd05c002`,
`ev_967a5dadd74a76025b8dd80caf3ef8d56d1777415b898d12e586db24c8c05c63`
and `ev_fb7a567011325cc2fd03c6dc0d0b3430417e4f35f2724e57f26d581d149fb793`
use module SHA-256 `ad0c266a966381defe9a68c11b76dc318acc6a9f6ac428d5aa253049df87ddd8`.

## Smallest follow-up

Reuse the four disclosed matched lanes and the checked type-library binding. Log `AutoSaveToStorageNotify` and `AutoSaveToStorageStoreNotify` if the pinned drawing source exposes them, with the existing four callback handlers. An observed 11 or 48 would prove entry to the alternate storage notification path. Capture the target's existence and size before save, at event 7 and after return. Read the visible path and dirty state through `GetPathName` and `GetSaveFlag` before the call. Keep callbacks free of COM calls and preserve the native controls and fresh-process checks.

One additional reduced-native lane can calibrate explicit veto by returning 1 from event 7. Compare event sequence, status and target existence and size with the generated failure. A different footprint distinguishes the observed failure from the calibrated veto. A matching footprint still permits several branches.

The repository records use of `cdbX64.exe` for older SOLIDWORKS instrumentation. Its availability on the current oracle remains to be verified. If it is available and supports the emulated AMD64 context, attach to the approved COM-created process and log four execution stops. Read the final event aggregate from the stack at `doccplu+0x15966`, the document result at `+0x16421`, destination validity at `+0x1da03`, and entry to the third-party call with the autosave field at `+0x1dfb5`. Start both healthy controls and the generated lane through the existing COM calls. Use read-only observations and hardware execution stops. The earlier debugger wrapper launches the application and sweeps process names, so the COM runner owns startup and cleanup for this repeat. [Prior debugger setup](../archive/Windbg.md) · [Legacy launch wrapper](../../tooling/windbg/Cdbdrive.py)
