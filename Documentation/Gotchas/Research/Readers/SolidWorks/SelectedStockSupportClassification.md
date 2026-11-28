# Typed selected-stock support overrides stream order

The compatibility sketch scan inferred the moving rectangle's support from
stream order. The complete cold two-stock reader finds its actual Right datum
through the linked `moCompRefPlane_c` owner, checks the self component and
frame, and binds that datum. Leaving the legacy `stream-order` annotation on
the resolved sketch made the registry refuse an unchanged strict readback.

Publish the qualified plane-reference annotation only after validating
the actual reference, its frame and the typed owner aliases. Finish a
measured same-format write by regenerating the part and checking the whole
document. [Measured readback evidence](../../../../../re/solidworks/records/SdkMeasuredSelectedStock2026.md#strict-readback-republication)
