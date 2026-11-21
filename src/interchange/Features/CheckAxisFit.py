from math import hypot as Hypot

from interchange.Features.Axes.AxisVector import CrossAxis, KAxisTriple
from interchange.Features.PlaneAxisLine import GetAxisLine
from interchange.Features.PlaneExtAxis import KAxisTolerance
from interchange.Features.PlaneExtFrame import KStationTolerance
from interchange.geometry.Models.VectorSpace import SpaceVector


# finite axis geometry must stay consistent with both independently owned support surfaces
def CheckAxisFit(
    StartValue: SpaceVector,
    EndValue: SpaceVector,
    LineOrigin: KAxisTriple,
    LineDirection: KAxisTriple,
    *,
    CompareDirection: bool = True,
) -> None:
    StartPoint, EndPoint, Direction = GetAxisLine(StartValue, EndValue)
    if (
        CompareDirection
        and Hypot(*CrossAxis(Direction, LineDirection)) > KAxisTolerance
    ):
        raise ValueError(
            "plane axis direction differs from the support plane intersection"
        )
    for PointValue in (StartPoint, EndPoint):
        DeltaPoint = (
            PointValue[0] - LineOrigin[0],
            PointValue[1] - LineOrigin[1],
            PointValue[2] - LineOrigin[2],
        )
        if not Hypot(*CrossAxis(DeltaPoint, LineDirection)) <= KStationTolerance:
            raise ValueError(
                "plane axis endpoints are outside the support plane intersection"
            )
