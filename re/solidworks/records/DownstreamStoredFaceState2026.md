# Stored ordinary face-reference state in SOLIDWORKS 2026

This source checkpoint maps three face-resolution branches and the fields retained after local model-context conversion. The field rules remain partial pending a dynamic trace of the complete construction and save path.

Task `B04-SW2026-DOWNSTREAM-STORED-FACE-STATE`, owner `configuration_header`, delivery PR #121. Root owns generated surface identities, prefix, live kernel handles, shared codec, product execution and vendor oracle. The exit condition for this checkpoint is reproducible source identity and explicit conditional construction rules, with unresolved branches retained. The separate temporary collector and its `+0x280` representation copies are unchanged.

The original `sldmodu.dll` has preferred base `0x4b140000`, size 46,536,280 and SHA256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Verification covers 69 complete function entries, 146 source intervals, 17 virtual slots, four runtime descriptors, 26 imports and nine direct-call sites. [Numeric ledger](DownstreamStoredFaceState2026.json) · [Source receipt](../measurements/2026/DownstreamStoredFaceSource01.json)

## Local model mapping retains the real owners

The generated cap class is `moEndFaceSurfIdRep_c` at table `0x4cf705a8`. The generated line or circle side uses `moFromSktEntSurfIdRep_c` at `0x4cf6ab10`.

| Slot | Exact target | Meaning in this selected context |
| --- | --- | --- |
| `+0x110` | `0x4bac8510`, then `0x4bb5dca0` | Decide whether this keeper needs model-context conversion |
| `+0x100` | `0x4bac8330` | Perform context conversion if required |
| `+0x280` | cap `0x4c6cf810`, side `0x4c6cfbe0` | Clone path for conversion that proceeds past the same-owner check |

The keeper's runtime feature is at `keeper+8`, equivalently representation `+0x18`. When a feature's virtual `+0x498` filed owner is the supplied model, the predicate returns false at `0x4bb5dd25..0x4bb5dd53`. Mode-0 externalization then returns before model lookup and conversion.

A direct `+0x100` call also returns the original representation at the same-owner comparison in `0x4bac8345..0x4bac8382`. The local representation, keeper, nested `moFR_c` and actual `moExtObject_c` file/configuration graph retain their identities and aliases. Missing or foreign features and forced mapping remain open. [Local owner rules](DownstreamLocalOwnerContext2026.md)

## Embedded role data has several identity domains

The embedded `BEnt.f18` record serializes the typed values below. Its backlink and candidate pointer list exist in runtime state. [Entity reference wire](DownstreamEntityReferenceWire2026.md)

| Field | Source owner and selected meaning | Fresh selected FaceRef value |
| --- | --- | --- |
| `f10` | Signed role mapped to an actual type-specific allocated row ID | Initial face roles, subject to later replacement |
| `f20` | Ordered nonzero incident **edge-row IDs**, produced by the VertexRef entity constructor | Empty |
| `f38` | Selected allocated **face-row ID** hint, produced by VertexRef construction or its late factory | 0 |
| `f40[0:2]` | Selected endpoint and opposite endpoint **vertex-row IDs**, produced by late EdgeRef repair | `(0,0)` |

The VertexRef constructor at `0x4b748be0` calls setter `0x4b53b4d0` at `0x4b748ecf`. Calls at `0x4b749750` and `0x4b759908` reach the face-hint setter `0x4b53b6c0`. The latter uses wrapper `0x4b7598d0`, called by the late vertex factory at `0x4b527484`.

The two-word setter `0x4b53b6f0` is called at `0x4b5364d2` when virtual `+0xf8` succeeds for EdgeRef. FaceRef and VertexRef return false. The repair reads actual vertex rows and uses the edge's `startVertex` or `endVertex` accessor to find the other endpoint. The selected repair record supplies the first word.

The executable-section scan pins nine direct E8-rel32 call sites. The privately retained complete LLVM function owners confirm instruction alignment. Indirect and inlined assignments are outside that scan.

For a fresh face in this profile, the embedded wire stores `i32(len(f10))`, its signed key/value pairs, then four zero i32 words for the empty `f20` count, `f38` and both `f40` words. Its length is `20 + 8*len(f10)`. The owner is present even when its arrays are empty. Read and preserve the payload of an existing owner as stored.

## Role0 is possible after the initial prefix

The initial constructor's own-face lookup precedes insertion of its current `f48` row. A later lookup can use that row after insertion. [Initial role lookup](DownstreamFreshFaceRows2026.md)

The replacement path constructs a new `CompFace(actual face)` at `0x4b52b50f` after append. The actual-face constructor `0x4b7e7180` requests mode 1 at `0x4b7e71e2`, so its own lookup can now find the allocated row and insert key 0. Replacement depends on the original and swapped-key validation and earlier rows.

The body representative gets its own role 0. Solid and surface body constructors call `0x4b802f40` at `0x4b7e8cfb` and `0x4b7e930d`. It finds the actual `f48` CompFace through `0x4b5288d0`, creates a new FaceRef through `0x4b74cb00`, retains it at body `+0xf0` and invokes `0x4b759a90` to install the role in a separate `f18` owner. Copy helper `0x4b755d80` installs a fresh inline array, copies selected scalar, vertex and version fields, and leaves `f70` empty.

## Three selected resolution branches

`f60` and `f64` have phase-dependent meanings. In final full candidate selection, `f60` is the filtered candidate-index count and `f64` is an ordinal into that index vector. The actual selected face is `candidate_faces[candidate_indices[f64]]` at `0x4bc13511..0x4bc1352a`. The temporary mode1 constructor's `f64` handle is a different phase.

| Selected branch | `f60,f64` | `fe8` | `f70` |
| --- | --- | --- | --- |
| Ordinary prism mode0, at least four distinct post-context reps, no special state or key replacement | `1,0` | 0 | 0 |
| Mode1 actual-part map resolves the own surface to the exact supplied face, recursively uses get0, publishes boolean0 | `1,0` | `0x200` | 0 |
| Mode1 full resolution, fresh empty body cache, exactly one real candidate in one valid classical body, ordinary initial flags | `1,0` | `0x300` | Actual selected `gcFace_w` handle |

The fast map branch at `0x4bc1298f..0x4bc12a5f` requires the part map at model `+0x1350`, a successful body predicate and exact supplied-face identity.

Full resolution searches at `0x4bc12cc0`. At `0x4bc133b1..0x4bc133f7`, the original supplied face can select a matching ordinal. One candidate yields ordinal 0. The call at `0x4bc136ce` passes the selected body, face and boolean 1 to publisher `0x4b759590`. In the ordinary direct-body branch, boolean 1 and a face set bits `0x100|0x200`. The store at `0x4bc136dd` puts the same live face in `f70`. Store emits its low u32 and load zero-extends it.

`f70` requires the actual live face handle allocated during kernel receive. Its allocation remains an independent source obligation.

A cylinder cap with one one-coedge loop has inline own/lateral/null rows and requests mode 1. A lateral face with exactly two one-coedge loops has own/capA/null/capB/null, three distinct nonnull representations, and also requests mode 1. Derive this decision from the actual topology, including seams and split faces.

`clearEntCache` at `0x4b74c510..0x4b74c56b` clears runtime body and cache owners and masks `fe8` by `~0x700`. The serialized `f18`, `f60`, `f64` and `f70` still retain their values after that call.

## Remaining construction and proof obligations

Open predicates include original and swapped-key equality, temporary map lifetime, candidate uniqueness, live face-handle allocation and forced contexts. A fresh generator must establish the branch before using its local-owner rules.

The next controlled root-owned proof is a generated actual surface/loop/component/atom graph with exact branch accounting, byte readback and then fresh native load/rebuild/save measurement. This tranche ran zero SDK product processes, zero native processes, zero VM calls and read zero CAD or held-out files. Neither `vendor_loadable` nor `application_usable` is asserted.

Run [VerifyStoredFaceSources.py](../../tooling/sw2026/downstream/VerifyStoredFaceSources.py) against the licensed original `--bin-directory`, this numeric `--record` and an unused `--output`. It hashes source ranges and typed table cells, and verifies the bounded rel32 inventory only. The [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md), [RE playbook](../../Playbook/README.md) and [Loader analysis phase](../../Playbook/LoaderAnalysis.md) apply before advancing.
