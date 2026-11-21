# Sketch handles reference value groups

A feature dimension handle points directly to its actual dimension object at
`ff0`. Reusing that rule for a two-point sketch dimension loses the sketch group
owner, even when the display class and parameter names look correct.

The ordinary `moSkDimHandleValG2_c` stores the actual `sgSketch` at `ff0` and the
index in its `val_g2` array at `ff8`. The retained value is the row at that index.
Its endpoints are separate local point handles. This indexed reference does not
add the direct dimension-pointer reference count used by the feature handle.

Use the concrete handle class, actual owner profile and actual mapped sketch to
validate this branch. Do not replace it with a cached dimension pointer or infer
ownership from a saved selection string. Construction may retain its immutable
planned value order as runtime metadata before the sketch arrays are published;
that metadata is not an additional serialized field.

The [SDK rectangle ledger](../../../../../../re/solidworks/records/SdkRectangleDimensions2026.md)
binds the current constructor and the guarded fresh-process proof.
