# Bind neutral concentric selections to a generated child

The internal SOLIDWORKS assembly planner now binds one ordinary concentric
mate to two direct rigid occurrences of the same feature-only cylindrical
part. It traces each explicit lateral selection from the authored circle and
boss to the actual generated face, body atom, sketch and configuration. The
planner retains alignment, rotation lock, selection order and the fixed
occurrence.

Call `PlanCylMate` with the complete assembly, its actual embedded child,
the generated part candidate and the minted lateral face tag. Use the
returned placements, selected occurrence indexes and mate input with the
existing internal parent constructor. A supplied B-rep or a foreign face
refuses before a plan is returned.

Three fresh host processes verified the disclosed feature-only request, an
independent anti-aligned locked request and a radial-driver contrast. Seven
internal parent constructions and their actual wrapper and fixed-owner
fields passed. This is an internal planning boundary. Public writer
qualification remains open.
[Implementation and proof](../../../../../../re/solidworks/records/SdkConcentricMatePlanning2026.md)
