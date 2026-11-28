# Kernel build and behavior version differ

## Expectation

A feature's Parasolid version is the kernel's full build number or its marketing
version converted to an integer.

## Actual behavior

The 2026 feature constructor reads the GCP environment's current session behavior
word. Normal engine startup selects behavior kind `0x64f1`, then asks the kernel
for that behavior. In the matching kernel, the latest-index helper returns
`0x185`; the native version-table entry at that index is `370108`.
The separate full-kernel-build getter returns `3701250`.

The first value therefore supplies feature construction provenance on this
startup path. A caller that deliberately changes compatibility behavior can
produce a different valid result.

## Workaround

Trace the feature caller through the session setter and behavior query, including
the target kernel's index rule and table. Keep behavior provenance explicit in
the builder contract. Do not substitute a saved feature value, a PE version
resource, the full kernel build, or the environment's pre-engine zero seed.

The [construction record](../../../../re/solidworks/records/ModelConstruction2026.md)
contains module hashes and exact addresses. These static derivations do not
establish target-application acceptance of a generated document.
