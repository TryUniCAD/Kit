# A principal datum ID cannot represent sketch rotation

## Expectation

A successful neutral read should preserve the saved orientation of a sketch on a principal datum.

## Actual behavior

The legacy neutral sketch identifies the support plane by datum ID.
The datum supplies a fixed frame. It cannot represent a separate in-plane rotation saved in the sketch reference.
An orthonormal basis with the correct normal can still rotate the two tangent axes.

## Required handling

The reader checks all three saved axes against the canonical native basis.
Signed zero compares equal to zero in this check.
An owned principal reference with rotated tangents raises an unsupported rotation error in both public read modes.
The [principal-plane placement change](../../../../Changes/Solidworks/Inspection/Parts/SolidworksPlanePlacement.md) documents the boundary and regression check.
