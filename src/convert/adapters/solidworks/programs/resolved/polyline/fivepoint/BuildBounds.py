from __future__ import annotations

from .PadBounds import PadBounds


def BuildBounds(Bounds: PadBounds) -> dict[int, float]:
    OutputData: dict[int, float] = {}
    for OffsetPos in (8797, 9027):
        OutputData[OffsetPos] = Bounds.CentreX
    for OffsetPos in (8805, 9035):
        OutputData[OffsetPos] = Bounds.CentreY
    for OffsetPos in (8813, 9043, 4309, 4879):
        OutputData[OffsetPos] = Bounds.CentreZ
    for OffsetPos in (8821, 9051):
        OutputData[OffsetPos] = Bounds.Diameter
    return OutputData
