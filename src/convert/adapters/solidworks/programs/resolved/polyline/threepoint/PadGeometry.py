from __future__ import annotations

import math as MathLib

from .PadBounds import PadBounds


def ComputeBounds(
    PointsMm: tuple[tuple[float, float], ...], DepthMm: float
) -> PadBounds:
    MinimumX = min(PointPair[0] for PointPair in PointsMm)
    MaximumX = max(PointPair[0] for PointPair in PointsMm)
    MinimumY = min(PointPair[1] for PointPair in PointsMm)
    MaximumY = max(PointPair[1] for PointPair in PointsMm)
    CentreX = (MinimumX + MaximumX) / 2000.0
    CentreY = (MinimumY + MaximumY) / 2000.0
    CentreZ = DepthMm / 2000.0
    HalfX = (MaximumX - MinimumX) / 2000.0
    HalfY = (MaximumY - MinimumY) / 2000.0
    HalfZ = CentreZ
    ExpandedX = (MaximumX - MinimumX) * 1.1 / 2000.0
    ExpandedY = (MaximumY - MinimumY) * 1.1 / 2000.0
    ExpandedZ = DepthMm * 1.1 / 2000.0
    Diameter = 2.0 * MathLib.sqrt(HalfX**2 + HalfY**2 + HalfZ**2)
    return PadBounds(
        CentreX,
        CentreY,
        CentreZ,
        ExpandedX,
        ExpandedY,
        ExpandedZ,
        Diameter,
    )
