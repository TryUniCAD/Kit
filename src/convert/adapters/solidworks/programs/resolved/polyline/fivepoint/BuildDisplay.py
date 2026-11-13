from __future__ import annotations

from .PadBounds import PadBounds


def BuildDisplay(Bounds: PadBounds) -> dict[int, float]:
    OutputData: dict[int, float] = {}
    for OffsetPos in (3533, 4052):
        OutputData[OffsetPos] = Bounds.CentreX - Bounds.ExpandedX
    for OffsetPos in (3541, 4630):
        OutputData[OffsetPos] = Bounds.CentreY + Bounds.ExpandedY
    for OffsetPos in (3680, 4246):
        OutputData[OffsetPos] = Bounds.ExpandedX
    for OffsetPos in (3688, 4254):
        OutputData[OffsetPos] = -Bounds.ExpandedX
    for OffsetPos in (3696, 4832):
        OutputData[OffsetPos] = Bounds.ExpandedY
    for OffsetPos in (3704, 4840):
        OutputData[OffsetPos] = -Bounds.ExpandedY
    for OffsetPos in (3727, 4293):
        OutputData[OffsetPos] = Bounds.CentreX
    for OffsetPos in (3735, 4871):
        OutputData[OffsetPos] = Bounds.CentreY
    for OffsetPos in (4309, 4879):
        OutputData[OffsetPos] = Bounds.CentreZ
    OutputData[4068] = Bounds.CentreZ - Bounds.ExpandedZ
    OutputData[4638] = Bounds.CentreZ + Bounds.ExpandedZ
    for OffsetPos in (4262, 4816):
        OutputData[OffsetPos] = Bounds.ExpandedZ
    for OffsetPos in (4270, 4824):
        OutputData[OffsetPos] = -Bounds.ExpandedZ
    return OutputData
