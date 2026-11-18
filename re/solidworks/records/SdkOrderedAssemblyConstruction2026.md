# Ordered SDK planar assembly construction

The SDK constructs an ordered group of ordinary aligned coincident, parallel
and positive driving distance mates on two placements of one actual generated
plain child. It reuses the existing mate factories and actual persistent
allocator. It never resets the previously fixed occurrence or substitutes
synthetic parent state to bypass the fresh-mate guard.

## Ownership and admission

| Item | Scope |
| --- | --- |
| Task | `B04-SW2026-ASM-SDK-ORDER` |
| Owner | PR #121 ordinary assembly lane |
| Delivery | PR #121 |
| Base | Complete single-mate SDK assembly tranche `210cf5c0ed230f1e728a58cbf91e4cb2ed50e40a` |
| Dependencies | Actual plain `PartCandidate`, ordinary assembly graph and metadata constructors, shared coincident/parallel/distance factories, linked MatesList codec |
| Exit | Complete ordered generated graph, independent process/stream verification and preserved single-mate outputs; separate native lifecycle and applicable held-out qualification before promotion |

`MakeOrderedAsm` accepts a nonempty ordered tuple of `AssemblyMateIn`, with
distinct names and one common fixed occurrence. Its child, configuration,
placement and principal-plane scope is identical to the
[single-mate constructor](SdkCompleteAssemblyConstruction2026.md).
Dimensioned children, different child definitions, nested assemblies,
unsupported mate kinds, arbitrary saved mate graphs and public adapter writing
remain outside this API's admitted construction scope.

`MateContext.PreviousValues` defaults to an empty tuple. Existing callers keep
the same fresh-state admission and emitted bytes. A continuation supplies the
actual previously constructed mates. The context is an in-memory construction
contract; it adds no native field, stream, map entry or wire discriminator.

## Allocation and publication rules

The native wrapper collector visits each mate's actual ordered `f410` list.
For a new resolved wrapper, it takes the containing assembly's current `fd48`,
increments that counter and writes the owning mate ID and local endpoint
ordinal separately. Therefore wrapper IDs continue `0,1,2,3,...` while local
ordinals repeat `0,1` for each mate. The instruction proof explicitly covers
later wrappers rather than assigning every pair its local ordinals as global
IDs. [Native registration and wrapper allocation](CoincidentMatePublication2026.md)

The existing coincident/parallel and distance factories now share a small
state validator. An empty prior tuple still requires two fresh unfixed
occurrences. A nonempty prior tuple requires the same actual anchor, fresh
unsolved constructor state and a complete previously published prefix:

- Every prior mate has the supported concrete schema-one class, actual mate
  group owner and aligned constructor state.
- Each resolved wrapper retains its actual occurrence backlink and parent,
  its mate ID, global wrapper ID and mate-local endpoint ordinal.
- Prior persistent IDs are ordered, distinct and later than the existing
  parent identities. A distance dimension precedes its mate and retains its
  real display/handle/value chain.
- Each prior mate and dimension is registered by actual object identity in
  the same `PersistentIds.Allocations`. A cloned node with matching numeric
  fields is not an allocated prior object.
- The allocator, model wrapper counter, configuration watermark and ordered
  header creation logs all describe that same prefix.

After validation, the existing graph factories allocate the next actual
dimension if needed, then the next mate and its two wrappers. Both headers
receive the actual mate creation log, and the independent configuration
watermark advances. No new graph constructor duplicates the existing larger
mate, detached-plane or dimension construction. A malformed prior prefix
rejects before changing any observed allocation or publication state.

Final stream emission carries the actual configuration map through resolved
features into one MatesList containing every authored mate in input order.
The resolved group's wire child list remains empty. The same existing model,
occurrence, bounds, manager-header, Definition, history and XML constructors
serve single and ordered candidates.

## Evidence and limits

`CheckSdkOrderedAssembly.py` freezes the full Python closure, then compares
separate generated, independently decoded/re-encoded and mathematical
counterpart processes. The disclosed generated designs exercise all six
orders of the three qualified mate families, two unrelated plain children,
proper rigid rotations, translations and both anchor choices. Each parent
has twelve streams and each child ten. Their graph data is generated from
the authored neutral child and explicit construction settings; no vendor
payload supplies a constructor input.

The [sanitized process receipt](../measurements/2026/SdkOrderedAssemblyConstruction01.json)
records final source and output identities, complete stream comparisons,
atomic negative cases and unchanged single-mate/historical regressions.
The final result is SHA-256 `5493223761bfe60d898a63710a9a08c03760ba432bd0b3d902741e4b74e02857`, with source manifest `2c540bca6cf921ed507c4ef0b7bcc9d1e34a299cd89cbc593d10c8001a2918e4`. It covers 12 complete ordered bundles, 20 atomic negatives, 18 unchanged complete single-mate bundles and 12 historical bundle regressions across 122 fresh workers and 660 typed stream round trips. Two permanent process integrations passed in 53.53 seconds. Scoped Black, Ruff, strict Mypy, Pyright and steering checks passed. Earlier proof snapshots remain private and immutable. Native execution and
sealed inputs are excluded from these source-process measurements. The
separate first single-mate native result does not qualify an ordered group.

Decoded native feature owners are loader attachments. These guards admit
fresh constructed objects with actual ownership and allocation, not an
arbitrary decoded mate list. [Owner-field distinction](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/FeatureOwnersAreNotMateWireFields.md)
Release portability retains the existing version-19000 and concrete-schema
guards. Public adapter writing and ordered native acceptance remain disabled.
