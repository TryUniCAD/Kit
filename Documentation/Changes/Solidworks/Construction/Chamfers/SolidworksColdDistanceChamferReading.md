# Read cold distance chamfer candidates internally

The linked SOLIDWORKS 2026 part reader can inspect a generated equal-distance
or two-distance chamfer on its one rectangular blind stock. The internal
`TryColdChmf` route accepts `AllowDistancePair=True` for guarded research.
It validates the actual stock atom, ordered edge references, signed
annotation frames and active driving dimensions. The neutral model
retains D1 for the equal mode and D1 plus the independent D3 for the
two-distance mode. The same edge and setbacks define the clipped solid.

This entry covers cache-free single-edge candidates in one ordinary
`Default` configuration. Native saved distance parts, public distance
publication and held-out qualification remain separate work.
[Reproduction and measured scope](../../../../../re/solidworks/records/ChamferDistancePairRead2026.md)
