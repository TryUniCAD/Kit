# Decoded partition geometry needs an archive owner

A SOLIDWORKS 2026 blind boss can have a complete decoded solid in the
selected configuration partition while its public feature has no output body
link and the public body has no topology counts or volume. The active
partition supplies the kernel geometry. The boss's saved output atom and
manager entry, together with the kernel's body identifiers, prove ownership.

Check that the boss output atom is the actual configuration manager member
and that the selected kernel body has the matching typed identifiers. Then
check which measurements and links the public model actually publishes.
The [binding-order gotcha](../../../../Research/Workers/Verification/SolidworksActivePartitionBindingOrder.md)
covers already annotated public geometry.
[Measured reader comparison](../../../../../../re/solidworks/records/VendorBlindBossAdmission2026.md#active-body-evidence)
