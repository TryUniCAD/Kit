# SOLIDWORKS 2026 ordinary atom-manager body enumeration

Cold body admission remains unqualified. The root reports that the authored-light comparisons now open without warning32, but still expose zero bodies before rebuild and one afterward. This checkpoint explains the actual body query and its separate ownership domains; it does not identify a measured failing predicate or change a writer.

Task `B04-SW2026-ORDINARY-PART-PARTITION-LOAD`, owner `/root/flag_ownership`, delivery PR #121. The root owns native execution and integration. The worker read original pinned PE images, source and prior format knowledge only. No VM, CAD/COM, hidden payload, codec, schema, product process or test was executed, and no shared file changed. The CAD success criteria and full RE playbook govern this work.

The [numeric record](AtomManagerBodyEnumeration2026.json) pins `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`, version `34.5.2.0604`. It contains complete exception groups, independently decoded instruction windows, RTTI, imports and concrete vtable cells. Conclusions below are source-backed partial rules; the exact failing cold-open operands still need a same-invocation observation.

## The reached ordinary manager branch

The concrete `moPart_c` vtable `0x4d1252d8`, slot `+0x12a0`, selects `[0x4c1ab900,0x4c1abaed)`, SHA-256 `21acecd307dbc284a5968c903ff995bf84f73728cf8737e5aa3153ccc9b60ccf`.

This part getter can first return an existing keyed body cache, a reached `part+0xea8` object's body array, or the separate ordered-solid-body cache at `0x4b53e220`. A missed atom-manager stop therefore does not prove an empty manager.

The fallback at `0x4c1aba65` calls the exported `moAtomManager_c::getBodies` with actual manager `part+0xd88`, actual output array, live visibility enum, body-type enum3, actual feature argument, flags1, ID-types0, and the part getter's final integer argument. Enum3 selects the actual solid-body test, not an assumed public COM enumeration value.

The public manager body is `[0x4bcf3170,0x4bcf400b)`, 3739 bytes, SHA-256 `bebe8def5dbd1c17812d14ab079eb88b508f26935488210ea675e10b1df0f121`. ID-types0 selects the complete internal helper `[0x4bcf4010,0x4bcf4e8a)`, 3706 bytes, SHA-256 `5024ebfe970383151c57fb42a85ff9099ea4ba6f831cb8dfd4b6110351f8afd9`. It clears bit2 of the flags argument and forwards the actual feature and final integer limit. It ignores the helper's `EAX`: the exported count is final output-array count minus its entry count at `0x4bcf31ec`.

## Cache, viewer and ordinary atom paths differ

The helper reads actual manager `+0x258`, checks its concrete part class, and uses manager `+0xa0` when the incoming feature is null. Its body-cache shortcut requires `SldDocMan::getEnableGetBodiesCache`, compatible current owner/feature mode, manager `+0xac==0`, and the selected valid-cache flag. These flags and maps are runtime state, not archive defaults.

For visibility0 and solid type3, a valid flag at manager `+0x120` can return the cache at `+0x128/+0x178` before ordinary atom iteration. An empty valid cache and an empty atom map are different observations. The flags at `+0xb8/+0x120/+0x188/+0x1f0` are initialized clear by the manager constructor and cleared by `cleanUpCachedBodyMaps`; `moAtom_c::setBody` reaches `updateCachedBodyMaps` before publishing its new body pointer. This does not prove which cache state exists in a particular open.

Actual part slot `+0x1250` is `moModel_c::isViewerModel`, `[0x4c02d7d0,0x4c02d7ef)`. With the helper's `EDX=0`, it returns whether runtime `model+0x2b0` mask4 is clear. A true result, or true `isShrinkWrap`, takes the adjunct-body route instead of the normal atom tree. The owner-taking model constructor writes `0x0c` to the low word at runtime `+0x2b0`, so this predicate is normally false immediately after that constructor. Later load/runtime mutations remain separate. This runtime word must not be confused with a feature schema's `f2b0` file-version field.

## Normal iteration and filters

| Stage | Actual rule |
| --- | --- |
| Key order | Traverse the signed-key tree whose head is manager `+0x88` and size is `+0x90`; key is each tree node's `+0x1c` |
| Alias lookup | Sign-extend that key and call `su_CMapPtrToPtr::Lookup` on manager `+0x58` |
| Atom eligibility | Skip null atom or nonzero atom `+0x144` |
| Visibility | Enum0 bypasses visibility filtering; nonzero enums use actual body/feature/config state and atom `+0x170` |
| Feature range | A nonnull selected feature can exclude atoms by actual owning-feature order, output membership or `Concept::isBefore` |
| Body | Read atom `+0x160`; a null selected body skips the atom, with explicit in-progress/override branches retained |
| Body kind | Solid type3 requires `isSolid(body,1,0)`, with a separately reached general-body exception; the selected body must also pass actual `gcEnt::isValid` |
| Body identity | If actual owner `+0xf50` is null, normal valid body identity must agree with atom `+0x140`; the separate dimensional-pattern branch remains conditional |
| Publication | Eligible atoms enter a temporary array; their actual nonnull bodies are later appended to the output array |

The actual atom-ID getter can materialize its pointer mirror. Observe an existing call's result instead of calling it again; see [the getter gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/AtomIdGetterMaterializesPointerMirror.md) and [body-to-atom selection](PartBodyAtomBinding2026.md). Neither the body value nor an atom ID establishes that the value is a dereferenceable heap pointer.

## Current reload creates both indexes and restores the owner

The version19000 path is not the older monolithic `moModel_c::Serialize` arm. That entry dispatches version `>=0xc7d` through actual slots `+0x4b8/+0x4c0` and returns. For `moPart_c`, `+0x4c0` is `0x4c2378b0`, which calls base model resolved body `0x4c234150` at `0x4c2378fa`.

The complete base resolved body is `[0x4c234150,0x4c2378a1)`, 14161 bytes, SHA-256 `0b4ce1209e7d6151cd603478ab9b7b2090526a20024c756a35937d6e39a12b4e`. For version `>=0x21b`, it calls actual manager `+0x28` at `0x4c23423e`. On `IsLoading`, `0x4c234255` writes the actual model `R14` into manager `+0x258`. The similar store at `0x4c225046` belongs to the older monolithic arm and is not evidence for current-version reach.

Manager serializer `[0x4bcef8d0,0x4bcefbab)` loads each actual `moAtom_c`, writes its runtime manager pointer at `+0x138`, and inserts its sign-extended `+0x140` ID into manager map `+0x58`. The same ID enters the ordered tree at manager `+0x88`. Store emits the actual map count and atom objects, not the ordered-tree nodes or runtime body-cache maps. The SDK already models this field grammar in Config `ModelFields`.

The standalone manager constructor `0x4bcedbc0` seeds empty maps/tree and a null owner. The distinct constructor `0x4bced920` takes a model pointer as its second argument and installs it at manager `+0x258`; it is not a copy constructor. The ordinary model constructor uses that owner-taking form.

Current `moAtom_c` serialization initializes runtime `+0x160` to null before its discriminator. `body_kind=0` leaves publication to the later model/body lifecycle. Current feature references are represented by `f130/f12c` IDs; the direct `+0x148/+0x150` reference reads are in the older `<0x86f` branch. This checkpoint does not close every modern feature-ID fixup caller.

Selected `Part::replaceBody` can call actual `moAtom_c::setBody` at `0x4c1cfa1f`. That setter needs both a nonnull body and nonnull feature, then writes body `+0x160` at `0x4bcfb617` and feature `+0x148` at `0x4bcfb61e`. Earlier source gates and any later clears remain independent. The bounded `0x4c12d4f0` routine destroys the previous receiver `+0xd88` and replaces it with a supplied pointer, but this packet does not prove that routine is reached in the selected cold open.

## Minimal discriminating observations

At the normal map-lookup return `0x4bcf466c`, `R13` is manager, `RBX` is ordered-tree node, `R15D` is signed key, and `RDI` plus `qword[RSP+0x38]` are the actual atom or null. `RBP=RSP+0x100`. At `0x4bcf4870`, the actual atom is in `RDI` immediately before loading `atom+0x160`.

Capture the actual model `+0x2b0`, manager identity/owner, map count, tree size, selected cache flags and actual body/feature aliases. Pair those with the final array count at `0x4bcf31ec`, where `RBX` is output and `ESI` is its entry count. Any observer must retain bounded explicit incomplete states and normal continuation; it must not call the native getters or modify these words.

The first observation distinguishes an earlier cache/viewer route from an empty manager, a missing map alias, a null body association and a later predicate failure. A positive kernel body count in another invocation does not distinguish those cases.

## Verification and limits

The [sanitized source receipt](../measurements/2026/AtomManagerBodyEnumerationSource01.json) records original-PE verification of one module, 26 complete functions, 29 decoded instruction windows, 10 data ranges, 25 imports and seven vtable cells. The retained verifier checks original bytes and complete unwind groups; it executes no vendor code. Native cold-open body admission, default-light equivalence, full model acceptance and held-out qualification remain false. No SDK or writer code is changed.
