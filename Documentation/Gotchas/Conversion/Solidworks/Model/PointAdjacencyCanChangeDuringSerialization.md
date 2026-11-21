# Point adjacency can change during native serialization

## Expectation

A native save only observes point adjacency and cannot change an existing pointer.

## Actual behavior

The pinned 2026 point serializer has a store branch that can change the point's adjacency members. For the ordinary profile path, it tests each nonnull handle through actual virtual slot `+0x2d8`. A zero result clears that pointer before writing. The members are point `+0xf8` and `+0x100`, corresponding to point `h1/h2`. They differ from the value dimension's embedded geometry handles at `+0x130/+0x158`.

The original serializer span is `[0x4c58f910,0x4c590557)`, SHA-256 `281ad8aacf682f14bbca0af3ff839ab74262ebc50afdba7ceea7a916f257193b`, in model image SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Relevant reads and clears occur at `0x4c58fb8d` through `0x4c58fbe6`. This is static native evidence, not a new measured training result.

The rule can remove an existing pointer. It does not explain how a centre acquired a nonnull handle, determine the runtime predicate for every concrete handle, or prove the cause of a particular saved mismatch. Constructor clones, point role-use counts, centre-use counts, retained adjacency and serialized presence are separate facts.

## Workaround

Observe the actual authoring route and compare point adjacency before and after native serialization. The [training observer](../../../../Changes/Solidworks/Inspection/Sketches/SolidworksRadialTrainingObservations.md) adds the two bounded pointer records to its existing point loop; it does not duplicate the array decoder or invoke the predicate. Preserve concrete handle/vtable/index identity and capture the predicate target for subsequent binding. Keep incomplete states explicit.

The [native observation record](../../../../../re/solidworks/records/RadialTrainingObservation2026.md) and its complete identity metadata give field ownership, module hashes and open questions. Do not copy a saved null pointer or retained handle into a writer default. A chosen neutral construction policy still needs independent native acceptance.

The separate [circle registrar proof](../../../../../re/solidworks/records/CircleAdjacencyRegistration2026.md) explains single `h1` through deduplication while role uses reach two. Serializer cleanup is not required to explain that graph.
