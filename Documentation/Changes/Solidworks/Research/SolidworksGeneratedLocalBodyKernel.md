# Generate a SOLIDWORKS bare local body research candidate

The [research builder](../../../../re/solidworks/records/GeneratedLocalBodyKernel2026.md)
projects one validated planar prism from a typed neutral B-rep to a bare
current-format Parasolid BODY. It computes topology, node indices and frame
lengths. Its shared topology path accepts a bare BODY owner while retaining
the existing marked partition path.

The [measurement](../../../../re/solidworks/measurements/2026/GeneratedLocalBodyKernel01.json)
records two offline builds with zero runtime source reads, different
stream sizes, exact typed readback and agreement with analytic mass properties.
The optional command output belongs outside the checkout. Native import and
part acceptance remain pending.
