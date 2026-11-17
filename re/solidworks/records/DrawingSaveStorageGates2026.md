# Drawing save storage gate map

## Measured boundary

The matched native debugger trial observed listener aggregate 0 on both the reduced-native and generated blanks. The subsequent matched trial observed EAX 1 for the reduced-native drawing and EAX 0 for the generated drawing at `doccplu+0x16421`. The stop is immediately before the result test after document save dispatch. Seven distinct processes, both pristine brackets, native save and fresh reopen, source immutability and debugger detach passed. The generated lane still emitted only event 7, returned `[false,1,0]` and left a zero-byte target. The JSON pins exact receipt and module digests.

The observation places the failure within the dispatched document save or its descendants. A successful event-listener result has already been measured. The exact failing storage instruction and the archive field responsible remain open.

## Storage construction and allocation

The ordinary shared UI base save selects the storage object through the holder at `uiBaseDoc_c+0x4a8` and its slot `+8`. The presence gate at `sldappu!0x458e7322` precedes storage slot `+0x10` at `0x458e7333`. Both the concrete `SolidStorage_c` and `SolidStorageMFC_c` vtables resolve this slot to `doccplu!SolidStorageBase_c::saveDoc` at `+0x1b810`.

The path split at `doccplu+0x1b89a` calls `sldmfcu!findFileFromEmbeddedName` at `0x3c8bfef0`. It produces the physical filename and an optional embedded-name component. Later backend branches use those derived names. Matching the COM path alone does not identify which internal path branch executed.

The structured path checks existence at `doccplu+0x1c1a4`, then calls `suFileLockBytes::Init` or `Create` at `+0x1c1bf/+0x1c1c6`. The raw HRESULT is available at `+0x1c1cb`. The caller advances without immediately testing it. `suFileLockBytes::Create` calls `CreateFileW` at `sldmfcu!0x3c7f2b53` with create disposition 2, then stores the file handle at `this+0x38`. This can allocate an empty file before root storage exists.

The structured root factory `StgCreateDocfileOnILockBytes` is called at `doccplu+0x1c1fd`. Its final raw HRESULT is tested at `+0x1c225`. A nonzero value reaches the throw helper through `+0x1d04c`. Success installs the root through slot `+0x88` at `+0x1c23b` and binds lock bytes through `+0xc8` at `+0x1c24a`. A separate branch has its own lock-byte status at `+0x1c36d`. The ZIP construction branches also create lock bytes and construct `ZipStorage` at `+0x1c537`. The generated lane's selected backend remains unmeasured.

Both ordinary calls from `saveDoc` to `SaveToStorage`, at `+0x1c64e/+0x1c669`, set EDX to zero. Accordingly, the nonnull CObject argument branch inside `SaveToStorage` cannot bypass root wrapping under either call.

## Root validity and callback sequence

The root wrapper factory is called at `doccplu+0x1d9dc`. RCX is the selected IStorage and R8 the selected ZipStorage. Their presence alone can be sampled if the validity result requires follow-up. `sldmfcu!suFileStorage::createStorage` at `0x3c8b57a0` chooses nonnull IStorage first, then ZIP, then its backend-free base. A nonnull wrapper does not guarantee valid backing storage.

At `doccplu+0x1da03`, EAX is the typed `isValid` virtual result. Structured and ZIP implementations test their live root at `this+0x80` through `sldmfcu!0x3c763c70`. The backend-free base at `0x3c7509d0` returns zero. Zero at the instruction reaches the error helper and throw of `0x80004005`. A valid root advances through the normal preamble, including `writeVersion` and `SaveDisplayName`, before the callback-eligibility gates.

The exact later getter result sites are `doccplu+0x1dd1b` and `+0x1dd2b`. They test `getSaveDisplayListOnly` and `getSaveOnlyQuickViewData`, backed by `uiBaseDoc_c+0x3dc/+0x3e0`. A nonzero result skips the ordinary properties and third-party block and continues at `+0x1e173`. That branch alone does not establish the observed failure.

`SaveDocumentProperties` at `+0x1df56` and three `saveUiXMLToStorage` calls at `+0x1df83/+0x1df95/+0x1dfa7` precede the third-party virtual dispatch at `+0x1dfb5`. Their return values are discarded. A zero return from one of those calls alone does not skip the third-party call. An exception in the interval remains a distinct candidate.

## Discriminating experiments

The prepared private storage deck reuses the qualified debugger engine and all original inputs. It observes the aggregate, then replaces the breakpoint with `+0x1b810` entry, then with `+0x1da03` validity, within the same save. The reduced native lane must observe both sites and save/reopen cleanly before the generated lane runs. The root-owned normalized 02 deck is the execution packet. Historical 01 remains immutable.

| New observation | Smallest follow-up |
| --- | --- |
| Generated storage entry observed, validity zero | Sample only backing IStorage and ZIP presence at `+0x1d9dc` in a matched repeat. |
| Generated storage entry observed, validity unobserved | Sample `SaveToStorage` entry at `+0x1d750` to separate root setup from its version/history preamble. On an independently confirmed structured path, sample raw HRESULT at `+0x1c225`. |
| Generated storage entry unobserved | Split the document-specific save path with the drawing's ordinary shared-save result at `slddrwu!0x3defcdc1` and the shared UI base-save return at `slduiu!0x49725c13`. Both calls have typed EAX results. The normal branch is still qualified by the control first. |
| Generated validity nonzero | Observe the two preview-only getter results in execution order at `+0x1dd1b/+0x1dd2b`. If both zero, observe presence of `+0x1dfb5` to bound the intervening XML/property work. |

The drawing override in slot `+0x3080` is `slddrwu!0x3defb790`. Its ordinary shared-save call is at `0x3defcdbb` and the typed result is ready at `0x3defcdc1`. Shared `uiModelDoc_c::saveDocument` checks the existing path at `this+0x2f8`; its helper result is tested at `slduiu!0x49725a8c` before the UI base save. The base save return is ready at `0x49725c13`. These are fallback observation sites if the storage entry is unobserved. No current measurement assigns the failure to those earlier gates.

Each follow-up retains the same owned oracle identity, pinned module, COM call, path, passive brackets, native control and debugger cleanup. Distinguish an exact observed stop, a save completed with a stop unobserved, and an instrumentation failure.

## Measured storage route

The normalized paired storage run observes both storage save entries at
`+0x1b810` and both EAX values of 1 at root validity `+0x1da03`.
Both stops retain the original save thread and a nested frame. The
generated drawing still returns error 1 after event 7 with a zero-byte
target. All three native reference lanes save and reopen, both
debuggers detach cleanly and all seven process identities differ.

The measured generated route has a valid storage root. The next
paired run samples the later preview-only getters and third-party
call entry to bound the intervening preamble.
[Storage entry and validity receipt](../measurements/2026/DrawingBlankSaveStorageGateNative01.json)

The next native attempt observed zero from both preview-only
getters on both traced inputs. The generated save then returned
after the armed third-party stop was unobserved. Cleanup failed its
explicit removal check with HRESULT `0x8000ffff`. Final debugger
absence was measured. Both brackets passed. The full comparison
remains failed pending a qualified repeat.
[Preview attempt](../measurements/2026/DrawingBlankSavePreviewGateNative01.json)

The properties-gate repeat qualifies its cleanup independently by
owned engine-process selection and original instruction byte
checks. Both lanes explicitly remove their breakpoints, restore
all armed bytes and verify debugger absence. The reduced-native
lane reaches both the post-properties site and third-party
dispatch. The generated save returns with the post-properties
site armed and no delivered stop. This preserves the next split
at the call instruction `+0x1df56`.
[Properties comparison](../measurements/2026/DrawingBlankSavePropertiesGateNative01.json)

The next seven-process comparison delivered `+0x1df56` on both traced
lanes. The reduced-native lane delivered its same-frame return at
`+0x1df5b`, saved and reopened. The generated save completed with
error 1 while that return site was armed and unobserved. Both lanes
explicitly removed all breakpoints, verified original instruction
bytes after detach and measured debugger absence. The document
properties call interval is the next loader-analysis boundary.
[Call-entry comparison](../measurements/2026/DrawingBlankSavePropertiesEntryNative01.json)
