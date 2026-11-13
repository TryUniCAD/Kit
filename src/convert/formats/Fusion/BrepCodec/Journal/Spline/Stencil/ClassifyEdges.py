from dataclasses import replace as ReplaceValue
import math

from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormEdge,
    FormUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.SplineFrame import (
    CurveFrame,
    SurfaceFrame,
)

KTangentSine = math.sin(math.radians(0.65))
KCreaseSine = math.sin(math.radians(1.15))
KFlatSine = 1e-6
KCreaseSamples = 8
KCreaseSide = tuple[NubsSurface, FormUse]


def CrossValue(First: list[float], Second: list[float]) -> list[float]:
    return [
        First[1] * Second[2] - First[2] * Second[1],
        First[2] * Second[0] - First[0] * Second[2],
        First[0] * Second[1] - First[1] * Second[0],
    ]


def UnitValue(Vector: list[float]) -> list[float]:
    Length = math.sqrt(sum(Entry * Entry for Entry in Vector))
    if Length == 0.0:
        raise ValueError("Fusion Form crease check found a degenerate frame")
    return [Entry / Length for Entry in Vector]


def SideNormal(SideValue: KCreaseSide, Param: float) -> list[float]:
    Cache, UseValue = SideValue
    Knots = UseValue.Pcurve.Knots
    if not Knots[0] <= Param <= Knots[-1]:
        raise ValueError("Fusion Form crease check found a pcurve off the edge range")
    Point, _ = CurveFrame(UseValue.Pcurve, Param)
    AlongU, AlongV = SurfaceFrame(Cache, Point[0], Point[1])
    return UnitValue(CrossValue(AlongU, AlongV))


def EdgeParams(EdgeValue: FormEdge) -> list[float]:
    Knots = EdgeValue.Curve.Knots
    Lower, Upper = EdgeValue.Bounds or (Knots[0], Knots[-1])
    Breaks = [Lower, *(Value for Value in Knots if Lower < Value < Upper), Upper]
    return [
        Begin + (Finish - Begin) * (Index + 0.5) / KCreaseSamples
        for Begin, Finish in zip(Breaks, Breaks[1:])
        for Index in range(KCreaseSamples)
    ]


def EdgeSines(EdgeValue: FormEdge, Sides: list[KCreaseSide]) -> list[float]:
    Signed: list[float] = []
    for Param in EdgeParams(EdgeValue):
        _, Tangent = CurveFrame(EdgeValue.Curve, Param)
        Across = CrossValue(SideNormal(Sides[0], Param), SideNormal(Sides[1], Param))
        SineValue = math.sqrt(sum(Entry * Entry for Entry in Across))
        TurnValue = sum(
            First * Second for First, Second in zip(Across, UnitValue(Tangent))
        )
        Signed.append(math.copysign(SineValue, TurnValue))
    return Signed


def EdgeSides(BodyValue: FormBody) -> dict[int, list[KCreaseSide]]:
    Sides: dict[int, list[KCreaseSide]] = {}
    for FaceValue in BodyValue.Faces:
        for UseValue in FaceValue.Uses:
            Entry = (FaceValue.Surface.Cache, UseValue)
            Sides.setdefault(UseValue.EdgeIndex, []).append(Entry)
    return Sides


def IsSteady(Signed: list[float]) -> bool:
    Sizes = [abs(SineValue) for SineValue in Signed]
    return (
        min(Sizes) > KFlatSine
        and max(Sizes) >= KCreaseSine
        and len({SineValue > 0.0 for SineValue in Signed}) == 1
    )


def EdgeClass(EdgeValue: FormEdge, Sides: list[KCreaseSide]) -> str:
    if EdgeValue.Convexity not in ("tangent", "unknown"):
        raise ValueError("Fusion Form crease check needs tangent or unknown edges")
    Signed = EdgeSines(EdgeValue, Sides)
    Largest = max(abs(SineValue) for SineValue in Signed)
    if EdgeValue.Convexity == "tangent" and Largest <= KTangentSine:
        return "tangent"
    if IsSteady(Signed):
        return "unknown"
    raise ValueError("Fusion Form conversion may split or reclassify a crease edge")


def ClassifyEdges(BodyValue: FormBody) -> FormBody:
    Sides = EdgeSides(BodyValue)
    Edges = tuple(
        (
            ReplaceValue(EdgeValue, Convexity=EdgeClass(EdgeValue, Sides[EdgeIndex]))
            if len(Sides.get(EdgeIndex, [])) == 2
            else EdgeValue
        )
        for EdgeIndex, EdgeValue in enumerate(BodyValue.Edges)
    )
    return ReplaceValue(BodyValue, Edges=Edges)
