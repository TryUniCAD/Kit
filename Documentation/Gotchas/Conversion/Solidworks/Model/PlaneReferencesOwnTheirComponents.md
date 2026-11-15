# Plane references own their component copies

## Expectation

Profiles on the same plane can share a plane wrapper, and that wrapper can
retain the model's existing self-component object.

## Observed behavior

The 2026 incoming-component reference constructor calls the component's copy
virtual and stores the returned allocation. The unit-component implementation
allocates a distinct object and copies its model relationship. The reference
destructor directly deletes that component object.

The profile plane setter adopts its wrapper pointer without retaining it.
Replacing the wrapper directly deletes the old allocation. A shared wrapper
therefore has conflicting exclusive owners, independently of whether the
underlying principal plane is shared.

The [construction record](../../../../../re/solidworks/records/ModelConstruction2026.md#plane-wrappers)
identifies the constructor, copy implementation, setter, replacement and
destructor addresses in the exact target binary.

## Workaround

Create a separate plane wrapper for each independent profile-data object.
Create a distinct unit-component copy inside each wrapper, preserving the same
actual model-owner reference. Share the referenced principal plane and model
objects according to their proven native relationships.

The fresh factory supports nonexternal unit components and null default-base
components. It rejects unimplemented component-copy states. This ownership
repair does not establish native generated-part acceptance.
