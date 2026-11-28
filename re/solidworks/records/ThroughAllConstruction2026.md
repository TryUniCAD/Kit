# Through-all extrusion construction in SOLIDWORKS 2026

This is source-only research. No through-all writer has been implemented or qualified. The original-image collector has zero writer outputs and native launches. A later root-owned source attempt passed registered metadata and both native controls, then stopped in the observer before source qualification; the [retry record](ThroughAllSourceObserverRetry2026.md) preserves that separate outcome.

Task `B04-SW2026-EXTRUDE-THROUGHALL` is owned by `/root/assembly_occurrence` for static analysis and the source harness, with `/root` as the sole Windows oracle owner. Delivery is PR #121. Dependencies are the shared extrusion and end-spec schemas, the ordinary cut factory, and new independently locked source files. The exit is complete generated native open, independent geometry, editable history, save and fresh reopen against prewriter-locked held-outs with healthy controls. A source lock alone does not meet that exit.

## Exact-build authority

The reproducible [evidence collector](../../tooling/sw2026/ThroughAllConstructionEvidence.py) records binary hashes, PE body ranges and SHA-256 values, managed method tokens, MVID, body classification, call edges and parser versions. It emits independently written field rules and identity metadata, never executable bodies or vendor listings. Its [adjacent JSON receipt](ThroughAllConstruction2026.json) is generated from the original installed images outside the checkout.

| Module | SHA-256 | Role |
| --- | --- | --- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` | Native model and serializers |
| `sldcoreu.dll` | `3af88769b06bf7a1510fe52f279fbda20e5dc5548dc3925a1357e0f71cc3b3e3` | Mixed C++/CLI feature construction |
| `sldappu.dll` | `50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf` | COM feature wrappers and macro-data bridge |
| `slduiu.dll` | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` | Native API command construction |

The oracle is SOLIDWORKS `34.5.2.0604`, document version 19000. This does not qualify adjacent releases. The mixed-mode module MVID is `3f9c2ded-9024-4b12-ac82-deb36cae1451`; managed code is decoded only when the method implementation flags declare CIL. Native methods remain native and their import thunks are resolved separately.

The complete export inventory explicitly raises the PE parser symbol budget to 100,000. The model has 45,857 declared and parsed exports. The earlier default-budget inventory was incomplete and is not evidence of absence.

## Native end owners

These extend [EndConditionConstruction2026](EndConditionConstruction2026.md) and the [ordinary cut constructor](OrdinaryBlindCutConstruction2026.md). The shared version-19000 layout remains unchanged.

| Field | Encoding and rule | Native authority | Confidence for this family |
| --- | --- | --- | --- |
| `moEndSpec_c.f08` | i32 single-end state | getter `0x4b283ba0`, setter `0x4b2913b0` | Partial until new sources exercise both modes |
| `f0c`, `f10` | Ordered i32 end types, indexed 0 and 1; getter and setter do not remap | `0x4b30d800`, `0x4b3100b0` | Partial for through-all |
| `f88`, `f8c` | Independent flip and direction integers | `0x4b2a75e0` / `0x4b2a7860`, `0x4b2c47a0` / `0x4b2c69a0` | Partial for through-all; do not conflate cut-inside/outside with direction |
| `f18`, `f20` | Actual distance display objects; nullable object references, not inline scalar distances | `getDistance` `[0x4badf660,0x4badf691)` | Partial until actual source owners are correlated |
| `fc8`, `fd0` | Optional draft displays governed by `fb8`, `fbc` and second-end activity | `[0x4bada5b0,0x4bada6da)`, `[0x4baf4100,0x4baf43c2)` | Partial for the new profile |
| `f818` | Actual end-spec owner on `moExtrusion_c`; ordinary modern cuts use `moICE_c` with the same serialization path | serializer `[0x4bb11640,0x4bb11888)` | Existing ordinary ownership; new termination pending |

The `moEndSpec_c` serializer is `[0x4bb10250,0x4bb11067)`, selected by vendor vtable slot 5 at vtable `0x4cf3d3f8`. Existing layouts condition extra point references on type 3 and body references on type 7. A type-1 mode does not justify a new captured record or fixed stream length. Complete linked round trips of new vendor saves remain pending.

### Distance deletion and reconstruction

`deleteNotUsedDims` has primary PE unwind range `[0x4bada5b0,0x4bada6da)`, 298 bytes, SHA-256 `e7cca85a1268e358689476cd08d8e424fdcc6ca4e58056b01c90425c1eaf789a`.

It removes the first distance display when the unsigned first type is in 1–4 and an environment predicate is false. It removes the second display when either the feature is single-ended or the second type is in 1–4, under the same predicate. Removal first clears actual dimension configuration data, destroys the display and nulls its owner pointer. Disabled draft displays are removed separately; second-end draft is also removed for a single-ended feature.

The predicate is `SldSession_c::Environment()` followed by virtual offset `0x78` with selector `0x33`. Its semantic name is **not found**. This is not authority to assume a universal null or to change the environment. New sources must measure their actual feature-owned dimensions.

`recreateNecessaryDisplayDims` has primary range `[0x4baf4100,0x4baf43c2)`, 706 bytes, SHA-256 `caae7595497a7864e9b2a8a114867ae8873590f9d78c25d678dc9acf8e7ee09c`. It iterates both end indices and applies the matching prune predicate before allocation. On the prune branch it destroys and nulls the display, then skips distance allocation. On the other branch it retains or creates `moDisplayDistanceDim_c` with `ParallelPlaneDistanceDim_c`, using role `end + 1`. The separate draft roles are 3 and 4; the from-offset role is 19. The ordinary type-1 update path therefore cannot be modeled as an always-active blind depth graph.

Both rules are **partial** for through-all until exercised by the new sources. They are independent code evidence rather than a fit to a saved part.

### Managed factory boundary

`ExtrusionPacket_c.CurrentEndSpec`, token `0x0600503a`, RVA `0x141848`, contains 144 CIL code bytes, SHA-256 `7a7f1a88631b01dc344c78015bc8cc07126f9de38dd64cd49b719f6389dbbeb9`. Its input end spec comes from native extrusion offset `0x818`. Its type switch is:

| Native type | Construction result |
| --- | --- |
| 0 | `BlindEndSpec_c` |
| 1, 2 | null |
| 3 | `ToPointEndSpec_c` |
| 4 | `ToSurfaceEndSpec_c` |
| 5 | `OffsetFromSurfaceEndSpec_c` |
| 6 | `MidPlaneEndSpec_c` |
| 7 | `UpToBodyEndSpec_c` |
| Default, including 9 | null |

`ExtrusionPacket_c.Initialize`, token `0x06005038`, independently has null selections for types 1 and 2. `BlindEndSpec_c.ApplyToModel`, token `0x06005072`, calls the base method, then `setDistance`, then `setType` with native type 0. The hypothesis that the blind packet or a generic `EndSpecification_c` provides a through-all constructor is **refuted for these exact methods**. Absence from this managed packet does not mean absence from native SOLIDWORKS.

Branch destinations in the private CIL analysis include the 12-byte fat-method header; stored instruction offsets are code-relative. The switch was interpreted with that distinction retained. No CIL listing is included here.

## Native authoring route

The source harness uses the native COM command route, not the unsupported managed factory branch:

| Edge | Exact entry or range | Evidence limit |
| --- | --- | --- |
| `IFeatureManager.FeatureExtrusion3` wrapper | `[0x4564bf70,0x4564c1d9)` | COM forwarding, not a standalone constructor |
| `IFeatureManager.FeatureCut4` wrapper | `[0x4564a930,0x4564abd9)` | Registered signature must be checked before CAD |
| Native extrusion command | `iApiFeatureExtrusion4` `[0x492546e0,0x49254c2d)` | Loads actual end-spec dialog data from macro parameters, feature scope and additional data, then runs the native command |
| Native cut command | `iApiFeatureCut7` `[0x49252ec0,0x4925341c)` | Entry identity pinned; detailed new type-1 behavior still requires source observations |
| Macro-data bridge | `uoDData_c::loadFromMacro` `[0x459ee330,0x459ee360)` | Native data map, not a captured field program |

The first cohort uses API end type 1. The both-direction input is `Sd=False`, `T1=1`, `T2=1`. API enum 9 is recorded in the registered metadata but is **not exercised** or assumed to equal native stored type 9. The exact native `f08/f0c/f10` correlation will come from disclosed source saves.

The official [2026 end-condition enum](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swEndConditions_e.html) identifies the API values. The official [multibody programming example](https://help.solidworks.com/2024/english/api/sldworksapiprogguide/Overview/Programming_Multibody_Parts.htm) includes a through-all boss merging existing bodies. This defeats a blanket assumption that through-all is cut-only, but the older API example does not qualify the pinned 2026 boss profile.

## REA and retained evidence

A bounded owned `sldbasegeomu.dll` Hopper document confirmed the ordinary modern cut factory and command completion edges. Evidence IDs include `ev_7428316b6f6a72a08d4e2329d49727c3466f62d4ec67cff7c80762834a27e20c` for the cut factory, `ev_cab65ef92697c4d3a391fbbbc24ce644d63297d700f51ab90f869f130134d71d` for extrusion dialog completion, and `ev_72bf91ca7797374e4e1d2a5ff65c21498f03325c9036e5475933f4228c590fcf` for the feature-completion edge. The private provider snapshot retained six evidence records. The owned document was closed after capture.

The model target was already leased by another provider session; that foreign document was not closed. Stateless LLVM and original PE/CIL evidence supply the model facts above. An empty `uiBoss` query over the small target inventory is only an inventory limitation, not evidence that boss construction is absent.

## Remaining work

1. Execute the frozen [source protocol](ThroughAllSourceProtocol2026.md) with registered metadata and healthy controls, then lock new guest-private source files before writer code.
2. Correlate exact Config and Resolved owners, including null active-distance fields and aliases, with native API measurements and code rules.
3. Bind the environment selector and any non-neutral save-only fields. Preserve unresolved `f150/f154` rather than copying them.
4. Trace the finite extent of a through-all boss independently. The stock-span formula in the source tool is explicitly an unverified hypothesis and never an acceptance gate.
5. Only then extend the shared generator, freeze input admission and independent predictions, and qualify held-out native lifecycle and exact feature trees. Public coverage remains unchanged.
