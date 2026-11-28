# Ordered internal SDK planar assembly construction

`MakeOrderedAsm` constructs a complete assembly with an ordered group of
aligned coincident, parallel and positive driving distance mates on two
placements of one actual generated plain child. It shares the existing mate
graph factories, dimension construction and persistent allocator. The normal
adapter writer remains disabled.

The optional `MateContext.PreviousValues` preserves existing empty-context
behavior. Continuation verifies actual prior objects, wrapper IDs, the same
fixed anchor, allocation registration, configuration progress and header logs
before allocating the next mate. Cloned nodes and inconsistent or missing
prior state reject without advancing observed publication state.

The research checker freezes its source before generation and verifies
independent complete-stream construction and readback, all six orders of the
three supported families, two plain-child/placement variants, atomic prior
state rejection and byte-identical existing bundle regressions. The internal
API still excludes dimensioned children, mixed or nested definitions,
unsupported mates and arbitrary saved graphs. Ordered native lifecycle and
held-out qualification remain separate requirements.

[Construction rules and evidence](../../../../../re/solidworks/records/SdkOrderedAssemblyConstruction2026.md) ·
[Process receipt](../../../../../re/solidworks/measurements/2026/SdkOrderedAssemblyConstruction01.json)
