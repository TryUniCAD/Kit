from math import fsum as SumExact
from math import hypot as Hypot

from interchange.Features.FeaturePlaneAxis import PlaneAxis
from interchange.Features.PlaneAxisLine import GetAxisLine
from interchange.Features.PlaneExtAxis import KAxisTolerance
from interchange.Features.PlaneExtFrame import GetExtFrame, KStationTolerance
from interchange.geometry.Models.Transform import Transform


# finite axis geometry must stay consistent with both independently owned support surfaces
def CheckAxisFit(
    Definition: PlaneAxis, FirstFrame: Transform, SecondFrame: Transform
) -> None:
    StartPoint, EndPoint, Direction = GetAxisLine(Definition.StartMm, Definition.EndMm)
    FirstOrigin, FirstNormal = GetExtFrame(FirstFrame)
    SecondOrigin, SecondNormal = GetExtFrame(SecondFrame)
    FirstX, FirstY, FirstZ = FirstNormal
    SecondX, SecondY, SecondZ = SecondNormal
    Intersection = (
        FirstY * SecondZ - FirstZ * SecondY,
        FirstZ * SecondX - FirstX * SecondZ,
        FirstX * SecondY - FirstY * SecondX,
    )
    if Hypot(*Intersection) <= KAxisTolerance:
        raise ValueError("plane axis support planes must define a unique intersection")
    for Origin, Normal in ((FirstOrigin, FirstNormal), (SecondOrigin, SecondNormal)):
        if (
            abs(
                SumExact(
                    Value * AxisValue for Value, AxisValue in zip(Direction, Normal)
                )
            )
            > KAxisTolerance
        ):
            raise ValueError("plane axis direction does not follow both support planes")
        for PointValue in (StartPoint, EndPoint):
            Station = SumExact(
                (StationValue - OriginValue) * AxisValue
                for StationValue, OriginValue, AxisValue in zip(
                    PointValue, Origin, Normal
                )
            )
            if not abs(Station) <= KStationTolerance:
                raise ValueError(
                    "plane axis endpoints are outside their support planes"
                )
