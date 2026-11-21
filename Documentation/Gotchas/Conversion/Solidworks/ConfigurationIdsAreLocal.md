# Configuration ids use a separate allocator

## Expectation

Every node's saved id comes from the document header's persistent-id counter.

## Observed behavior

The 2026 base-configuration constructor assigns its id from the configuration
manager's `f40c` counter.
The helper returns the current value and then increments it.
This namespace is separate from ordinary model-node persistent ids.
The [construction record](../../../../re/solidworks/records/ModelConstruction2026.md)
identifies the exact constructor and helper addresses.

## Workaround

Allocate configuration ids from their own manager.
Keep ordinary persistent ids and archive map references separate.
Do not increase the header's next-id value merely because a configuration exists.
