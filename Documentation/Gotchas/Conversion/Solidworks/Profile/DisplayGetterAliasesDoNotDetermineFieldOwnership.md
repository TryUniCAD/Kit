# Display getter aliases do not determine field ownership

## Expectation

An exported getter name could appear to identify every caller's receiver and returned field.

## Observed behavior

The actual 2026 radial display table binds its attachment-list getter to `0x4b286df0`.
That complete leaf returns the pointer at receiver `+0xe48`.
A public export at the same address names an unrelated model getter.
The display constructor independently identifies its own `+0xe48` as the attachment-point list.
The shared instruction address does not give these objects the same field owner or type.

## Workaround

Identify the call receiver and concrete vtable before assigning a field meaning.
Check that meaning against the matching constructor and consumers.
Use export names as location evidence.
The [presentation record](../../../../../re/solidworks/records/RadialPresentationConstruction2026.md#common-finalization-with-an-empty-attachment-list)
records the actual list getter, constructor, import target and empty-list finalizer.
