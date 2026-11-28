# Read cold distance chamfer parts

The linked SOLIDWORKS 2026 part reader can inspect a generated equal-distance
or two-distance chamfer on its one rectangular blind stock through strict
`open_document`. It validates the actual stock atom, ordered edge references, signed
annotation frames and active driving dimensions. The neutral model
retains D1 for the equal mode and D1 plus the independent D3 for the
two-distance mode. The same edge and setbacks define the clipped solid.

This entry covers cache-free single-edge candidates in one ordinary
`Default` configuration. The two held-out distance cases passed the
native lifecycle on SOLIDWORKS 2026 SP05.2. The guarded SDK round trip
uses the two disclosed archives and two existing angle-distance controls.
Native saved distance parts and distance publication have their own scope.
[Reproduction and measured scope](../../../../../re/solidworks/records/ChamferDistancePairRead2026.md)
