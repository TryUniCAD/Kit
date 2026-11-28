# SOLIDWORKS 2026 single-edge fillet archive ownership

Workstream `B04-SW2026-EDGE-FILLET-SOURCES` uses version `19000`, container version 4, and SOLIDWORKS 2026 SP05.2 x64 build `34.5.2.0604`. The [source authoring protocol](EdgeFilletSourceAuthoring2026.md) produced two disclosed ordinary constant-radius fillets on closed rectangular Front-plane blind bosses. Each model has an original and a separately saved D1 edit. The terminal source lock is `1f2652129840582cb663063b08f590dadbaf8dd046f0b96f5a1b99cf5ae47797`. Both unchanged control brackets passed in eight distinct native processes. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Reverse-engineering playbook](../../Playbook/README.md) · [Corpus correlation](../../Playbook/CorpusCorrelation.md)

The [guarded audit](../../tooling/sw2026/edge_fillet_source/AuditFilletArchive.py) verifies the SHA-256 of the source lock, registered enum receipt, both control reports, six source-phase reports and each CAD input before interpretation. For the original and edited states it compares the typed archive to the corresponding fresh native reopen. Separate research processes replay nine streams per input using their typed graph models. For ResolvedFeatures the audit also re-emits Config-0 first and passes its new map at counter 110 into the resolved writer. Counter 350 is observed at the end of all four resolved streams. All 36 streams re-emit byte-for-byte with zero unread tails and zero guarded external data accesses. The receipt records their hashes, class and schema inventory, raw field operations, observed owners and native quantities. [Exact archive receipt](../measurements/2026/EdgeFilletArchiveRead01.json)

## Measured feature and body owners

| Disclosed save | D1 in metres | ResolvedFeatures interval for schema-one `Fillet_c` | Config atom body stamp |
| --- | ---: | --- | ---: |
| Axial original | 0.00437 | [11996, 15788) | 1816 |
| Axial edited | 0.00611 | [12158, 15950) | 1409 |
| Transverse original | 0.00283 | [11996, 15772) | 1816 |
| Transverse edited | 0.0052699999999999995 | [12188, 15964) | 1412 |

The build map ties `Fillet_c` to `sldmopartu` slot-5 dispatch `0x1802701d0` and `edgeRadiusObject_c` to `0x180272610`. It separately identifies the radial-display, length-parameter, surface and edge-reference serializers in `sldmodu`. The audit re-verifies the schemas actually traversed by these four saves against the [existing research fillet layout](../../tooling/sw2026/serial/defs/ResolvedFillet.py), [typed reference layout](../../tooling/sw2026/serial/defs/ResolvedRefs.py), [dimension layout](../../tooling/sw2026/serial/defs/ResolvedDims.py) and [mapped SP05.2 dispatch](../../data/Serialization/SerializeMap2026.json). The only reached provisional operation is `mo_dynSurfIdArr.Serialize`. The fillet's edge keeper at `f820.f18` consumes two embedded `moEntityId_c` rows, with `moSurfaceIdRep_c` and `moFilletSurfIdRep_c` owned by the same actual fillet. The second keeper, `f828.f18`, has no rows. No other keeper shape or fillet family is qualified by this evidence.

The resolved fillet root has map slot 274 and feature ID 34. Its one `f868` item follows `edgeRadiusObject_c.f08` → `moDisplayRadialDim_c.f850` → `moFeatureDimHandle_c.ff0` → `ThreeDRadiusDim_c.f28` → `moLengthParameter_c`. The parameter name is D1 and `f58` is the editable metre value. That value equals the saved `fbf0` row's `f08` and the native driver's value after a clean reopen. Two eight-byte operations remain represented as raw fields in the existing research layout. Both are one-element current display arrays, and the audit independently interprets each element as a little-endian double and checks the stock depth or radius. The separate fixed eight-byte Definition CLSID field remains retained by its field owner. Its value construction has not been established here. These are read/replay observations. The audit does not manufacture replacement values.

The only `f848` item and the radial item's `f10` are separate `moCompEdge_c` wrappers sharing `moEdgeRef_c` slot 284. The `f820.ff0` keeper also aliases that reference. Their wrapper words `f18/f1c` are `(101,0)` and `(0,0)` respectively. In the one saved `f9b8` row, the result face has one produced fillet surface, four stock surface representations and a terminal null. Its related edge and the edge in the one `fbf0` row use distinct references at slots 330 and 341, each with the same ordered source-representation keys. All keys resolve into the `Default` configuration and match actual creation events in both Header2 and Config-0-ModelHeader for stock ID 32 or fillet ID 34. [Edge owner audit](../../tooling/sw2026/edge_fillet_source/FilletArchiveOwners.py) · [Distinct edge references gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Resolved/FilletEdgeReferencesHaveSeparateOwners.md)

The independently measured selected edge runs from `(0.0419, −0.0251, 0)` to `(0.0419, −0.0251, 0.0228)` metres in the axial case. Its ordered typed support IDs are side 2, side 1, end 1 and end 0. The transverse edge runs from `(−0.02975, 0.02645, 0.0286)` to `(0.01315, 0.02645, 0.0286)` metres. Its ordered IDs are end 1, side 3, side 2 and side 4. Native rollback independently verified one actual edge and two adjacent planar stock faces by body and feature identity. The original archive read located the four representations. The [rollback audit](EdgeFilletRollback2026.md#physical-stock-and-selected-edge) now joins them to the prior stock and orders the two incident faces and two endpoint planes. The general generating order and the `f70` edge values still require evidence. The fillet's common parent list `f60` is empty in each save. The selected references and linked atom supply the actual dependency seen in native.

The `fd88` atom manager, stock `f528` and fillet `f538` share Config-0 atom slot 58. The atom has native ID 101, stock creator 32 and fillet last modifier 34. Its `f180/f1b0` stamp equals `BODY_MATCH` from the one active body. `ATOM_ID_2001` and `LAST_BODY_MODIFYING_FEATURE_ID` independently bind the same actual kernel body. Each active partition's typed node records re-emit exactly from the canonical grammar, with seven faces, fifteen edges and ten vertices, and the saved cylindrical face agrees with the native radius and axis. The four active record sets contain 206, 203, 206 and 203 nodes. These comparisons exclude the transmit description, external compression and unqualified delta history. [Active kernel audit](../../tooling/sw2026/edge_fillet_source/FilletArchiveKernel.py)

## Remaining gates

The strict production archive path rejects `Fillet_c` schema 1. In each saved kernel history, the existing bounded `ReadXmtHistory` path reaches `ReadRollbackMut` and refuses the first rollback framing at record offset 51. The later [physical rollback audit](EdgeFilletRollback2026.md) consumes all four payloads and validates each previous state. Production feature and cache projection, source-independent construction of the edge and face owner groups, active topology generation, and the remaining condition variants require further evidence.

The independent [digest-only pre-writer lock](../measurements/2026/EdgeFilletPrewriterSourceLock01.json), SHA-256 `b572c2428f2145975a4f32b2588ce9493c4ab02ede58c0e25c16672c1c711247`, records two separate private native lifecycles and healthy brackets with eight distinct processes. Only the original and edited source hashes and acquisition provenance are published. The private inputs and phase reports were excluded from this audit. The lock precedes writer implementation and records zero writer outputs and zero held-out writer acceptance. [Held-out procedure](../../Playbook/GenerativeCorpus.md)

Run the data-only audit from the checkout root after retrieving the exact disclosed terminal packet. Use a fresh output filename.

```sh
python3.14 -B re/tooling/sw2026/edge_fillet_source/AuditFilletArchive.py \
  --capture /absolute/path/to/disclosed/EdgeFilletSource03/Capture \
  --report /absolute/new/EdgeFilletArchiveRead01.json
```

## Explicit shared archive read

The shared version-19000 ResolvedFeatures reader now has an internal `ReadFillets=True` option. Its context requires an ordinary compressed part with `cmgr_f658=1`. The option adds only the seven concrete schema-one descriptors observed in the disclosed files. It reuses the existing body-feature, current component-reference, boundary entity, surface-ID, point and dimension rules. The fillet-specific layout reads the real keeper counts and result maps. The bounded path rejects the unqualified component alias, composite edge and saved body-row branches and checks the selected and auxiliary record inventory. Field values come from the parsed file.

The [typed production-reader receipt](../measurements/2026/EdgeFilletTypedRead01.json), SHA-256 `39c1df18ead423448ce02262e2555fee39abf4139e6ea8d5f45c9804f8b93f9b`, records four complete production `ReadResolvedMut` reads with no missing or provisional grammar. All four match the independent owner records above. Each consumed 143 schema bodies and inherited map counter 110, ending at 350. The ordinary shared Config-0 writer re-emits the exact configuration before the unchanged research store replays the production-read resolved graph byte-for-byte. The shared display codec records two actual typed binary64 values for the stock depth and radius. The separate immutable ordinary control reproduces both streams with its resolved map at 109 to 268. The alternate manager context, one-row keeper and enabled component array refuse. The standard read and resolved store continue to refuse `Fillet_c` schema 1. Public feature projection, production kernel history admission and generation require separate qualification.

```sh
python3.14 -B re/tooling/sw2026/edge_fillet_source/AuditTypedFillet.py \
  --capture /absolute/path/to/disclosed/EdgeFilletSource03/Capture \
  --control /absolute/path/to/disclosed/EdgeFilletSource03/Packet/Control.SLDPRT \
  --report /absolute/new/EdgeFilletTypedRead01.json
```

The [saved public reader](SavedEdgeFilletSdk2026.md) now binds the warm
transaction, actual prior edge, live D1 and sense-corrected rounded body
across all four disclosed saves.
