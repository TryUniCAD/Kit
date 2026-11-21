# Generic feature owners are separate from mate wire fields

A freshly constructed mate has its actual mate group in the generic
feature's runtime `owner` field. Its anonymous fallback planes also have
an actual parent owner. It is tempting to require those same dictionary
keys after reading the separate native mate stream.

The version-19000 generic feature serializer does not emit that runtime
pointer. Native document loading attaches decoded mates to the group's
runtime list separately. Component-owner references inside the resolved
chains and detached self-components are serialized and must retain the
actual containing assembly alias. These are distinct ownership paths.

Check generic feature ownership during fresh construction. On typed wire
readback, check the serialized component owners, actual occurrence
backlinks, independent inline planes and the inherited resolved group
separately. Do not invent an extra owner word or mistake its absence for
a broken component link.

[Native feature registration and mate loading](../../../../../../re/solidworks/records/CoincidentMatePublication2026.md)
and the [fresh SDK construction proof](../../../../../../re/solidworks/records/SdkPlanarMateConstruction2026.md)
record the scope and exact evidence.
