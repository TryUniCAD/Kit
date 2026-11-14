from __future__ import annotations

from .PadBounds import PadBounds


def BuildBounds(Bounds: PadBounds) -> dict[int, float]:
    OutputData: dict[int, float] = {}
    for OffsetPos in (8201, 8423):
        OutputData[OffsetPos] = Bounds.CentreX
    for OffsetPos in (8209, 8431):
        OutputData[OffsetPos] = Bounds.CentreY
    for OffsetPos in (8217, 8439, 4293, 4879):
        OutputData[OffsetPos] = Bounds.CentreZ
    for OffsetPos in (8225, 8447):
        OutputData[OffsetPos] = Bounds.Diameter
    return OutputData
