# Ordinary part rebuild-warning publication, SOLIDWORKS 2026

Task `B04-SW2026-ORDINARY-PART-PARTITION-LOAD`, warning-publication subtask; owner `flag_ownership`; delivery PR #121. Root owns the VM, diagnostic processes and integration. This is a bounded source checkpoint, not a writer change or native acceptance. The [numeric ledger](PartRebuildWarning2026.json) binds five exact original images, 24 complete function entries, eight instruction windows, six data ranges, six virtual cells and 22 imports. The [source receipt](../measurements/2026/PartRebuildWarningSource01.json) records the passing independent file-byte replay. No proprietary code/listing is included.

## The measured warning comes through the load-error lane

`auAm_c::apiOpenDoc` is `[0x458a1ff0,0x458a42c5)`, SHA-256 `7ec79022168a37364c59b2eb8a73b2f71b9bda09ca6e4f08ea7780d8266b36c7`. The first non-`this` API long argument is saved from entry `edx`; this is not the archive version. At `0x458a3c9d`, values at least 5 enable translation of older internal load errors into the warning accumulator.

The original selector table `[0x458a4248,0x458a42c5)` and RVA table `[0x458a422c,0x458a4248)` prove that **internal load error 128 uniquely reaches `0x458a3cf2`, which ORs warning bit 32**. Actual `appApiFileLoadWarning_c` records are ORed afterward, separately. At `0x458a3ddf`, the accumulated warning is written through the actual output pointer. Therefore a probe of only `addApiFileWarning(32)` can miss the actual producer. [Specific warning-source gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/RebuildWarningCanOriginateFromLoadError.md)

The independently rehashed `ApiWarningBoundary01.json`, SHA-256 `54ac38cb1f9589f771cbcbddcd263988856e56834c7b95adaff37926fece165c`, records internal 128 at actual `auAm_c::addApiFileError`, with caller `sldprtu` RVA `0xf21e9`. Preferred base `0x332a0000` gives return VA `0x333921e9`. This is the separate part helper below. Its intervention ended with a COM/controller failure; the captured call is not a successful open or proof that the candidate itself crashes.

## Actual part configuration decision

Actual `uiPartDoc_c` primary table `0x3349e068`, slot `+0xde8`, points to complete `[0x33391b20,0x3339255d)`, SHA-256 `ed1b5f35b209615c27673f810d4e426fdc089c58b54f90d00b3cef588fb48ab3`. Actual `uiModelDoc_c` base table `0x4a645b78` binds the same slot through thunk `0x4a31adc5`, IAT `0x4a467308`, to the exact imported symbol `uiBaseDoc_c::iiConfigureMAIN(int,int,int&,int&,int,moUpdateEngine_c*)`. The preceding LLVM label `iRestoreDisplayListsMultipleConfigs` does not name this separate function.

For the source arm ending at the measured call:

1. `uiEnvironment_c::getPaletteDrag()` is zero. Its direct getter binds runtime environment `+0xe4`. The actual part is not shrink-wrap. Other earlier mode/version/configuration branches still apply.
2. The actual part's virtual `+0xc0` is called at `0x3339215c`, with the original second integer argument as its flag.
3. A nonzero result enters the API/server refusal decision. Otherwise, entry requires that flag to be nonzero **and** `moNode_c::isUpdateError(part)` to be nonzero. The latter leaf `[0x4c03e570,0x4c03e577)` reads `part.f0c & 0x2`.
4. A present actual `auAm+0x388 != 0`, or `CAmApp::_runAsServer() != 0`, selects local result 7. If the actual `auAm` exists, `0x333921e3` publishes internal error 128, then rejoins its configuration loop.

The complete override calls neither `askToRegen` nor `getAskRegen`. Those methods form a separate warning-producing path and must not replace this measured owner.

At the helper's measured return address `0x333921e9`, `rbx` is its actual document receiver, `r12d` the saved original entry `r8d`, `rdi` the selected result 7, and `r15` the actual API object. Its established frame has `rbp = rsp + 0x100`; the saved flag is `i32[rbp+0x460]`. Those are read domains, not values to inject.

## Part flags and configuration state remain distinct

Actual part virtual `+0xc0` points to `[0x4c1b8a60,0x4c1b8b37)`, SHA-256 `263205bf5f0e534cc1c0a55ede4d42cb5a6ef2923ed5be24e5887e04e06638dd`. If runtime part `+0x2b4` is nonzero, the selected cached-update branch reads `part+0x2b8 & 0x1`. Otherwise it calls `moNode::needsUpdate`, which tests `f0c & 0x1`; argument 1 also queries actual part virtual `+0x168`. That concrete secondary function checks frozen/model-context conditions and the external-context update collector. Dependent-derived-part routes remain separate. No direct header `f44` or body-timestamp comparison occurs in the complete `+0xc0` body.

This does not identify the serialized producer or legal fresh value of runtime `+0x2b4/+0x2b8`. Neither is supplied as a new writer default.

`moBaseConfiguration::needsRebuild` separately uses configuration `f0c & 0x8`, its `+0x968` override and current-configuration state. Its `getUpdateStatus` also consults actual part need-update, update-error, and transient part `+0xd3c`. The ordinary loader can set that last flag under conditional null/count/kernel/rollback gates at `0x4c23f2e3..0x4c23f345`; zero public bodies alone does not prove that assignment occurred. The two flag masks and the public warning are not interchangeable.

## Separate rebuild policy and notification ownership

`uiModelDoc::askToRegen`, `[0x4976d9e0,0x4976db15)`, SHA-256 `4f30db9c34fc32d337697a32740ee832d3f2c8612a89e5087fa3d06327920360`, first calls `getAskRegen(true)`. Result 2 exits. Otherwise an actual API object with `+0x388 != 0` publishes internal 128 and bypasses that method's later regeneration dispatch. The non-API branch separately considers playback, regression, policy and dialog response.

`getAskRegen`, `[0x45a295a0,0x45a2961b)`, SHA-256 `ded4ba1a7c57717b001d1ffc683c591fa890f459f51a334ef78f4338df2d2648`, first reads cached registry `+0x604`; nonzero returns 0. It then queries the actual dont-ask option named `MSG_NEEDS_UPDATE_ON_OPEN`. Its source initializer supplies constructor arguments 1 and `0x2a14`, but those arguments do not establish the current option-map value. `equals(-1,false)` returns 0; otherwise it samples `value(false)`, requesting `value(true)` only when the caller requested true and that first value was nonzero.

The boolean controls a real notification path. `value(bool)` calls `suSolidworksDAApOptions::hasValue`, which reads its case-insensitive option map. With notification enabled, a value other than -1 and a valid reached frame, it synchronously invokes `SendMessageW(0x8160,0,option-name-text)`. A matching original message-map entry selects `0x45a9cd20`; that reviewed body appends a unique text value to its receiver's vector and invalidates/updates a window. The actual live receiver join remains conditional. No direct debugger-presence API occurs in these reviewed bodies, but cached registry writers and wider caller/notification context remain unclosed. [Notification gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/RebuildPolicyReadCanSendUiNotifications.md)

## Received geometry versus atom publication

The independent `KernelAskBodiesBoundary01.json`, SHA-256 `a3add91a7e7080cb48bfd56d2774f9341e36fe3e96cd0901e53b9b84613c36b5`, captures kernel status 0, count 1 and a present returned body-tag array. The **same invocation** completes with warning 32 and zero public bodies. Its controller diagnostics are empty. Thus an accepted kernel body inventory can coexist with the failed application-level initial body inventory. A blanket receive-failure explanation is insufficient for that observed run.

The separate ordinary `getBodies` stop returned 1 at `0x4c23edeb`, but that process later failed its COM/controller lifecycle. Preserve its actual sample and failed completion together. `AdmissionMatrix01.json`, SHA-256 `f70156b289191f3aae426ba9d9785f9e765bbb23fcafdc27d179708ef21950f5`, retains all four uninstrumented cold/warm and read-only/writable warning-32, zero-body cases, with two healthy controls and no rebuild/save calls. The earlier receive-return breakpoint case opened cleanly with one body. None makes debugger attachment, read-only mode, warm-up, timing or a saved field a universal cause or remedy.

The earliest unresolved application boundary is actual `replaceBody` feature/atom publication. Its selected positive-body-ID branch resolves the actual atom manager ID, then requires that atom to occur in the candidate feature's actual output array. Record the actual feature identity alongside each array result; an earlier unrelated feature's empty array is not the boss's result. `replaceBody` and `moAtom::setBody` return void. There are separate direct output-atom `+0x180` and alternate-setter paths. [Immutable ordinary-loader proof](OrdinaryPartPartitionLoad2026.md)

The minimum next observation is the actual `+0xc0` return and its incoming flag at `0x3339215f`, or the update-error fallback return at `0x3339217d`, tied to the actual part; combine that with the positive-ID atom lookup/output-membership boundary if it is reached. Source counters, mark identities, declared body counts and the actual runtime fields must retain their distinct owners. No payload change or preference change is proposed.

## Scope

Source replay verifies original PE identities, complete declared unwind groups, retained instruction/data ranges, import names and virtual cells. Corrected metadata uses explicit hexadecimal masks and includes both unchanged prior complete loader/publication parent records. The initial source inspection's missing leaf extent and command-argument mistakes did not execute a product or create native evidence; the exploratory padded body-getter interval is excluded from this delivery.

All work used original-image file reads, authored source inspection and the exact disclosed data-only reports. No VM, CAD/COM, schema/codec, tests, hidden inputs, shared mutations, or REA/Hopper sessions were used. Current-source counterpart hashes are retained without executing them. These are partial source rules, not a whole-source conversion or native/held-out qualification. The CAD criteria's success-under-every-criterion and end-of-available-context stopping conditions remain in force.
