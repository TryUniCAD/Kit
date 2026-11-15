# Computed field deletion

`DerivedFields` exposes authored inputs and readable computed values through one mapping. A computed key is present, but replacing or deleting it would break count and reference-index construction rules.

The mapping deliberately raises `ConstructionError` when an existing computed field is replaced or removed. A missing authored key instead reaches normal dictionary access or deletion and raises `KeyError`. The two conditions have different meanings and callers must not conflate them.

Changing the computed-field guard to `KeyError` has an additional consequence: CPython's inherited `MutableMapping.clear` catches that exception as normal termination. It could then return with computed keys still present. Keep the mutation guard and change authored inputs or their collections when a computed value must change.

The [implementation](../../../../../re/tooling/sw2026/builders/Sketch.py) and [review response](https://github.com/TryUniCAD/Kit/pull/121#discussion_r4577681134) document this contract. The [mapping protocol](https://docs.python.org/3.11/reference/datamodel.html#object.__getitem__) distinguishes missing keys, while [CPython's clear implementation](https://github.com/python/cpython/blob/3.11/Lib/_collections_abc.py#L933-L939) supplies the relevant inherited behavior. This assessment used source inspection without local execution.
