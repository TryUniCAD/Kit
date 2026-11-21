# Packed binary64 coverage is distinct from opaque payload

A mate without a driving display can have an empty `native_byte_fields`
report. Requiring that list to stay empty for every supported mate rejects
the ordinary distance display's native allocation even when it is fully typed.

`moDisplayDistanceDim_c.f5b0.data` is a native binary64 array. The SDK reports
its element type and count, declared and observed lengths, exact length
rule and decoded values. The fresh ordinary constructor computes one
zero double, with eight-byte elements and independently modeled allocation
metadata. This is not an unclassified byte span.

Check the complete typed allocation and its provenance. The writer must
compute each value from the model or native constructor rule. A typed
array whose values came from a vendor save would still be donor data.
Do not erase the coverage report to make a zero-byte claim.

[Native allocation rule](../../../../../../re/solidworks/records/ProfileConstruction2026.md#live-dimension-construction-ledger)
and the [SDK driving-distance proof](../../../../../../re/solidworks/records/SdkDrivingDistanceConstruction2026.md)
record the constructor and process evidence.
