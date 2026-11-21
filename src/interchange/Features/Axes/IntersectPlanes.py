from fractions import Fraction
from math import hypot as Hypot

from interchange.Features.Axes.AxisVector import AxisRational, CrossAxis, KAxisTriple
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
    FirstExact, SecondExact = AxisRational(FirstNormal), AxisRational(SecondNormal)
    CrossValue = CrossAxis(FirstExact, SecondExact)
    CrossLength = Hypot(*CrossValue)
    if CrossLength <= KAxisTolerance:
        raise ValueError("plane axis support planes must define a unique intersection")
    Direction = (
        CrossValue[0] / CrossLength,
        CrossValue[1] / CrossLength,
        CrossValue[2] / CrossLength,
    )
    Separation = sum(
        (
            Normal * (Fraction(Second) - Fraction(First))
            for Normal, First, Second in zip(SecondExact, FirstOrigin, SecondOrigin)
        ),
        Fraction(),
    )
    ScaleValue = Separation / sum(
        (Normal * Normal for Normal in CrossValue), Fraction()
    )
    try:
        Anchor = tuple(
            float(Fraction(Origin) + Tangent * ScaleValue)
            for Origin, Tangent in zip(FirstOrigin, CrossAxis(CrossValue, FirstExact))
        )
    except OverflowError as ErrorInfo:
        raise ValueError(
            "plane axis intersection requires a finite model origin"
        ) from ErrorInfo
    return (Anchor[0], Anchor[1], Anchor[2]), Direction
