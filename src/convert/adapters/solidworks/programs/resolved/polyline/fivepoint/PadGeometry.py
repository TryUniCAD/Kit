from __future__ import annotations

from dataclasses import dataclass as Dataclass
import math as MathLib

from convert.adapters.solidworks.container.Container import SldprtFormatError


@Dataclass(frozen=True, slots=True)
class PadBounds:
    centre_x: float
    centre_y: float
    centre_z: float
    expanded_x: float
    expanded_y: float
    expanded_z: float
    diameter: float


def AttachmentPoint(PointsMm: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    MaximumX = max(PointPair[0] for PointPair in PointsMm)
    Rightmost = [PointPair for PointPair in PointsMm if PointPair[0] == MaximumX]
    if len(Rightmost) != 1:
        raise SldprtFormatError("five-line rightmost attachment vertex must be unique")
    return Rightmost[0]


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
    ExpandedX = HalfX * 1.1
    ExpandedY = HalfY * 1.1
    ExpandedZ = DepthMm * 0.55 / 1000.0
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
