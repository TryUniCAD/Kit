# Ordinary authored reference planes in SOLIDWORKS 2026

Task `B04-SW2026-REFPLANES`; owner `/root/assembly_occurrence`; delivery PR #121. Root owns the Windows oracle, Git operations and shared registers. This lane owns new source-authoring tools and this focused knowledge ledger. No native generated reference-plane feature or production writer is qualified.

Scope starts with one ordinary offset plane, a plane-supported centered circle sketch and a blind boss. Positive and reversed offsets on the three principal supports provide independent centroid predictions. The next source tranche will cover an angle plane, its axis reference and the separate angular dimension owner. Dependencies are the exact 2026 archive/model primitives, independently authored native sources, pre-writer held-out locks and complete field classification. Exit requires generated held-out native open, parameter edit, rebuild, save and fresh reopen at zero errors and warnings, with healthy controls and zero runtime file/CAD access during generation.

## Inventory and evidence limits

The [principal handle record](PrincipalPlaneHandles2026.md) covers model-owned default planes and their sketch support handles. The existing builder constructs principal planes and anonymous absolute planes used by drawings and mate wrappers. It does not construct a registered authored offset or angle feature. The repository search found no independently hash-locked 2026 authored offset/angle source cohort. The [historical metadata writer](MetadataWriters.md) is explicitly 2025 and donor-backed; its frame patches are not a construction model and will not be restored.

The current research schemas in `ResolvedBody.py` and `ResolvedRefGeom.py` model the common plane data, three-slot constraint interface and some coincident/parallel/perpendicular owners. They lack the ordinary distance/angle geometry records, the concrete default constrained-plane owner registration and the extra angular owner fields. A stored frame alone cannot establish the editable feature relationship.

All model addresses below refer to pinned `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`, from SOLIDWORKS 2026 SP05.2 `34.5.2.0604`. Class serializer/vtable identities come from the regenerated [2026 map](../../data/Serialization/SerializeMap2026.json). Independent original PE export, import and x64 instruction reads used the host Apple LLVM objdump. These are static observations, not runtime traces or native acceptance.

REA opened the exact model identity, but the first Hopper decompile reported foreign lease `a2f20739-b5bb-4081-8bb1-6dbda3f61bc1`. The task's metadata session was closed without touching the foreign document or process. No task-owned Hopper document remains open. Original PE analysis continued independently; unavailable pseudocode is not treated as evidence of missing code.

A separate bounded UI target did not complete Hopper bridge readiness within its 120-second startup limit. The retained evidence was exported privately; the subsequent task-owned close succeeded and `binary_session` reported `open=false`, `cleanup_pending=false`. No UI decompile was admitted. REA managed metadata inspection of the API module also reported a 64 MiB representation limit, not an absence of managed methods: parent evidence `ev_5942307e926d58e281048e07a08da57b355d0a3d56f9192f8f28dcb407fe535a`, summary `ev_9b2f8a182f113c517581669d2afd3559eb5960eea3e48ecd66349544f792a42f`.

## Constraint geometry inputs

Confidence for every new row is **partial**: exact 2026 store/load and constructor instructions were read, but the new authored source cohort is not yet measured.

| Owner / member | Encoding and meaning | Constructor / accessor | Archive order |
| --- | --- | --- | --- |
| `moRefPlaneGeometry_c.f08` | Object reference to the selected `moRefWrapper_c` | Owner-taking constructor `0x4c2d7920` stores the supplied wrapper; default constructor `0x4c2d7990` uses null | Base serializer `0x4c2d8b90`, first field |
| Geometry `f10` / `f18` | Two `f64` selected-location coordinates | Same constructors initialize the UV pair through geometry helpers | Base serializer, after wrapper |
| Geometry `f20` | `mgPoint_c` selected point | Same constructors initialize a point owner | Base serializer, after UV |
| `moRefPlaneDistanceGeom_c.f38` | `f64`, offset distance input | Constructor `0x4c2d7890`; getter `0x4b2bd110`; setter `0x4b34fc40` | Serializer `0x4c2d8ae0`, after complete geometry base |
| Distance `f40` | Canonical boolean, reverse direction | Constructor takes explicit boolean; getter `0x4b2b1c70`; setter `0x4b2b18f0` | One archive boolean after distance; load stores true only for input byte `1` |
| Distance `f44` | `i32`, plane count | Constructor takes count; default constructor `0x4c2d78e0` initializes `1`; getter `0x4b286250`; setter `0x4b2b3c20` | After reverse boolean |
| `moRefPlaneAngleGeom_c.f38` | `f64`, angle input | Constructors `0x4c2d7760` and `0x4c2d77a0`; getter/setter share the distance accessors | Serializer `0x4c2d8a40`, after complete geometry base |
| Angle `f40` | Canonical boolean, reverse direction | Explicit-boolean constructor `0x4c2d77a0`; the two-argument and default constructors use false | One archive boolean after angle; same load normalization |

Neither derived distance nor angle serializer adds a version gate around its own scalar suffix. This observation does not remove the base owners' version guards. Units, positive/reversed API conventions, selected-location UV semantics, count domain and concrete publication/factory paths still require the source correlation and targeted factory traces.

The constructor defaults establish initial object state only. They do not authorize substituting zero UV coordinates, zero points, count one or false reverse for a completed authored feature. Those values must follow from the declared selection and the exact active setter/factory path.

## Constraint-data ownership

`moConstraintRefplaneData_c` owns the computed plane through its normal `moRefPlnData_c` base and a separate interface object at `f88`. The owner-taking constructor `0x4b8e07d0` calls the common plane-data initializer, allocates `moConstraintRefplaneInterfaceData_c` and installs the supplied three geometry pointers in order at interface `f08`, `f10`, `f18`. Replacing each pointer marks runtime interface state `fa4=1`. The null/default constructor `0x4b8e0790` leaves the interface absent. The runtime arrays and marker are not automatically archive fields.

Serializer `0x4b8e2ac0` writes the complete common plane data and then the interface object, using the archive's ordinary object/reference mode. Interface serializer `0x4b8e2b70` writes exactly three object slots. On load it accepts null slots and otherwise checks each object's runtime ancestry against `moRefPlaneGeometry_c`. Thus selected references and the computed frame have distinct owners.

`moConstraintDefaultPlaneRefplaneData_c` shares serializer `0x4b8e2ac0`. Its active construction and its association with ordinary offset inputs still need the disclosed corpus and factory path. A name or a shared serializer alone does not prove that association.

## The extra angle owner

`moConstraintAtAnglePlaneRefplaneData_c` is a separate concrete class. Its constructor `0x4b8dfb40` calls the common constrained-plane constructor, initializes additional runtime point/selector state, inspects the actual geometry slots and may update adornments. It cannot be replaced by a default-plane payload with a rotated cached frame.

Its serializer `0x4b8e2930` writes the complete constrained-plane base, `i32 f148`, then object reference `f150` to `moDisplayAngularDim_c`. The load branch applies `safeSetFeatureOwner` at `0x4bb2c630` with the actual plane owner from `f10`, then updates its angle state. `setAngleDim` at `0x4b8f7dd0` releases an existing `f150` display, sets it null, calls the concrete angle setter through virtual slot `+0x230` and reinitializes the plane. A null display is therefore a lifecycle state, not proven complete writer admission.

The extra selector's final construction rule, complete display/parameter graph, axis-reference binding, annotation IDs and save/update lifecycle remain open. No angular writer is implemented from this partial table.

## Factory and API boundary

The exported `moConstraintRefplaneFactory::createRefPlane` at `0x4b27cbe0` is a folded null-return body. It does not identify the actual public construction route. The API layer must select a concrete factory or registered override. Treating that base export as the implementation would miss the active path.

The pinned mixed-mode API layer `sldcoreu.dll`, SHA-256 `3af88769b06bf7a1510fe52f279fbda20e5dc5548dc3925a1357e0f71cc3b3e3`, imports the default constrained-plane constructor and the explicit distance/angle geometry constructors. Its distance constructor import is at IAT `0x1801774f0`; its angle import is at `0x180177510`; its default-data import is at `0x180176c30`. Their native jump thunks require mixed-mode call-site analysis rather than a direct x64 call search. The UI layer `slduiu.dll`, SHA-256 `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7`, has a direct angle-constructor call at `0x492fb117` inside `0x492fafd0`–`0x492fb1fa`. These are leads for the next bounded trace, not proof of the public API path.

The native author will use registered COM library major `34`, `IFeatureManager.InsertRefPlane` and the matching feature-data interface. Its metadata-only preflight records the actual generated interface binding before any CAD session. Offset constraint code `8` appears in an official [2026 source example](https://help.solidworks.com/2026/English/api/sldworksapi/Create_Ref_Plane_SSMember_Example_CSharp.htm). The six-argument method, selection marks and reference-data access must still be verified on the pinned registered library and actual source controls. Older API documentation is historical context only.

## Next evidence

Prepare and run the offset-first API source cohort with a repeated control, unrelated offsets on Front/Top/Right, reversed placement, a driving circle radius and boss depth, and an actual plane-dimension edit. Compare body count, volume, area, centroid, plane/sketch transforms, selected principal support, native feature tree and all driving values. Retain original and edited saved siblings and fresh-read both. Seal independent source specifications and native artifacts before writer code, and expose no held-out values on the host. Root will bind the healthy native receipt and update the task register.

## Prepared offset-first source protocol

[ReferencePlaneSourcePhase.py](../../tooling/sw2026/ReferencePlaneSourcePhase.py) freezes the source scripts, pinned native control and four disclosed requests. [AuthorReferencePlaneSources.py](../../tooling/sw2026/AuthorReferencePlaneSources.py) first reads the registered major-34 method signatures and plane enums without CAD activation. Native phases then use the exact executable identity and explicit feature-data/plane interface GUIDs. Indexed feature-data properties use their registered property DISPIDs, with selection access bracketed by `AccessSelections` and `ReleaseSelectionAccess`.

The disclosed inputs are Front offset `13.79 → 24.53 mm` with radius `8.31 mm` and depth `6.47 mm`, an identical repeated case, reversed Top offset `27.13 → 14.71 mm` with radius `11.27 mm` and depth `4.19 mm`, and Right offset `19.37 → 31.63 mm` with radius `7.43 mm` and depth `9.11 mm`. These are independently authored inputs. Each source's expected cylinder volume is `πr²d`, surface area `2πr(r+d)` and centroid is the declared signed support offset plus the positive principal normal times `d/2`. The expected sketch origin and normal are checked independently of its observed transform. The source protocol deliberately fails if the API's reverse convention differs; a failed disclosed observation does not become a fitted writer rule.

Create an unused private packet with `prepare OUTPUT CONTROL --guest-private-base C:\KitReferencePlaneSources`, using the previously qualified control SHA `c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57`. Run frozen `verify`, then guest `run Source.json D00 metadata`. This first command starts no CAD process and publishes `ApiMetadata.json` for offline binding review.

The disclosed sequence is `D00 before`, then each `D01` through `D04` with separate `author` and `reopen` invocations, then `D00 after`. Each author phase creates original and edited native siblings and exports the edited geometry to `.x_t` and `.step`. Reopen uses a fresh process, zero open errors/warnings, rebuilds both exact siblings and checks all independent geometry, native tree, support and driving values. Raw disclosed receipts and native files are available only under the explicit `Disclosed/DNN` subtree. Always run the tail control independently after a failure; do not seal an incomplete cohort.

Only successful complete disclosed brackets permit `D00 seal`. That guest-only phase creates two independent source designs on a fixed private drive and publishes only their combined spec hash. Each hidden `H01`/`H02` then runs `before`, `author`, `reopen`, `after`, `lock` separately. Detailed hidden inputs, logs and artifacts never enter the host share or stdout. Source and edited native manifests must agree across author/reopen and remain unchanged at lock. Those sources are not held-out writer acceptance; they establish source-before-writer custody for subsequent independent generation.

The source phase tool never calls a Kit writer. Its producer is the native oracle and `writer_output_count` stays zero. The task remains active after preparation: native metadata/source qualification, exact constructor publication and remaining field classification precede new writer code; independent generated acceptance follows the source locks. Angle-plane axis references and angular display ownership remain the next separate tranche.

The first prepared packet is `9aad0b09e29433e61d0be577667fba399ca0d52310835b20b2bccff52c7afd08`. Its host verifier, Python parsing, analytic centroid displacement and refusal to create hidden designs or execute native phases on the host passed. [Preparation receipt](../measurements/2026/ReferencePlaneSourcePreparation01.json). No native case has run. The full initial source protocol uses ten native discovery processes and four bracketed native processes for each of the two held-out sources; metadata inspection starts no CAD process.
