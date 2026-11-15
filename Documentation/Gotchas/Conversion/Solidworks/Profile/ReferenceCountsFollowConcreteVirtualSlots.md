# Reference counts follow concrete virtual slots

## Expectation

The shared dimension base class increments its reference count when a handle attaches.
Counting handles could appear sufficient for every derived dimension.

## Observed behavior

The 2026 sketch circle dimension overrides both reference methods with a zero-return routine.
Its actual handle construction, copying and detachment use those virtual slots.
The bounded radial sequence therefore preserves the dimension's count at zero.
Its separately owned parameter still has a runtime connection.

The modern dimension loader also reads the stored dimension count into a temporary and resets its runtime count.
Parameter loading independently reconstructs its connection.
Archive references, geometry constraint references and persistent IDs use other rules.

## Workaround

Resolve the concrete vtable at every lifetime call.
Track each counter's owning object and its serializer separately.
Keep identical field offsets in different classes distinct.
Confirm later mutations before treating a bounded count as a final saved value.

The [2026 lifecycle record](../../../../../re/solidworks/records/RadialParameterLifecycle2026.md)
contains exact call sites, field owners, module hashes and verification limits.
