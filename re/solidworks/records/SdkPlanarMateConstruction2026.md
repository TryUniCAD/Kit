# Fresh typed planar mate construction in the SDK

The SDK constructs one complete aligned coincident or parallel mate subgraph from actual fresh assembly occurrences and actual child principal datums. Six independently authored bundles reproduce the unchanged research composer's complete parent container, every parent stream and child container byte for byte. This is a source construction and process-boundary proof. Public writing, new native acceptance and held-out qualification are not enabled by this tranche.

| Ownership | Value |
| --- | --- |
| Task | `B04-SW2026-MATES`, fresh SDK construction slice |
| Owner | `/root/assembly_occurrence` |
| Delivery | PR #121 |
| Scope | Archive version 19000; schema-one owned graph; one aligned coincident or parallel mate; two fresh direct resolved part occurrences; registered positive principal-plane datums; proper rigid placements; one explicitly fixed occurrence |
| Dependencies | [SDK MatesList codec](SdkMatesListCodec2026.md), actual parent Config/Resolved maps, child file/configuration/header identities, shared persistent-ID allocator, [self-component constructor](../../../src/convert/adapters/solidworks/Archive/Construction/Model/MakeSelfComp.py) and existing research document publication |
| Tranche exit | Guarded full-bundle identity, exact SDK mate read/write and actual alias checks, modeled length changes and atomic malformed-input rejection |
| Remaining product exit | Complete SDK assembly/child publication, public native output, extended mate graphs and independent held-out native open/edit/rebuild/save/reopen qualification |

## Construction API and admission

[`MakeMateMut`](../../../src/convert/adapters/solidworks/Archive/Construction/PlanarMates/MakeMateMut.py) accepts a `MateContext` and a `PlanarMateIn`. The context contains the actual assembly, its actual mate group, model header and active configuration, an explicit `FeatureTarget`, and the shared `PersistentIds` instance. The input contains kind, native feature name, two ordered `MateSelection` values, the actual fixed occurrence and an authored Unix creation epoch. Each selection carries the actual occurrence plus a `MateChild` containing the actual part, model header, active part configuration and feature inventory, and the selected datum node.

The constructor accepts `coincident` and `parallel`. Alignment is explicitly aligned. Distance, anti-alignment, multiple mates, nested occurrence paths, custom planes, assembly child datums and solver options remain outside this API's admitted profile. The distance display/parameter constructor is an independent promotion dependency; a valid distance reader is not a fresh distance writer.

Admission verifies actual identity and ownership rather than a numeric-ID lookup or a private builder annotation. Each occurrence must be a distinct member of the parent; its external-feature entry must point back to that exact occurrence; the selected plane and configuration must belong to the supplied part. Shared file kind/path/name/creation identity, selected configuration and current child update epoch must agree. Parent header allocation, direct occurrence counts and schema-one owners are checked before construction. Both initial solve states are `3`, both initial fixed flags are `0`, and the selected anchor must be one of those actual occurrences. Proper rigid transforms reject scaling, shear, reflection and nonfinite geometry.

The actual datum's `moDefaultRefPlnData_c` provides its origin, normal, native frame and display bounds. Its full basis is read from the native matrix columns; `_principal_axis`, `_plane_u` and `_plane_v` annotations are not inputs. The positive canonical normal selects the native discriminator 1/2/3. [Principal-plane framing](PrincipalPlaneHandles2026.md) and [endpoint construction](AssemblyPlanarEndpointConstruction2026.md) establish this interpretation.

## Field ownership and knowledge

The pinned native image is SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`, `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. This promotion reuses existing independently retained constructor/setter/serializer evidence. It does not claim a new native trace or application measurement. No Hopper document was opened in this slice.

| Owner and fields | Classification and rule | Evidence and status |
| --- | --- | --- |
| Generic node/concept/feature and `f35c` model-feature base | Native constructor constants and independently owned empty option state; actual owner/name; explicit release date/kernel/version; shared optional persistent allocation | [Model construction](ModelConstruction2026.md), [mate publication](CoincidentMatePublication2026.md); confirmed native rule, guarded equivalent construction |
| Mate `f2a0/f2a4` | Derived signed low/high words of `(created_at + 11644473600) * 10000000` | Registration lifecycle in [publication](CoincidentMatePublication2026.md); confirmed |
| `moMateCoincident` versus `moMateParallel` | Authored kind chooses the actual native concrete class; common two-geometry factory inheritance | `0x4bc42030`, initializer `0x4bc5d920`, concrete descriptors in [wrapper factory evidence](PlanarMateWrapperWriteState2026.md); confirmed |
| Mate `f3b4` | Authored explicit alignment yields internal value `1` | API/command/model edge and setter `0x4b2cfe10` in [input translation](PlanarMateInputTranslation2026.md); confirmed |
| Mate `f3b8`, optional owners/arrays/strings | Native pre-solve zero and absent ordinary auxiliary state; no finished saved solver status is copied | Constructor `0x4bc2db40` and its derived constructor fields in [wrapper factory evidence](PlanarMateWrapperWriteState2026.md); confirmed |
| Chain component, chain and one-entry external-feature list | Actual parent and occurrence backlink; fresh acquisition/mode/configuration state; stamp `(101 + occurrence.f3f0) & 0xffffffff` | [Exact chain constructor and loader proof](PlanarMateReferenceChains2026.md); confirmed |
| Selected component-plane `ff0`, `ff8`, `f100` | Actual child datum ID and first matching child creation event, or native unset epoch `2592000`; no inline plane for registered selections; discriminator derived from actual principal normal | [Feature-reference lifecycle](ModelConstruction2026.md#feature-reference-creation-time) and [wrapper construction](PlanarMateWrapperWriteState2026.md); confirmed |
| Resolved `f08/f0c`, `f10/f18`, `fd0/fe8/f100`, `fb0/fb8/fc0/fc8` | Current child update/configuration; independent placement-cache copies; transformed datum origin/basis and inverse plane frame; actual child bounds | `iUpdateLastAccess` `0x4c3290f0`, transform helper `0x4c3292c0`, [endpoint rules](AssemblyPlanarEndpointConstruction2026.md); confirmed native rule and exact process comparison |
| Detached `f3c8` graph | One separate unnamed/unregistered absolute plane and owned self-component per endpoint; world root/normal, identity frame and zero bounds; original datum in `f9c`; parent stamp/configuration | `createNewPlaneRef` `0x4b68f39d`–`0x4b68f578` and [constructor proof](PlanarMateWrapperWriteState2026.md#detached-and-resolved-plane-identity); confirmed |
| Resolved wrapper `f74/f78/f7c`, parent `fd48` | Mate persistent ID, old parent wrapper counter plus endpoint ordinal, local endpoint ordinal; parent counter advances by two | Traversal `0x4c1bf830`, assignment `0x4c333fd0` in [publication](CoincidentMatePublication2026.md#wrapper-ids-consume-a-separate-counter); confirmed |
| Occurrence `f408` and unchanged `f400` | Authored anchor changes only the fixed flag; pre-solve state remains independent | Native `fix` and solve-state storage in [wrapper evidence](PlanarMateWrapperWriteState2026.md#fixed-occurrence); confirmed |
| Feature `owner` and runtime group attachment | Actual constructor ownership is retained in memory. Generic feature serialization does not emit that runtime pointer; group attachment is a separate loader operation | [Publication and loading](CoincidentMatePublication2026.md#stream-owners-and-disclosed-comparison), [specific gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/FeatureOwnersAreNotMateWireFields.md); confirmed scope, not a new owner word |

Inverse-frame translation preserves the native operation order: compute `0 - origin` componentwise, then dot that vector with each world-plane axis. Replacing this with a leading unary negation of the finished scalar can change IEEE signed-zero words. No matrix or transformed cache is taken from a saved file.

All endpoint graphs and feature fields are constructed before the shared allocator, parent wrapper counter or fixed flag changes. A rejected input leaves those parent publication fields unchanged. The constructor returns the complete mate subtree; it does not silently update a header log, configuration progress, a container or another document. The existing document composer remains responsible for those separate, already modeled publication operations.

## Shared primitives

[`Nodes`](../../../src/convert/adapters/solidworks/Archive/Construction/Nodes/) provides generic node/concept initialization, native entity visibility, a release target, registration FILETIME and persistent IDs. `InitFeatureMut` takes a caller-preallocated empty schema-one node, an authored optional name, actual owner, target and optional allocator. It shares the independently mapped feature base without claiming that an arbitrary concrete native class is qualified. The mate-facing `MakeFeature` and `MakeModelFeat` retain explicit concrete admission.

[`Geometry`](../../../src/convert/adapters/solidworks/Archive/Construction/Geometry/) provides finite proper-rigid interpretation, plane frames and row-vector transforms. `IdentityXform.py` and the four node/concept/ID primitives are shared dependencies delivered with the independent Definition and part-root tranches. Identity, ID-seed and concept initialization stay byte-exact. The current tranche makes two mechanical static-check repairs to the already committed ID/node primitives: `PersistentIds.__init__` calls the object initializer, and the existing allocator runtime guard explicitly casts its argument to `object` before checking. Historical source/proof identities remain intact; a fresh frozen comparison binds the corrected source and requires identical generated outputs.

## Process proof and reproduction

[`CheckSdkPlanar.py`](../../tooling/sw2026/CheckSdkPlanar.py) freezes the entire Python source closure before generation, with no vendor payload, saved CAD source or opaque input. For each neutral design it starts separate SDK and unchanged-reference interpreter processes. Both run the real part/assembly composition and container codec. The SDK lane substitutes only the fresh mate factory and its actual SDK `WriteMatesMut`; the rest of document publication stays unchanged. Temporary Python hooks are scoped to that process and restored. No research builder or vendor dependency is imported by the production constructors.

The six authored designs cover both mate kinds, all principal axes, three distinct contour topologies, identity/rotated placements, both endpoint orders, independent translations, a non-ASCII feature name and explicit registration epoch. Comparison requires whole parent container equality, equality of every parent stream, whole child container equality and exact actual-map SDK mate read/write. Constructor and decoded-wire checks require actual ordered occurrence backlinks and independent detached component/plane ownership. Runtime-only generic feature owners are checked at construction and are reported separately from serialized component-owner aliases.

Twenty malformed inputs exercise foreign/repeated occurrences, external backlink, child configuration/update, datum ownership/registration/bounds, scale/reflection, foreign fixed input, parent allocation/counter bounds, unsupported kind, name/epoch, parent/child schema/version and finite placements whose inverse-frame projection overflows. Every rejection happens before a parent artifact is emitted and leaves allocator/counter/fixed state unchanged. The permanent integration entry points are [`SdkMateTests.py`](../../../tests/Convert/Solidworks/Research/Mates/Construction/SdkMateTests.py) and [`SdkMateFaultTests.py`](../../../tests/Convert/Solidworks/Research/Mates/Construction/SdkMateFaultTests.py); they call a fresh interpreter with neutral stdin and exercise actual native graph/container boundaries.

```sh
uv run --isolated --frozen --extra dev --python 3.11 python -I -B re/tooling/sw2026/CheckSdkPlanar.py \
  --root /absolute/path/to/trusted/source \
  --output /absolute/path/to/unused/construction-proof
```

[Sanitized receipt](../measurements/2026/SdkPlanarMateConstruction01.json) binds exact source/proof hashes, process identities, native field coverage and stream sizes. It explicitly records no native application launches, no native acceptance, no held-out reads, no runtime input-file access and no public writer enablement. The research composer remains the complete-document scaffold; this tranche alone is not a complete SDK assembly writer.
