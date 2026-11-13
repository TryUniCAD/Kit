from __future__ import annotations

from convert.adapters.solidworks.container.Container import SldprtFormatError


def FindAttach(PointsMm: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    MaximumX = max(PointPair[0] for PointPair in PointsMm)
    Rightmost = [PointPair for PointPair in PointsMm if PointPair[0] == MaximumX]
    if len(Rightmost) != 1:
        raise SldprtFormatError("five-line rightmost attachment vertex must be unique")
    return Rightmost[0]
