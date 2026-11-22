from math import hypot as HypotValue, ulp as FloatUlp

from convert.adapters.solidworks.Archive.Construction.Ellipse.ReadEllipAxes import (
    ReadEllipAxes,
)
from interchange.geometry.Models.GeometryConics import EllipseGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# each station multiplication addition and inverse subtraction contributes to its component error
def AxisDotError(CenterValue: float, MajorValue: float, MinorValue: float) -> float:
    MajorSize = abs(MajorValue - CenterValue)
    MinorSize = abs(MinorValue - CenterValue)
    MajorError = FloatUlp(MajorValue) + 2 * FloatUlp(MajorSize)
    MinorError = FloatUlp(MinorValue) + 2 * FloatUlp(MinorSize)
    return (
        MajorSize * MinorError
        + MinorSize * MajorError
        + MajorError * MinorError
        + FloatUlp(MajorSize * MinorSize)
    )


# translated station recovery needs a binary64 dot bound while retaining the signed major and minor roles
def EllipAxisGeom(
    CenterValue: tuple[float, float],
    MajorValue: tuple[float, float],
    MinorValue: tuple[float, float],
    DepthValue: float,
) -> EllipseGeometry:
    MajorX, MajorY = MajorValue[0] - CenterValue[0], MajorValue[1] - CenterValue[1]
    MinorX, MinorY = MinorValue[0] - CenterValue[0], MinorValue[1] - CenterValue[1]
    RadiusA, RadiusB = HypotValue(MajorX, MajorY), HypotValue(MinorX, MinorY)
    FirstDot, SecondDot = MajorX * MinorX, MajorY * MinorY
    DotError = (
        AxisDotError(CenterValue[0], MajorValue[0], MinorValue[0])
        + AxisDotError(CenterValue[1], MajorValue[1], MinorValue[1])
        + FloatUlp(abs(FirstDot) + abs(SecondDot))
    )
    if (
        not 0 < RadiusB < RadiusA
        or MajorX * MinorY - MajorY * MinorX <= 0.0
        or abs(FirstDot + SecondDot) > DotError
    ):
        raise ValueError("full ellipse lacks orthogonal positively ordered axes")
    Geometry = EllipseGeometry(
        PlaneVector(CenterValue[0] * 1000.0, CenterValue[1] * 1000.0),
        PlaneVector(MajorX / RadiusA, MajorY / RadiusA),
        RadiusA * 1000.0,
        RadiusB * 1000.0,
    )
    _ = ReadEllipAxes(Geometry, DepthValue)
    return Geometry
