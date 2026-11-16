# Lazy fields retain mapping ownership

## Expectation

A typed archive node can normalize its field payload to `dict` without changing how generated fields behave.

## Actual behavior

The fresh sketch builder's `DerivedFields` implements `MutableMapping` and computes derived values in `__getitem__`. Its key iterator exposes authored and computed keys without evaluating the computed values. Converting that provider to `dict` evaluates and freezes those values during construction, losing later count and reference-index updates.

This is a source-level ownership finding from [the builder](../../../../../re/tooling/sw2026/builders/Sketch.py) and the existing [computed-field deletion contract](../Profile/ComputedFieldDeletion.md). It is not a new native measurement or a captured default.

## Workaround

The [typed archive model](../../../../Changes/Solidworks/Model/SolidworksArchiveObjectModel.md) accepts `MutableMapping[str, object]` and retains the exact caller-owned mapping. Validation visits keys only; it neither copies the mapping nor reads its values. The body registry reads a computed field when that field is actually serialized.

Map snapshots separately copy membership while retaining node identities. Neither snapshotting nor compatibility adaptation may deep-copy nodes or materialize their payloads as an incidental normalization step.
