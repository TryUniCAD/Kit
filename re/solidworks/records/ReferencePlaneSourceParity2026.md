# Offset-plane source and generated tree parity

Full paired source/generated acceptance is unfinished. The earlier disclosed generated Front case passes its own native persistence and geometry checks, but its source control has 26 recursive rows and the independently authored generated model has 27. A private generative correction and strict paired observer are prepared; neither hidden source has been exposed.

Task `B04-SW2026-REFPLANES`; owner `/root/assembly_occurrence`; delivery PR #121. Scope is the ordinary principal offset plane, centered radius-driven circle and blind boss. Dependencies are the pre-writer [source lock](../v2026/heldout/ReferencePlaneSourceLock01.json), shared constructors, [native markup roles](MarkupFolderConstruction2026.md), [explicit authored folder order](PartFolderOrder2026.md) and the [previous disclosed evidence](ReferencePlaneOffsetNativeDiscovery2026.md). Exit requires exact ordered native source/generated tree and semantic identity, working edits/save/reopen and controlled blind qualification. Root owns shared Part/Model integration and every Windows invocation.

## Existing roles cover the system-folder difference

The earlier request deliberately used authored folder captions and a top-level `moNotesAreaFtrFolder_c`. The native source uses `moInkMarkupFolder_c`; native annotation note areas remain children of `Annotations`. The already implemented [MakeTreeInput](../../../tests/Convert/Solidworks/Research/Presentation/MakeTreeInput.py) supplies that distinct markup role and independently authored standard English presentation names. Its earlier [native tree-parity evidence](../measurements/2026/TreeParityInspection01.json) is separate from this new plane trial.

The source recipe now uses that existing factory and derives `folder_order` from the authored mapping before JSON encoding. It never derives an order from saved rows. The explicit sequence survives sorted JSON and the shared allocator constructs the corresponding folder objects normally. No new Model mutation is proposed here.

## Origin publication precedes the authored plane

The locked source author calls `new_part` before `InsertRefPlane`. The ordinary model already owns its principal planes and document Origin when the new datum is published. The old offset hook instead allocated the plane's distance and plane before constructing Origin, then emitted `OffsetPlane` before `Origin`. Geometry and self-persistence do not establish preservation of that history order.

The independently proposed private Part patch changes two related construction boundaries: allocate Origin before the new plane's dimension/feature, then publish `systems → Origin → OffsetPlane → profile → boss`. The document Origin still references the actual principal support at world zero. The new offset plane and sketch keep their separate translated frame. IDs, references and archive maps follow the shared allocator and graph. The non-offset route is unchanged in output.

The actual pinned `moRefPlane_c` primary vtable is `0x4d16f278` in `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Its part-insertion predicates match the ordinary profile/extrusion path already traced in [Model construction](ModelConstruction2026.md):

| Slot | Actual target | Complete leaf result |
| --- | --- | --- |
| `0xd18`, `0xd20`, `0xc48`, `0xd10` | `0x4b27cbe0` | integer false |
| `0x1450` | `0x4b27e150` | integer true |
| Owner callback `0x1288` | `0x4bb51930` | Existing owner-preserving callback |
| Linked-child connection `0x4d8` | `0x4b2fe0b0` | Existing reference-count callback |

Thus the reference plane does not enter the special-folder branches merely because it is a datum. The existing part insertion `0x4c1c5040`, linked insertion callback `0x4bdacc50` and ordered node-list storage `0x4c1799b0` remain the shared rules. This finding does not assert a universal insertion order under rollback, edits or other feature kinds. The private static receipt SHA-256 is `0352c488641e610c231fb36a737957927c055da1f1abf07b85471f47894c7526`. No vendor listing or code bytes are committed.

## Pure disclosed recipe and prediction boundary

[ReferencePlaneSourceRecipe.py](../../tooling/sw2026/ReferencePlaneSourceRecipe.py) admits only the four published disclosed authored specifications. Its strict input schema contains the part name, principal support, reverse flag, distance, radius, blind depth and independent edit. A native source path, saved field, stream, cache, observation or additional input key is not accepted. Hidden slots remain rejected by this provisional mapper.

The recipe uses the existing authored Part and native-role factories. The case's base selects its principal axis; the scalar inputs drive the real offset-plane, circle and boss graphs. Circle text is authored at local `(1.7r,1.3r)` and transformed onto the independently predicted offset plane. The canonical Right basis is `U=-Z, V=+Y, N=+X`; Top is `U=+X, V=-Z, N=+Y`; Front is `U=+X, V=+Y, N=+Z`. A cross-product guard checks handedness. These are the existing [principal-plane frame rules](PrincipalPlaneHandles2026.md), not saved text positions.

The independent prediction uses the pre-writer source-plan circle equations, including `O=sign*d*N` and `COM=O+depth*N/2`. It records the required ordered semantic features and requires full source/generated tree and semantic identity, as well as generated baseline/edit/reopen tree equality. Requests and predictions are locked before any subsequent native CAD file access. The standalone writer receives stdin only and cannot read the native source or its observations.

## Frozen private preparation

The [preparation receipt](../measurements/2026/ReferencePlaneSourceParityPreparation01.json) binds the exact source and proof identities:

| Identity | SHA-256 |
| --- | --- |
| Private Origin-before-offset patch | `f63ec04aa249f2e0747cd7f1038fb77167222a86b3f24dd3ed701a660a83ea65` |
| Private Part constructor | `8793833bbf820c978d5f24e3cd7876a78052b33bf7cdcf775a6d5caade56c5e3` |
| Existing explicit-order Model | `4bdd7397c1e7ba639fdb322a4b997c66ec0fc434341e830ac5adc274b0d4220e` |
| Complete 3,880-file Python closure | `f0972b72944fa36d6b884b4968501ca9b7411da7f705d0ab3d307c9b951dd589` |
| Pure disclosed recipe | `67ec69705ee992ef62efd3ecd40e69d709d2fc57337be0b2a7757e52b126efc2` |
| Pre-access request/prediction lock | `2108e23be27c6ed0f4e860b1f7934e9cc84a1da6bc45d600c45249e25cefff15` |
| Guarded construction proof | `9ac2e9eff5342abd3cf60eef3355d5dad73989eb267953ea5ba346597426dcbe` |
| Disabled paired native plan | `4347960ef76c9c76e642d8c499cefa31eabc8c170d12b9d5b8e37a0831e9b8aa` |

Each disclosed case passes two fresh guarded processes, eleven round trips per build, deterministic output and zero runtime input-file reads. The exact D01 candidate is 8,634 bytes, SHA-256 `9a565b31ab2fcb750f993ab3e7249316f1437712aed879445f2a3986b72d922e`. A rectangle and circles on all three origin frames retain identical serialized bytes across the private Part change. The compatibility checker normalizes only code-root locations in import and schema-source audit metadata; artifact and semantic fields remain identical. The prior compatibility proof is `24ea61220f0b1a385858b3a2f087c288ff549dc95b9e6f7ea99091141a1830e6`. The latest closure changes only the pure recipe's corrected Right text basis relative to that proof.

The first provisional mapper had transposed the Right text basis. This was corrected before native or hidden use; the first disabled plan remains unchanged at SHA-256 `e2c3c731bf705ca0c69d7a18f4a625e2c17a2cbd4e80e863cafed4e7fe21b660`. D01 and the private writer patch did not change. These are preparation corrections, not vendor acceptance results.

## Typed instrument difference remains visible

After its request/prediction lock, an independent two-file audit reads only the exact disclosed D01 native source and generated candidate. Both have 20 named resolved roots, twelve scoped stream round trips pass and linked Config/Resolved identities re-emit exactly. Plane, support, profile and driving inputs agree. The core Origin/plane/profile/boss sequence agrees.

The full raw resolved-root list is nevertheless unequal: the source's cabinet is physical root `6`, while the generated cabinet is physical root `12`. Receipt `7417ff440c02b17d618520aa3d46858563540dc28947b8b970c7fe3c9f7b1356` keeps that typed comparison failed. Both earlier live trees already place their cabinet at native row `6`, so physical root order and the measured UI tree must remain distinct instruments. No cabinet patch or captured source order is added. The next native trial must decide complete ordered UI-tree equality directly.

## Strict paired observer and release gates

[InspectPairedReferencePlane.py](../../tooling/sw2026/InspectPairedReferencePlane.py), SHA-256 `4054e64c5ad56deb3260147f57979e0a7e094e4fef8e05783c4dcd9531771b25`, reuses the exact native measurement helpers from the passed second disclosed trial. It adds source/generated full ordered native-tree equality, exact plane types/constraint/parent/frame and parameter/display ownership identity, generated initial/edit/reopen tree equality and unchanged source-bracket identity. Existing independent geometry and edit tolerances remain fixed. Every difference and row count is retained, including when geometry and self-persistence pass.

Its `verify PairedTrial.json --packet-sha256 SHA` checks the complete source/tool closure, authored disclosed case, regenerated request and independent prediction. The prepared packet has `state=prepared`, `execution_enabled=false` and no writer revision. `run` refuses that state, requires Windows and an actual committed writer identity, and checks the physical guest root against the encoded generation path before creating native output. Root alone can create and execute a newly frozen release packet after reviewing and integrating the private patch.

The intended four phases are unchanged source before, generated rebuild/distance edit/save, fresh edited reopen and unchanged source after. Source and generated use the same authored D01 specification. Both healthy source controls, four distinct ordered identities, immutable inputs, full paired tree/semantic equality and generated persistence are required. A failed candidate still reaches the tail control.

A separate process replay on actual prior native records accepts the two healthy source-control snapshots and rejects the unmatched 26-versus-27-row generated model. Receipt `82ef899b631197c905eee86afb93f43442971a7fc5482722e52006fbc5dd5d2c` records this comparator behavior with no CAD launch or hidden read. It does not qualify the new native observer.

The private paired candidate must pass this disclosed gate before either hidden design is exposed. Then freeze the complete actual writer, recipe translator, independent predictor and strict observer again; lock code first, then the guest-only authored specification and recipe/prediction, then generated bytes, and only afterward access native comparison inputs. A blind failure remains a failure. Source authoring, recipe generation, typed readback, self-persistence, paired native acceptance and full production conversion remain separate evidence levels.
