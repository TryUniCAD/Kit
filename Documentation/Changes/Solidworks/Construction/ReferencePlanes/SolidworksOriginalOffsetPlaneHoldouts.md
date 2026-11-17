# Qualify both original offset-plane holdouts

The research generator writes an ordinary SOLIDWORKS 2026 offset plane with a
live driving distance, a centered radius-driven circle sketch on that plane,
and a blind boss. It constructs the plane, dimension and sketch owners from the
authored model. The Windows guest translates original locked recipes and builds
each file twice under a runtime input-read guard before attaching the native
control. The generated files opened with one solid and zero diagnostic flags.

Both original pre-writer cases matched all 26 ordered native feature rows,
support and frame, and both driving dimension owners. Each distance edit moved
the solid. The edited model rebuilt, saved and reopened with its original
feature tree intact. All 162 recorded numeric comparisons passed, volume, area
and centre of mass met the six-significant-figure criterion, and all four
native controls passed across eight distinct SOLIDWORKS 2026 SP05.2 processes.
An independent guest audit verified all native phase, source and generated
hashes. Only the verdict and hashes leave the guest. See the [native receipt](../../../../../re/solidworks/measurements/2026/ReferencePlaneOriginalHeldouts01.json).

The qualified research profile covers principal-plane offsets, this circle
and blind-boss shape, and one distance edit per case. It does not enable the
public writer. See the [evaluation method](../../../../../re/solidworks/records/ReferencePlaneBlindQualification2026.md).
