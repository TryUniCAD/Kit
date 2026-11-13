from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.OrderJumps import (
    SpreadKnots,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot

KSplineFrame = tuple[list[float], list[float]]


def FindSpan(Knots: list[float], Degree: int, Param: float) -> int:
    SpanIndex = Degree
    while SpanIndex < len(Knots) - Degree - 2 and Param >= Knots[SpanIndex + 1]:
        SpanIndex += 1
    return SpanIndex


def BasisLevel(
    Knots: list[float], SpanIndex: int, Degree: int, Param: float
) -> list[float]:
    Values = [1.0]
    for Level in range(1, Degree + 1):
        Saved = 0.0
        Following: list[float] = []
        for Offset in range(Level):
            LeftGap = Param - Knots[SpanIndex + 1 + Offset - Level]
            RightGap = Knots[SpanIndex + 1 + Offset] - Param
            Ratio = Values[Offset] / (RightGap + LeftGap)
            Following.append(Saved + RightGap * Ratio)
            Saved = LeftGap * Ratio
        Values = Following + [Saved]
    return Values


def BasisSlope(
    Knots: list[float], SpanIndex: int, Degree: int, Param: float
) -> list[float]:
    Lower = [0.0] + BasisLevel(Knots, SpanIndex, Degree - 1, Param) + [0.0]
    Slopes: list[float] = []
    for Offset in range(Degree + 1):
        Start = SpanIndex - Degree + Offset
        Before = Knots[Start + Degree] - Knots[Start]
        After = Knots[Start + Degree + 1] - Knots[Start + 1]
        Rising = Lower[Offset] / Before if Before > 0.0 else 0.0
        Falling = Lower[Offset + 1] / After if After > 0.0 else 0.0
        Slopes.append(Degree * (Rising - Falling))
    return Slopes


def CurveFrame(Curve: BsCurve, Param: float) -> KSplineFrame:
    Knots = SpreadKnots(Curve.Knots, Curve.Multiplicity)
    SpanIndex = FindSpan(Knots, Curve.Degree, Param)
    Values = BasisLevel(Knots, SpanIndex, Curve.Degree, Param)
    Slopes = BasisSlope(Knots, SpanIndex, Curve.Degree, Param)
    Poles = Curve.Poles[SpanIndex - Curve.Degree : SpanIndex + 1]
    Point = [
        sum(Value * PoleValue[AxisIndex] for Value, PoleValue in zip(Values, Poles))
        for AxisIndex in range(Curve.Dimension)
    ]
    Tangent = [
        sum(Slope * PoleValue[AxisIndex] for Slope, PoleValue in zip(Slopes, Poles))
        for AxisIndex in range(Curve.Dimension)
    ]
    return Point, Tangent


def KnotList(Knots: tuple[SplineKnot, ...]) -> list[float]:
    return SpreadKnots(
        tuple(KnotValue.Value for KnotValue in Knots),
        tuple(KnotValue.Count for KnotValue in Knots),
    )


def SurfaceFrame(Surface: NubsSurface, ParamU: float, ParamV: float) -> KSplineFrame:
    KnotsU, KnotsV = KnotList(Surface.KnotsU), KnotList(Surface.KnotsV)
    Width = len(KnotsU) - Surface.DegreeU - 1
    SpanU = FindSpan(KnotsU, Surface.DegreeU, ParamU)
    SpanV = FindSpan(KnotsV, Surface.DegreeV, ParamV)
    ValuesU = BasisLevel(KnotsU, SpanU, Surface.DegreeU, ParamU)
    SlopesU = BasisSlope(KnotsU, SpanU, Surface.DegreeU, ParamU)
    ValuesV = BasisLevel(KnotsV, SpanV, Surface.DegreeV, ParamV)
    SlopesV = BasisSlope(KnotsV, SpanV, Surface.DegreeV, ParamV)
    AlongU, AlongV = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    for RowIndex in range(Surface.DegreeV + 1):
        for ColumnIndex in range(Surface.DegreeU + 1):
            PoleIndex = (SpanV - Surface.DegreeV + RowIndex) * Width
            PoleValue = Surface.Points[
                PoleIndex + SpanU - Surface.DegreeU + ColumnIndex
            ]
            ScaleU = SlopesU[ColumnIndex] * ValuesV[RowIndex]
            ScaleV = ValuesU[ColumnIndex] * SlopesV[RowIndex]
            for AxisIndex in range(3):
                AlongU[AxisIndex] += ScaleU * PoleValue[AxisIndex]
                AlongV[AxisIndex] += ScaleV * PoleValue[AxisIndex]
    return AlongU, AlongV
