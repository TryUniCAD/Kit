# Pending origins need a serialized update flag

## Expectation

A dirty part or descriptive builder metadata will cause the target application to solve every unsolved feature

## Actual behavior

The native origin initializer clears its update flag only after calling the sketch solver
The research factory previously applied that clear while retaining constructor sketch and point states
Its `_requires_update` metadata is not serialized

The actual part prepass calls per-feature admission helper `sldmodu 0x4c1d0110`
That helper first tests the feature's own needs-update result
Root dirtiness alone does not supply that result for an ordinary part
An empty earlier-change map can reject a clean feature before later profile-specific fallbacks

## Workaround

Keep the fresh origin node's native constructor `f0c` bit zero set until its first solve
Generate the bit through the model constructor rather than copying solved status or colour from a saved document
Verify the emitted flag through complete profile serialization and decoding
Keep target acceptance separate from static admission proof and archive round trips

The [construction ledger](../../../../../re/solidworks/records/ProfileConstruction2026.md#pending-origin-admission) binds the full path to the 2026 binary
