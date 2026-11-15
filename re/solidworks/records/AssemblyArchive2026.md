# SOLIDWORKS 2026 assembly archive grammar

Target-application acceptance is unproven. This work extends the research source-document codec; it does not construct a fresh assembly or establish vendor loadability, rebuild correctness, or mate editability. The fourth remote run passed the complete 14-stream byte-identity process check across two training assemblies, including both resolved-feature streams. Two unrelated signature-table checks still failed in that run because their licensed binary dependency had been removed from the checkout.

## Authority and inputs

The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) apply without reduction. Their stopping conditions are: “There are two acceptable stopping conditions. The first is success under every criterion on this page. The second is the end of the available context. Missing grammar is the work. It is not a blocker.” The parent goal continues beyond this component.

The implementation is [ConfigAssembly.py](../../tooling/sw2026/serial/defs/ConfigAssembly.py). It registers assembly-owned records and reuses `ConfigPart`'s model base, sections, presence fields, normalization witnesses, and existing reference/math schemas. It never registers the shared model twice. The archive registry discovers the new module automatically.

All native addresses below belong to the following 2026 modules, as recorded by [Manifest2026.json](../v2026/Manifest2026.json) and [SerializeMap2026.json](../../data/Serialization/SerializeMap2026.json):

| DLL           | SHA-256                                                            |
| ------------- | ------------------------------------------------------------------ |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `sldmfcu.dll` | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` |

Static evidence came from the existing private `assembly-serialize.c`, `assembly-core.c`, `assembly-config.c`, and `assembly-tail.c` dumps, plus read-only decompilation in isolated copies of the existing Ghidra projects. No shared database was changed. Decompiled vendor listings remain outside repository checkouts under the research artifact policy. This finding records format facts without vendor code. No native runtime or instruction trace was collected by this component.

The two controls are declared in `re/solidworks/v2026/corpus/assemblies/Manifest.json`: `A0_one.SLDASM` contains one component; `A1_two.SLDASM` contains two components and three recorded mate creation attempts. Read-only inspection of the authoring specification identifies two coincident mates and one distance mate. Both controls are parser training fixtures, not held-out generated output. Their saved values must not become builder defaults or donor data.

## Scope and classification

The schema requires format version `19000`. Older and future layouts fail explicitly. A field with an offset name is identified by its wire owner, width, and order; that name does not assert a recovered product-level meaning.

Every scalar, string, transform, cache value, and object link in the tables below is **source input** for this source-document codec. Presence markers and normalization witnesses preserve the original wire representation. Collection lengths and section lengths are **derived bookkeeping**, recomputed from their typed records. No value from either control is classified as a universal constant or neutral fresh-model cache.

Complete parsing and exact storage of the 14 exercised streams are **confirmed by remote compatibility evidence**. Other branches and subclasses remain **partial — static native evidence**. A successful Kit object round trip confirms the exercised encoding and remains separate from native execution, held-out generalization, and target-application acceptance.

## Assembly root

`moAssembly_c::Serialize` at `sldmodu.dll!0x4b663c90` dispatches slots `0x4b8` and `0x4c0` for versions greater than `0xc7c`. At vtable `0x4ce69b30` those slots are `0x4b6746e0` and `0x4b677880`. The shared section helper `0x4c2114b0` reads or writes a four-byte byte-length prefix; its caller supplies section kind 1 or 2.

| Order     | Record/member                               | Wire rule                                                                                                     | Native evidence                                                                     |
| --------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| LW 1      | model base                                  | Existing `moModel_c.FUN_4c22ec80`, including direct-load bookkeeping                                          | `0x4b6746e0` calls `0x4c22ec80`                                                     |
| LW 2–3    | `f1a18`, `f1a20`                            | Separate u8 presence markers, each followed by embedded `mgBBox_c` when nonzero; second exists after `0x17fa` | `0x4b6746e0`                                                                        |
| LW 4–5    | `f14a0`, `f14d8`                            | Two embedded string-to-string maps after `0x23da`                                                             | `0x4b6746e0`; constructor `0x4b67e710` establishes both map types                   |
| RES 1     | model base                                  | Existing `moModel_c.FUN_4c234150`; part-only fields remain absent for assembly root                           | `0x4b677880` calls `0x4c234150`                                                     |
| RES 2–3   | `f1560`, `f1570`                            | i32, u16                                                                                                      | `0x4b677880`                                                                        |
| RES 4–7   | `f15a0`, `f1608`, `f1748`, `f1740`          | Four object pointers in this order; nullable values remain actual object tags                                 | `0x4b677880`                                                                        |
| RES 8–12  | `f1750`, `f1598`, `f1590`, `f1868`, `f1a28` | i32, i32, object, object, i32                                                                                 | `0x4b677880`; timings after `0xe09`, `f1a28` from `0x11c7`                          |
| RES 13–14 | `f18c8`, `f18e8`                            | Two embedded object arrays, not object-pointer tags                                                           | `0x4b677880`; constructor `0x4b67e710` calls `su_CObArray` twice                    |
| RES 15    | `f1710`                                     | i32 smart replacement presence, after `0x1feb`                                                                | `LoadSmartReplacementData` at `0x4b660620`                                          |
| RES 16    | `f1718`, `f1720`, `f1708`, `f1738`          | When `f1710 != 0`: object, u32 count of `(i32 key, object, object)`, object, i32                              | Read `0x4b660620`; store `0x4b677880`; current version follows post-`0x2392` branch |
| RES 17    | `f1940`                                     | i32 flag after `0x2795`                                                                                       | `0x4b677880`                                                                        |
| RES 18–19 | `f1948`, `f1990`                            | Embedded object lists when flag is nonzero on read                                                            | `0x4b677880`; constructor `0x4b67e710` establishes list types                       |
| RES 20    | `f1674`                                     | i32 after `0x27a3`                                                                                            | `0x4b677880`                                                                        |

The native store uses `f1940 == 1` whereas the read accepts nonzero. The codec preserves the read record; this is not evidence that a fresh builder may choose other flag values. The downstream-id branch under archive condition `0x80` is explicitly unmodelled rather than skipped.

Three member roles are independently bound by exported leaf accessors in the same binary:

| Field   | Native role and evidence                                                                          | Constructor seed                  | Fresh generation obligation                                                                                                        |
| ------- | ------------------------------------------------------------------------------------------------- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `f1570` | `getSolveStatus`, `0x4b69e140`, returns the i32 member at `+0x1570`; serializer narrows it to u16 | Constructor `0x4b67e710` writes 0 | Derive the solve result or prove an accepted neutral state; constructor initialization alone does not prove a valid saved assembly |
| `f1674` | `getActiveGroundPlaneId`, `0x4b298b50`, returns `+0x1674`                                         | Same constructor writes -1        | Map an authored active plane to its generated id, or prove the absent-plane state                                                  |
| `f1940` | `getAssemXRayToggle`, `0x4b298b80`, returns `+0x1940`                                             | Same constructor writes 0         | Authored display option; enabled mode must construct the two associated lists consistently                                         |

These are static operand and constructor observations, not constants inferred from related controls. The other assembly scalar roles remain unresolved for fresh construction.

## Configuration graph

The serializer map identifies `0x4c221a20` as `moConfiguration_c`/`moDeformConfiguration_c`, despite misleading inferred `moMateGroup_c *` parameter types in one dump. Both concrete vtables point to concept lightweight `0x4c17a7b0` and concept resolved `0x4c17b570`. The resolved method serializes a list only when the native member at `+0x60` is nonnull; the configuration constructor leaves that member null, so this dispatch emits no bytes for the configuration record.

| Owner                            | Fields in wire order                                                        | Encoding and condition                                                                                               | Native evidence                                                                           |
| -------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `moConfiguration_c`              | base, `fc48`, `fc50`                                                        | Existing base configuration, then two `moConfig_c` object pointers                                                   | `0x4c221a20`                                                                              |
| same                             | `fca0`, `fca8`                                                              | Two object pointers when condition 1 is absent                                                                       | `0x4c221a20`                                                                              |
| same                             | `fce8`                                                                      | i32 count, then config object pointers; count is not MFC variable-width list count                                   | Reader `0x4b8c04b0`, writer `0x4b8c11d0`                                                  |
| same                             | `fba8`, `fbb0`, `fbc0`, `fbc4`, `fbc8`, `fce0`                              | object, object, i32, i32, object, mass-cache object                                                                  | `0x4c221a20`; final cache after `0x42d6`                                                  |
| `moConfig_c`                     | `f08`, `f0c`, `f10`, `f14`, `f18`, `f28`, `f20`, `f34`, `f38`, `f3c`, `f40` | Eleven 32-bit integers in this order                                                                                 | `sldmfcu.dll!0x3c7c6310`                                                                  |
| same                             | `f48`, `f50`                                                                | CString and i32, not an opaque 16-byte member                                                                        | Helper `sldmfcu.dll!0x3c7c6720`                                                           |
| same                             | `f58`, `f5c`, `f60`, `f64`, `f68`, `f6c`, `f70`, `f74`                      | Seven i32, then u8 boolean witness after `0x42d2`                                                                    | `sldmfcu.dll!0x3c7c6310`                                                                  |
| `moConfigObject_c`               | `f08`, `f10`, `f28`, `f40`, `f48`                                           | Config object pointer, component pointer, embedded referenced configuration, visual pointer, embedded children cache | `0x4c21dfc0`; helper `0x4b8ad480` supplies embedded referenced configuration during store |
| same                             | `f140`, `f78`, `f18`, `f20`, `f148`, `f170`                                 | i32 presence + transform, embedded list, three i32, i32 presence + transform                                         | `0x4c21dfc0`                                                                              |
| same                             | `fc0`, `fc8`                                                                | Flex cache object pointers only without condition 1                                                                  | `0x4c21dfc0`                                                                              |
| same                             | `f178`, `f190`, `f118`, `fd0`                                               | CString, u8 boolean witness, embedded list, embedded list with temporary condition `0x200`                           | `0x4c21dfc0`; `f190` after `0x3f09`, final list after `0x2f54`                            |
| `moFeatherWeightChildrenCache_c` | `f08`, `f28`                                                                | Embedded object array, u32                                                                                           | `0x4c223e60`; constructor `0x4b8a5230` sets array vtable at object `+0x50`                |

`moBaseConfiguration_c::SerializeXmlData` at `0x4c2389a0` calls the shared feature XML serializer and updates an external XML extractor without further archive fields. The separate condition-1 configuration visual callback remains explicit unknown work.

The final config-object list uses the native add/remove condition sequence: OR `0x200` before the embedded list, then clear `0x200` afterward. It does not restore a saved prior bitmask. The schema pins version `19000` explicitly, so changing the DSL's default version cannot silently broaden this recovered layout.

Exported `sldmfcu.dll` accessors independently bind these `moConfig_c` members. Each address below is a static read of the named member, not an observed native execution. The source codec preserves them; a future builder must supply authored settings or derive dependent state and validate the still-unrecovered enum domains.

| Member    | Native accessor or predicate                                                            | Address                    |
| --------- | --------------------------------------------------------------------------------------- | -------------------------- |
| `f08`     | `getAction`, `moConfigAction_e`                                                         | `0x3c7553e0`               |
| `f0c`     | `getExpAction`                                                                          | `0x3c765df0`               |
| `f10`     | `getVisibility` returns 1 exactly when `f10 != 0` and runtime member `f24 == 0`         | `0x3c7c6800`               |
| `f14`     | `excludeFromBOM` reads the member; `setExcludeFromBOM` directly stores its i32 argument | `0x3c765e60`, `0x3c765fb0` |
| `f18`     | `getSuppressionState`; raw value 3 maps to 0 when its boolean argument is true          | `0x3c7c67f0`               |
| `f28`     | `getAutoSuppressed`                                                                     | `0x3c757f20`               |
| `f20`     | `getSolvingOption`, `moConfigSolvingOption_e`                                           | `0x3c74f9b0`               |
| `f34`     | `getSaveAssemblyAsPartOption`, `moASMSLDPRTCompPref_e`                                  | `0x3c759fd0`               |
| `f38`     | `getDisplayMode`, `displayModeType`                                                     | `0x3c755370`               |
| `f3c`     | `getHlrDisplayQuality`, `hlrDisplayQualityType`                                         | `0x3c755380`               |
| `f40`     | `getEdgesInShadedMode`                                                                  | `0x3c7512a0`               |
| `f48/f50` | `getDisplayState` passes the embedded `visStateNameId_c` at `+0x48` to its copy helper  | `0x3c7c67a0`               |
| `f58`     | `getHiddeninFMTree`                                                                     | `0x3c7553d0`               |
| `f5c`     | `getIsSuppByCompPat`                                                                    | `0x3c7553b0`               |
| `f60`     | `getIsVisSetByCompPat`                                                                  | `0x3c755390`               |
| `f64`     | `getIsAZone` tests equality with 1; `isAZoneFlagSet` tests inequality with -1           | `0x3c7c67c0`, `0x3c7c6820` |
| `f68`     | `getTLTransparency`                                                                     | `0x3c76cf30`               |
| `f6c`     | `isFlexiblePartComp`                                                                    | `0x3c757ff0`               |
| `f70`     | `getUseMassPropertyFromRigidState`                                                      | `0x3c757ec0`               |
| `f74`     | `getHideForSpeedPakAtTopLevel`, u8                                                      | `0x3c7c67b0`               |

Dependent-state formulas and enum domains remain unresolved. Runtime-only members such as `f24`, `f30`, `f78`, and `f7c` are not added to the archive merely because an accessor exposes them.

## Component and mate records

`moReference_c` at `0x4b66f340` calls the shared feature serializer, then serializes these 2026 fields in order:

| Group                     | Members                                                                                                                        | Wire rule                                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| placement                 | `f360`, `f370`, `f3b0`                                                                                                         | u8-presence transform, u8-presence bounding box, external object pointer                             |
| state                     | `f400`, `f408`, `f3e0`, `f3c0`                                                                                                 | u16, u16 boolean witness, u32, embedded referenced configuration                                     |
| legacy carrier still read | discarded transform, `f378`                                                                                                    | u8-presence transform; u8 array presence followed by i32 count of individually u8-present transforms |
| auxiliary state           | `f450`, `f3f0`, `f468`, `f458`, `f548`, `f470`, `f4b0`, `f488`, `f4b4`, `f454`, `f490`, `f4d8`, `f418`, `f41c`, `f4c0`, `f4dc` | i32, u32, object, i32, object, object, i32, object, i32, i32, object, then five i32                  |
| provenance/reference      | `f3e8`, `f4f0`, `f4f8`, `f550`, `f500`, `f508`, `f524`, `f530`, `f388`                                                         | u32 time word, i32, object, i32, two CStrings, three i32                                             |
| final state               | `f55c`, `f3f4`, `f3f8`, `f538`, discarded stack object, `f49c`, `f4a0`, `f4a4`, `f3dc`                                         | three u32, object, object, four i32; final i32 after `0x42d2`                                        |
| conditional tail          | `f368`                                                                                                                         | u16 boolean witness only under condition `0x80`                                                      |

Native aliases `moReferenceInternal_c`/`moReferenceBrowser_c` at `0x4b66ef10` and `moReferenceModel_c` at `0x4b66ef30` add no archive fields. Their vtable dispatch matches the reference base.

| Owner                                                          | Wire rule after its base                                                                                                                                                                           | Native address |
| -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| `moMateGroup_c`                                                | Shared model-feature base; i32 count of obsolete manager records; high-word/low-word u64 count of i32 list values; conditional `f4f8` i32 under `0x80`                                             | `0x4b669f90`   |
| `moMateParent`                                                 | Shared model-feature base; i32 `f390`, `f394`, `f388`; u32 count of i32 values at `f370`                                                                                                           | `0x4b66b620`   |
| `moMate`                                                       | Parent base; u16 `f3b4`, `f3b8`; u8-present vector at `f3c0`; i32 count of `(i32 key, reference-wrapper object)`                                                                                   | `0x4b668d90`   |
| `moMateNGeoms_c`                                               | Mate base; array object `f430`; i32 count of reference-wrapper objects `f410`; u32 count of object-list pointers `f448`; three optional data objects; u16 `f438`; i32 boolean `f480`; two CStrings | `0x4b66ad10`   |
| `moMate2Geoms_c`, coincident, parallel, perpendicular, tangent | N-geometries base; no additional 2026 archive fields                                                                                                                                               | `0x4b668a60`   |
| `moMateEntityHelpData_c`                                       | u16 `f10`, then f64 `f18`, `f20`, `f28`                                                                                                                                                            | `0x4b6699f0`   |

The obsolete manager record's nonzero branch is deliberately an explicit unknown. No guessed size or zero-fill is used. Other mate subclasses retain registry unknown-class errors until their serializers are recovered.

The distance-mate path also has native evidence: `moMateDim_c` at `0x4b669510` calls the two-geometries base, serializes a display-dimension object pointer at `+0x4b8`, then u16 `f4c0`. `moMateDistanceDim_c` at `0x4b669690` adds u16 `f4d8`, i32 `f4dc`, i32 `f4e0`, and i32 `f4f4`. The current branch includes all four fields; the last is present from version `0x2bc4`. The distance value is represented by the linked dimension graph, not a copied scalar from the training control.

## Cache and auxiliary nodes

| Owner                       | Fields in order                                                                                                | Encoding                                                                                              | Native evidence                                                             |
| --------------------------- | -------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `moConfigSpecificInfo`      | `f08`, `f10`                                                                                                   | CString, i32                                                                                          | `0x4b7408d0`                                                                |
| `moBCMate_c`                | base, `f18`, `f20`, `f24`, `f28`, `f30`, `f38`, `f3c`                                                          | Base above, CString, two u32, two CStrings, two i32                                                   | `0x4b73f570`                                                                |
| `moBCConfigObjMapInfo_c`    | `f08`                                                                                                          | Embedded list                                                                                         | `0x4b73f2e0`                                                                |
| `moBCConfigurationInfo_c`   | `f08`, `f10`, `f18`, `f1c`, `f20`, `f2c`, `f30`, `f34`, `f38`                                                  | Two CStrings, two i32, object, four i32                                                               | `0x4b73f3d0`                                                                |
| `moBCNode_c`                | `f08`, `f0c`, `f10`, `f14`, `f18`, `f20`, `f28`, `f30`, `f38`, `f48`, `f40`, `f50`, `fb0`, `f58`, `f5c`, `f68` | Three i32, u32, CString, u32, two CStrings, i32, transform, two lists, three i32, final embedded list | `0x4b740570`; constructor `0x4b73bd40` constructs the final list at `+0x68` |
| BC assembly/part node       | base, `fb8`                                                                                                    | BC node base and embedded list                                                                        | `0x4b73f1b0`                                                                |
| `moBCChildNode_c`           | none                                                                                                           | Native serializer performs no archive reads or writes                                                 | `0x4b73f2b0`                                                                |
| `moAssemblyTimings_c`       | four discarded words                                                                                           | Four i32; source values retained even though native save emits zero                                   | `0x4b663bf0`                                                                |
| `moAssyFilePropContainer_c` | `f08`, `f10`                                                                                                   | Two object pointers                                                                                   | `0x4b2a12b0`                                                                |
| `moBodyMassPropsCache_c`    | `f08`, `f10`, `f18`, `f1c`, `f20`, `f238`, `f28`                                                               | i32, f64, u32, u8 boolean, i32, CString, embedded mass properties                                     | `0x4b2afbd0`                                                                |
| `moAssyMassPropsCache_c`    | `fc8`, `f08`                                                                                                   | f64; u32 count of `(u32 high key, u32 low key, embedded body mass cache)`                             | `0x4b2af900`                                                                |
| `moExplViewManager_c`       | feature base, `f358`, `f360`, `f398`, `f3a0`, `f3a4`, `f368`                                                   | Two objects, f64, two i32, embedded word-to-object map                                                | `0x4b667070`                                                                |

None of these cache values is accepted as a fresh neutral value. Parsed values remain source-document inputs; native recomputation and fresh construction require independent evidence.

## Component history and favorites

The second remote run reaches `moHistoryCompItemData_c` in both resolved-feature streams. Its node base is established by native helper calls and raw vtable operands, independently of the class name and error offset. The following three recovered item classes all dispatch lightweight slot `0x4b8` to node serializer `0x4c17adf0` and resolved slot `0x4c0` to fieldless `0x4b27e120`. Their XML slot `0x3e8` is also fieldless. They do not inherit concept child-list bytes.

| Owner                      | Wire rule for version 19000                                                                                                                        | Native evidence                                                        |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `moHistoryCompItemData_c`  | Node base, then chain-component object `f48`; during reading only, archive context `+0x8a0` is set to 1 for that object and cleared to 0 afterward | Serializer `0x4b645080`; base helper `0x4b645260`; vtable `0x4ce42360` |
| `moFavoriteCompItemData_c` | Node base, then chain-component object `f48`                                                                                                       | Serializer `0x4b63d850`; base helper `0x4b63db50`; vtable `0x4ce34820` |
| `moSCCompItemData_c`       | Node base, transform-wrapper object `f48`, smart-component-feature object `f68`, CString `f58`, i32 `f60`, transform-wrapper object `f50`          | Serializer `0x4c633150`; base helper `0x4c633600`; vtable `0x4d1d4c58` |

The history helper switches from old base handling to `moNode_c::Serialize` at version `0x17e6`; the favorite helper switches at `0x140e`, and the smart-component helper at `0xcea`. All are on the node path at 19000. Native history and favorite pointer operators `0x4c2127c0`/`0x4c2141a0` use `moChainComponent_c` as their static class constraint. Transform-wrapper operators `0x4c264d30`/`0x4c268930` establish the two smart-component wrapper slots. Object payloads remain typed registry records, and an unsupported nonnull smart-component feature still fails with its actual missing class.

The read context is a native read-side state mutation, not a serialized flag or an authored value. All listed fields remain source-document input. This recovery supplies no inferred native defaults or fresh assembly history builder.

## Live-section folder

`moLiveSectionFolder_c` serializer `sldmodu.dll!0x4beb1cb0` calls folder base `0x4beb1bc0`, then writes an i32 whose value is exactly `(byte member +0x378 == 1)`. The reader, from version `0xf5a`, reads an i32 and assigns the member from `(wire value == 1)`. The source-document codec retains the original wire witness through the existing normalization operation. It does not widen the native byte member into a guessed additional field.

Its primary vtable `0x4d065bb0` uses concept lightweight `0x4c17a7b0`, concept resolved `0x4c17b570`, and feature XML `0x4bb2a650`. The constructor path independently proves that the resolved list exists: getter `0x4bead2d0` returns runtime descriptor `0x4dae8f10`; its factory `0x4bead1b0` calls live-section constructor `0x4beae1d0`, then folder constructor `0x4beae110`, feature default constructor `0x4bb38710`, and concept default constructor `0x4bda5800`. The latter allocates a node list at `0x4bda584b`/`0x4bda5861` and assigns member `+0x60` at `0x4bda5869`. This class therefore retains the concept list handler. Its constructor's flag seed is not treated as an accepted fresh-document default.

The related `moLiveSectionData_c` body grammar is not registered by this correction. Its serializer at `0x4bfb7b10` includes native body archive operations; an encountered nonnull record remains an explicit unknown rather than an opaque body span.

## Tupni application and verification

The [Tupni playbook](../../Playbook/Tupni.md) and [trace authority finding](../../../Documentation/Gotchas/Conversion/Solidworks/Tracing/TupniTraceAuthority.md) apply. This pass used static native dataflow to bind field operands to widths, loop bodies to counted record sequences, and call/vtable signatures to record ownership. It did not collect execution traces, taint a native input, or infer constants from fixture invariance.

The new process-boundary test invokes the existing archive command in a subprocess, covering CMgr, Config-0, ModelHeader, ResolvedFeatures, Definition, Biography, and History across the two fixtures. It requires `14/14 streams round-trip with no tail across 2 files`. No fixture content is loaded by production code or used to generate a different model.

Local checks are restricted to AST parsing and static formatting/lint. No local serializer invocation, imports, tests, fixture parsing, or CAD automation were executed. The exact remote results below remain distinct from target-application acceptance.

Remaining work includes nonzero obsolete mate-manager records, additional mate/assembly subclasses, condition-specific callbacks, fresh assembly builders, held-out layouts, and controlled target-application acceptance. Missing grammar remains active work in the parent goal.

## First remote result

[Native job 132720808853](https://github.com/TryUniCAD/Kit/actions/runs/43684101116/job/132720808853) ran PR 129 head `5dcd802279d5cb341bcb72296d250f59ac3a8759` using synthetic merge `d95c3fd` over parent `8e44d0eb5129e8ddffce92c49e59740c342d3f3a`. The whole smoke step reported 1 failed, 138 passed, and 158 skipped in 60.07 seconds.

Both assembly Config-0 streams round-tripped exactly with no tail: A0 contained 24,828 decoded bytes and map count 103; A1 contained 25,338 bytes and map count 108. Both ModelHeader, Definition, Biography, and History streams also passed. Both CMgr streams failed with `bad class ref 32512 at 297`. Both resolved-feature checks stopped while deriving context from CMgr, before their own grammar was exercised. Total: `10/14 streams round-trip with no tail across 2 files`. This is an intermediate codec result, not target acceptance.

The next investigation checks the configuration constructor's child-list state against the pointer guard in native concept resolved serialization, rather than inserting padding or fitting offsets.

## Configuration child-list correction

The initial hypothesis that a concept resolved vtable entry always emits a node list is **refuted**. Static constructor dataflow identifies the missing predicate: default `moConfiguration_c` constructor `0x4b8c4c00` calls base constructor `0x4bdbdd40`, which calls feature constructor `0x4bb38350` with child-list argument 0. That argument reaches concept constructor `0x4bda5770`. Instruction `0x4bda579f` clears member `+0x60`; the zero-argument branch at `0x4bda57bf` skips allocation. The concept resolved serializer reads this pointer at `0x4c17b5a1` and skips its store payload at `0x4c17b5b0` when null. Its read branch has the same pointer guard.

The configuration wire handler therefore emits no resolved-list fields. Assembly model and mate feature lists retain their existing handlers. This correction follows constructor and reader/store predicates, not the numerical error offset. The second remote result below proves exact CMgr reproduction after this correction.

## Second remote result

[Native job 132725623286](https://github.com/TryUniCAD/Kit/actions/runs/43685701362/job/132725623286) ran PR 129 head `ab0676f2bec93bb852f32b43026fdcf9780e8fc8` using synthetic merge `451e928cf38efb46a94b5ea3f6bb27d8625d4b93` over parent `e34bd010e28429bc43e9e9d5a0e5fc5d42c73513`. The smoke step reported 1 failed, 138 passed, and 158 skipped in 46.08 seconds.

Both CMgr streams now round-trip exactly with no tail: A0 contains 1,874 decoded bytes and map count 32; A1 contains 2,256 bytes and map count 40. The ten previously passing streams still pass. Both resolved-feature streams now fail at byte 635 with `no schema for moHistoryCompItemData_c`. Total: `12/14 streams round-trip with no tail across 2 files`. This isolates the next missing typed record after the constructor-based alignment repair. The component history/favorite/smart-component grammar above is the next static repair; its remote reproduction remains pending.

## Third remote result

[Native job 132730137666](https://github.com/TryUniCAD/Kit/actions/runs/43687231116/job/132730137666) ran PR 129 head `1f801dd939ae3237c67c0976191e049e2a6ecb6e` using synthetic merge `27c89a8eb47ae2e921a4371af3e993e9ace1edcc` over parent `fde9e219faff10fca615a5b50560e78c1730888d`. The smoke step reported 1 failed, 138 passed, and 158 skipped in 39.79 seconds.

The twelve complete streams still round-trip exactly with no tail. Both resolved-feature parsers advance beyond the history item and now stop at unregistered `moLiveSectionFolder_c`, at byte 1,194 in A0 and byte 1,250 in A1. Total remains `12/14 streams round-trip with no tail across 2 files`. The new class boundary is evidence of parsing progress, not proof of a complete history-record round trip: storage was not reached after the later read failure. The folder correction above awaits the next remote reproduction.

## Fourth remote result

[Native job 132734160210](https://github.com/TryUniCAD/Kit/actions/runs/43688575142/job/132734160210) ran clean PR 129 head `913834f602ca2ce65fd8be1d5c69a0957fe7277e` using synthetic merge `061a797b82b73a548f6eaf711071cc5bd98c6a65` over parent `d8163fba85881722f3ccb9d897db8883e9f0fb46`. `AssemblyRoundTests.py` passed its subprocess exit-code assertion and its exact `14/14 streams round-trip with no tail across 2 files` assertion. Pytest captures successful subprocess output, so the job reports the passing test rather than repeating each stream diagnostic.

| Stream                               | A0 one component | A1 two components |
| ------------------------------------ | ---------------- | ----------------- |
| `Contents/CMgr`                      | Exact, no tail   | Exact, no tail    |
| `Contents/Config-0`                  | Exact, no tail   | Exact, no tail    |
| `Contents/Config-0-ModelHeader`      | Exact, no tail   | Exact, no tail    |
| `Contents/Config-0-ResolvedFeatures` | Exact, no tail   | Exact, no tail    |
| `Contents/Definition`                | Exact, no tail   | Exact, no tail    |
| `_MO_VERSION_19000/Biography`        | Exact, no tail   | Exact, no tail    |
| `_MO_VERSION_19000/History`          | Exact, no tail   | Exact, no tail    |

The whole smoke step reported 2 failed, 137 passed, and 158 skipped in 59.40 seconds. Both failures were in `SolidworksSignatureTableTests.py`, whose old setup required the removed `re/binaries/sldmfcu.dll`. No binary is restored by this component. The clean-main repair makes recorded format rows mandatory and verifies an external licensed binary separately when `KIT_SOLIDWORKS_DLL` is supplied; that repair is included in the next branch revision. This passing assembly check does not make the failed whole job green.

The subsequent required rationale-comment update changes no executable syntax in the eight assembly, metadata, and style process files. Static AST equivalence, Black, and the scoped rationale checker passed locally. All test execution remains remote, and current-head CI and approval still require fresh evidence after the update.
