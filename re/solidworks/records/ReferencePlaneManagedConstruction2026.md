# Reference-plane construction through the 2026 mixed-mode core

Task `B04-SW2026-REFPLANES`; owner `/root/assembly_occurrence`; delivery PR #121. This is a static construction-rule supplement to [the reference-plane ledger](ReferencePlaneConstruction2026.md). Root owns the native oracle and shared evidence registers. The offset source packet committed at `8c462e65f` remains unchanged. No authored-plane writer is implemented or admitted by this record.

## Identity and method-body distinction

The exact input is `sldcoreu.dll`, 5,416,536 bytes, SHA-256 `3af88769b06bf7a1510fe52f279fbda20e5dc5548dc3925a1357e0f71cc3b3e3`, MVID `3f9c2ded-9024-4b12-ac82-deb36cae1451`, preferred image base `0x180000000`. Its CLI flags are `0x18`; it contains 1,202 type definitions and 21,740 method definitions. This is a mixed native/managed PE, not an interop declaration assembly alone.

The concrete request, evaluator and packet methods below are actual CIL bodies: method implementation flags `0x0`, `miIL=true`, `miManaged=true`, `miNative=false`. Their method RVA points to a CLI method header, not directly to x64 instructions. Conversely, the imported `<Module>` methods have flags `0x85`, `miNative=true`, `miUnmanaged=true`, `miPreserveSig=true`; their RVAs point to six-byte indirect native import jumps. A method name and nonzero RVA alone do not distinguish those cases.

[ManagedConstructionIndex.py](../../tooling/sw2026/ManagedConstructionIndex.py) reads explicit method tokens with lazy `dnfile 0.18.0`, decodes only those CIL bodies with `dncil 1.0.2`, and resolves native imports/exports with `pefile 2024.8.26`. The [reproducible receipt](../measurements/2026/ReferencePlaneManagedConstruction01.json), SHA-256 `c8c90e3fd70e9e52f6b8e7adae5370500a52cc5c471218d4d190e59f0366b397`, retains body/code/signature hashes, implementation flags and grouped metadata call edges. It emits no code bytes, IL listings, pseudocode, interop source or vendor software. A `callvirt` edge identifies its declared metadata target, not an observed runtime implementation.

The prior REA metadata request exhausted its 64 MiB representation budget before admitting method records. Lazy metadata parsing independently recovered the concrete bodies. The failed producer is retained in the main ledger; it is not evidence that the methods are absent. All task-owned Hopper sessions are closed; the final scoped session status was `open=false`, `cleanup_pending=false`. No new Hopper target or native process was started for this supplement.

## Concrete current construction route

These are independently read rules, not values inferred from a saved source. All tokens and RVAs in this table belong to the core identity above.

| Method | Token / RVA | Construction rule |
| --- | --- | --- |
| `GeometryConstraintTriplet_c.CreateData` | `0x06004c17` / `0x131870` | Calls the concrete triplet `CreateNewRefPlaneData`. With both result and an existing plane present, installs the plane pointer in data `f10`, calls `moRefPlane_c.setRefPlnData`, then applies each of the three non-null constrained geometries in order. |
| `GeometryConstraintTriplet_c.CreateNewRefPlaneData` | `0x06004c0f` / `0x12e070` | Asks the request for its current evaluator type, creates that evaluator with `(request, triplet)`, and calls its `createRefPlaneDataNewType`. An absent/null evaluator or null result is an explicit non-success state. |
| `PlNullNullPlaneEvaluator_c.isParallelPlaneOffsetDist` | `0x06004f6f` / `0x13ad68` | Requires an available input geometry and an actual `DistanceGeom_c`; it does not classify every plane selection as a distance input. |
| `PlNullNullPlaneEvaluator_c.createRefPlaneDataNewType` | `0x06004f74` / `0x13b020` | Creates three geometry slots. In the distance branch, invokes `convertToADefaultPlane` with those slots and the actual plane argument. Coincident and incomplete/general branches are separate. |
| `RefPlaneEvaluator_c.createThreeGeoms` | `0x06004e15` / `0x136368` | Loops indices `0`, `1`, `2`; each absent input gives a null slot, each present input calls its virtual `CreateData`. The slot order follows the input triplet, not class sorting or reference-ID order. |
| `DistanceGeom_c.CreateData` | `0x06004c64` / `0x12ea28` | Calls the selected geometry wrapper's `RefCopy` when present, otherwise uses null. Allocates `0x48` bytes, then invokes `moRefPlaneDistanceGeom_c(wrapper, distance, reverse, count)` using all four declared inputs. |
| `DistanceGeom_c.UpdateData` | `0x06004c65` / `0x12eab0` | Resolves the concrete distance geometry and updates wrapper, distance, reverse and count separately through their native setters. |
| `RefPlaneEvaluator_c.convertToADefaultPlane` | `0x06004e18` / `0x136464` | Allocates `0xe8` bytes and invokes `moConstraintDefaultPlaneRefplaneData_c(threeGeometrySlots, actualPlane)`. This binds the distance branch to the concrete default constrained-plane owner; the folded generic model factory does not supply it. |
| `ConstrRefPlaneDataPacket_c.CreateFeature` | `0x06004c03` / `0x1312cc` | Validates, calls virtual `CreateData`, rejects a null result, and constructs `moRefPlane_c(data, concept, nullStatus)` only when no feature already exists for that index. Sets data `f10` to the actual plane, calls `moRefPlnData_c.init(1)`, then publishes the feature into the request's feature list. |

The last method is 177 CIL code bytes and includes an exception region for allocation cleanup. Merely serializing the default-data and geometry classes does not reproduce its owner linkage, initialization or publication. `ApplyPacket` (`0x06004bc5`, RVA `0x135998`, 917 code bytes) and `FinishCreation` (`0x06004bc6`, RVA `0x1347b0`, 337 code bytes) provide further status/publication edges in the receipt. Their presence is not a claim that every indirect native slot or save-time effect has been classified.

The model bindings below resolve each core native thunk through the original import table to the original exported function in pinned `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, base `0x4b140000`. No managed body is disassembled as native code to obtain these addresses.

| Boundary | Core token / thunk RVA / IAT RVA | Native model address |
| --- | --- | --- |
| Distance geometry constructor | `0x06004448` / `0x166903` / `0x1774f0` | `0x4c2d7890` |
| Angle geometry constructor | `0x0600441e` / `0x16691b` / `0x177510` | `0x4c2d77a0` |
| Default constrained-plane constructor | `0x0600446c` / `0x166bd9` / `0x176c30` | `0x4b8e0220` |
| Authored plane constructor | `0x06004445` / `0x1669a5` / `0x1767d0` | `0x4c2d2d20` |
| Plane-data initialization | `0x06004414` / `0x16699f` / `0x1767d8` | `0x4c2f25d0` |
| Install plane data | `0x060043d8` / `0x166999` / `0x1767e0` | `0x4b293d50` |

## Compatibility route and mode guard

`PlNullNullPlaneEvaluator_c.createRefPlaneDataPacket` (`0x06004f77`, RVA `0x13b0c8`) has a separate distance branch. It calls `convertToDistance` (`0x06004f78`, RVA `0x13aed8`), which creates a managed `Distance_c` packet from the input distance, selected plane and reverse flag, then preserves the input reference index through `set_PlaneRefIndex`.

`Distance_c.CreateData` (`0x06004d16`, RVA `0x132564`) constructs **`moFaceRefPlnData_c`**, not `moConstraintDefaultPlaneRefplaneData_c`. It then writes common plane-data `f5c=5` and calls `setPlaneRefIndex`. Conversely, `Distance_c.convertToThreeGeoms` (`0x06004d14`, RVA `0x132504`) constructs a `DistanceGeom_c` with that selected reference index, plane wrapper, distance, reverse and count `1`, then installs it into that triplet slot. These are real compatibility paths. The value `1` is a constructor argument in that conversion, not authority to choose it for every finished distance feature.

`RefPlaneEvaluator_c.isOldRefPlaneFeature` (`0x06004de0`, RVA `0x135d7c`) compares the feature's native create version **unsigned `< 4150` (`0x1036`)**. `isCreatedByOldApi` (`0x06004de1`, RVA `0x1371fc`) separately queries the actual plane-data owner through `isCreatedByOldAPI_0`. `isOldRefPlaneOrCreatedByApi` (`0x06004de2`, RVA `0x137244`) combines those tests. This is a construction/compatibility guard in the pinned implementation, not a newly discovered serialized field or a claimed 2025→2026 wire change.

The registered `InsertRefPlane` route, resulting concrete owner and its mode state must still agree with the forthcoming disclosed native source saves. The static triplet branch does not prove which branch a particular API call takes. The [folded-factory gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/ReferencePlanes/ReferencePlaneFactoryExportIsABaseStub.md) remains applicable.

## Angle scope

`AngleGeom_c.CreateData` (`0x06004c73`, RVA `0x12ec70`) independently calls wrapper `RefCopy`, then the explicit native angle geometry constructor with `(wrapper, angle, reverse)`. That binds its scalar inputs to the serializer suffix already recorded in the main ledger. It does not classify an angular plane's selected axis, concrete evaluator, `moDisplayAngularDim_c`, editable dimension publication or final computed frame. The angle-plane corpus and constructor path remain separate unfinished work. No rotated cached frame is admitted as an angular feature.

## Reader reuse and remaining boundary

The ordinary SDK currently identifies principal and stored-frame planes in `Core/Native.py`. `DecodePlanes` uses `MatrixFrame`/`MinimalFrame` for non-principal planes. `ReadPlaneHandle` explicitly admits only owned principal plane IDs whose axis and basis agree. That is useful for its existing principal-plane scope; it does not expose an authored distance constraint, reverse/count inputs or the three-slot editable dependency graph.

Research can reuse `serial/Schema.py`, the existing archive map/context and `defs/ResolvedBody.py`'s `moRefPlane_c.f6f8` owner. `defs/ResolvedRefGeom.py` already provides the common plane fields, three-slot constraint interface, wrapper geometry base and the compatibility `moFaceRefPlnData_c` branch. The current schemas lack the distance/angle geometry suffixes and concrete default/at-angle owner registrations. Those gaps should be filled in a separate typed reader extension from the native store/load evidence, then correlated with disclosed source cases under their actual version and archive context. The SDK's heuristic stored-frame reader is not a replacement for this exact source audit. No reader or writer code was changed by this supplement.

## Adjacent request-family index

Only metadata names, type tokens and declared method counts were inspected for this index. **Zero adjacent-family method bodies were decoded**. Matches are exact substring queries over this one module, restricted to names containing `Request`, `Packet` or `Evaluator`.

| Family | Concrete metadata leads | Scope |
| --- | --- | --- |
| Extrude | `SolidCore.ExtrusionRequest_c` `0x02000382`; `ExtrusionPacket_c` `0x02000384`; generic model request `0x02000381` | Candidate future construction path only |
| Revolve | `SolidCore.RevolveRequest_c` `0x02000460`; `RootRevolvePacket_c` `0x02000461`; `MainRevolvePacket_c` `0x02000462`; `RevolveEndSpecSubPacket_c` `0x02000465`; generic model request `0x0200045f` | Candidate future construction path only |
| Sweep | `SolidCore.CreateSweepRequest_c` `0x02000444`; `CreateSweepPacket_c` `0x02000445` | Candidate future construction path only |
| Fillet | `SketchFilletPacket_c` `0x020003af` | Sketch fillet name; no inference of 3D edge fillet construction |
| Shell / hole / loft / pattern | No matching request/packet/evaluator type names in this module | Not evidence that the native feature or a route in another module is absent |

## Reproduction and acceptance limits

Run the tool with the pinned parser dependencies and original external modules. Its receipt's `query.method_tokens` lists the 33 selected methods. Pass each token as `--method TOKEN`, together with `--family-index`; both module hashes are mandatory when resolving native exports. For example:

```sh
uv run --isolated --with dnfile==0.18.0 --with dncil==1.0.2 --with pefile==2024.8.26 \
  python -B re/tooling/sw2026/ManagedConstructionIndex.py \
  /absolute/licensed/sldcoreu.dll /unused/ManagedConstruction.json \
  --expected-sha256 3af88769b06bf7a1510fe52f279fbda20e5dc5548dc3925a1357e0f71cc3b3e3 \
  --native-module /absolute/licensed/sldmodu.dll \
  --native-sha256 569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e \
  --family-index --method 06004f74 --method 06004e18 --method 0600446c
```

The short example selects three methods. Replaying all 33 receipt tokens reproduces the published receipt; add `--check` to compare the newly computed metadata result with the existing receipt without writing it. No ambient CAD install, native model file, saved row or hidden source is required. A changed build/MVID requires a fresh metadata query and new static qualification; tokens and RVAs are release-specific.

Verification here is an offline exact-input process audit: CIL/header and native-thunk distinction, import/export binding, metadata-only adjacent inventory and deterministic receipt. Generation and `--check` both returned the receipt hash above. All 22 CIL bodies also present in the separately retained private trace had matching complete-body and code hashes. A wrong declared module hash failed before output. No native source authoring, generated output, open/edit/rebuild/save/reopen acceptance or runtime route trace is claimed. Source qualification, final scalar/frame/annotation rules, complete typed readback and blind generated acceptance remain the exit gates.
