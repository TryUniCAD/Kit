# Fusion can reorder fixed cuboid parameter observers on save

A freshly generated cuboid lists its parameter search observers
in creation order. Fusion 2706.1.17 saved the edited and restored
copies with the same table first, followed by the parameters in
ascending Design object identity. Their creation indices, names,
bindings and observer ranks remained the same. The original
reader refused the rewritten observer list despite those matches.

Keep the stored order in typed state. Validate either observed
order against the complete parameter table and preserve exact
observer counts, identities, ranks and names. An unrelated owner,
a missing or repeated subject, the wrong rank or another order
still indicates unqualified state.

[Measured saved copies](../../../../../re/Fusion/SavedCuboidRoundTrip/DisplayOrderContrast.md#generated-cuboid-native-lifecycle-and-observers)
