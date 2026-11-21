from math import copysign as CopySign
from math import fsum as SumExact
from math import hypot as Hypot
from math import isfinite as IsFinite

from interchange.Features.AxisVector import CrossAxis, KAxisTriple
from interchange.Features.PlaneExtAxis import KAxisTolerance
from interchange.Features.PlaneExtFrame import GetExtFrame
from interchange.geometry.Models.Transform import Transform


# axis diagnostics should identify the validity of the selected geometry
def GetAxisFrame(FrameValue: Transform) -> tuple[KAxisTriple, KAxisTriple]:
    try:
        return GetExtFrame(FrameValue)
    except ValueError as ErrorInfo:
        raise ValueError(
            "plane axis supports require finite orthonormal right handed frames"
        ) from ErrorInfo


# stable intersection coordinates support both stored and independently editable axis extents
def GetPlaneLine(
    FirstFrame: Transform, SecondFrame: Transform
) -> tuple[KAxisTriple, KAxisTriple]:
    FirstOrigin, FirstNormal = GetAxisFrame(FirstFrame)
    SecondOrigin, SecondNormal = GetAxisFrame(SecondFrame)
    NearbySign = CopySign(
        1.0,
        SumExact(First * Second for First, Second in zip(FirstNormal, SecondNormal)),
    )
    DeltaNormal = tuple(
        Second - NearbySign * First for First, Second in zip(FirstNormal, SecondNormal)
    )
    CrossValue = CrossAxis(
        FirstNormal, (DeltaNormal[0], DeltaNormal[1], DeltaNormal[2])
    )
    CrossLength = Hypot(*CrossValue)
    if CrossLength <= KAxisTolerance:
        raise ValueError("plane axis support planes must define a unique intersection")
    Direction = (
        CrossValue[0] / CrossLength,
        CrossValue[1] / CrossLength,
        CrossValue[2] / CrossLength,
    )
    FirstTangent = CrossAxis(Direction, FirstNormal)
    Station = (
        SumExact(
            Normal * (Second - First)
            for Normal, First, Second in zip(SecondNormal, FirstOrigin, SecondOrigin)
        )
        / CrossLength
    )
    Anchor = tuple(
        SumExact((Origin, Tangent * Station))
        for Origin, Tangent in zip(FirstOrigin, FirstTangent)
    )
    if not all(IsFinite(PointValue) for PointValue in Anchor):
        raise ValueError("plane axis intersection requires a finite model origin")
    return (Anchor[0], Anchor[1], Anchor[2]), Direction
