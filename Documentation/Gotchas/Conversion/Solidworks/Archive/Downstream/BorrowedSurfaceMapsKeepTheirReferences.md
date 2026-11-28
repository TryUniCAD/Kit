# Borrowed surface maps keep their references

## Expectation

Leaving `tempEdgeHelper` always destroys the part's surface map and clears every reference that used it. Destroying a comparison-key pointer array also releases the external model objects it names.

## Actual behavior

The exact 2026 ordinary part table returns false at virtual `+0x16e0`. The analyzed setup borrows actual model `+0x1350` and records `bb8=0`; its destructor skips the owned-map detach/destruction branch. Remaining nested map cleanup frees raw containers without invoking pointer-value destructors.

After successful collector-vector transfer, the old collector pointer is null and its representation-release loop is skipped. Separate comparison-key objects own their buffers, but their concrete scalar destructor does not release external objects inside the pointer buffer. The common object base has real process-global bookkeeping, so it should not be called an empty destructor either.

## Workaround

Track the actual helper setup, concrete virtual target, transfer and container element ownership. Preserve retained aliases and field values on this selected borrowed branch. A foreign or already-active helper needs its own ownership proof; the global-holder early return does not itself establish the borrowed state.

[Exact source record](../../../../../../re/solidworks/records/DownstreamReferenceTeardown2026.md) · [Source replay](../../../../../../re/solidworks/measurements/2026/DownstreamReferenceTeardownSource01.json)
