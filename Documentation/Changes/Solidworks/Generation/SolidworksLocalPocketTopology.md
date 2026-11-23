# Construct a local Parasolid solid with one rectangular recess

The internal SOLIDWORKS part composer generates the analytic boundary of one
closed rectangular solid with one blind rectangular recess opening through
its upper XY face. The millimetre B-rep supplies the outside, floor, opening
and all connecting edge uses. The composer normalizes face-use direction,
verifies the actual planes and ordered rings, and allocates two owned loops
on the rim. A through-opening, a touching recess, foreign trim ownership,
additional attributes and inexact plane stations are refused.

Two independently authored neutral shapes reproduce their complete parts and
all twelve logical streams deterministically. The model-only process reads
zero external inputs and verifies exact local body, partition and five linked
archive streams through typed replay. Decoded area, volume, centroid and
topology agree with independent rectangular subtraction. The previously
measured rectangle, concave L prism and two cylinders retain their whole-file
hashes. [Reproduction and measurements](../../../../re/solidworks/records/LocalPocketTopology2026.md)

The construction checkpoint preceded strict public readback. The generated
pocket parts await independent native measurement. The existing geometry-only
publication profiles and their per-output evidence gates still apply.
[Strict readback](../Inspection/Parts/Geometry/SolidworksLocalPocketReadback.md)
