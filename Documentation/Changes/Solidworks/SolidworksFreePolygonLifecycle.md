# SOLIDWORKS free-polygon lifecycle evidence

The construction ledger now correlates native authoring, rebuild and save observations for three unconstrained polygon sketches with the existing constructor and update rules
It records shared endpoint identity, native point counts, solver-status mapping and modification stamps
Use [the free-polygon observation](../../../re/solidworks/records/ProfileConstruction2026.md#free-polygon-authoring-and-rebuild-observation) when reviewing fresh local 2D profile state

The stamp rule remains computed from the graph
The native constructor starts at one, line permanence increments once per constructed line, and the observed updates add no coordinate changes
For this construction sequence the expression is `1 + len(lines)`
In the free-ring training updates, all ordinary point and line mapper calls return status one, which the native aggregate retains; saved status remains separately one
This records evidence for existing behavior and does not change the builder or adapter capabilities

The capture contains 8,543 events, no dropped events or script errors, healthy original controls and three native-authored one-body parts with successful rebuild and save results
It corroborates three-, eight- and eleven-line shared-point rings with zero authored sketch relations
These are training observations after the family implementation, not held-out acceptance of generated output
The origin observations start from template-loaded state and do not establish its first constructed solve
Research metadata `_requires_update` is not a serialized native flag and does not cause application regeneration by itself
Generated-file loading, full origin update, rebuild, body measurements and driving-dimension edits remain unverified

No local tests, builder imports, reproductions or oracle calls were run for this documentation change
Verification used the existing capture, static native disassembly and diff checks
