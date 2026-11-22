# A readable saved sweep carrier still needs typed trim proof

The shared SOLIDWORKS geometry reader exposes two planar caps and a
torus for the disclosed saved Standard sweeps. The two stored radii
can differ by one binary64 step from the live metre values projected
into millimetres. Retain the actual physical values alongside the
two driver values.

The geometry reader exposes the four coedges without pcurves. The full
typed kernel parser reaches the torus class 54 after 49 records.
Validate the actual shell and the trim lineage before claiming a
complete portable boundary or result-partition replay.

[Exact archived observations](../../../../../../re/solidworks/records/ScopedSavedSweepReplay2026.md)
