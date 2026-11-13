from __future__ import annotations


def FindAttach(PointsMm: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    MaximumX = max(PointPair[0] for PointPair in PointsMm)
    return next(PointPair for PointPair in PointsMm if PointPair[0] == MaximumX)
