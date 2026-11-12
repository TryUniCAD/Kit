from math import ceil as Ceiling, cos as Cosine, sin as SineOf

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import (
    KPlaneLoop,
    KPlaneSpan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    ArcPoint,
    SpanFinish,
    SpanStart,
)


def SpanPoints(Value: KPlaneSpan, Density: int = 64) -> list[tuple[float, float]]:
    if isinstance(Value, LineSpan):
        return [Value.StartCm]
    Count = max(2, int(Ceiling(abs(Value.SweepAngle) / 6.283185307179586 * Density)))
    return [
        ArcPoint(Value, Value.StartAngle + Value.SweepAngle * Index / Count)
        for Index in range(Count)
    ]


def LoopPolygon(LoopValue: KPlaneLoop, Density: int = 64) -> list[tuple[float, float]]:
    return [Point for Value in LoopValue for Point in SpanPoints(Value, Density)]


def SpanArea(Value: KPlaneSpan) -> float:
    if isinstance(Value, LineSpan):
        StartX, StartY = Value.StartCm
        FinishX, FinishY = Value.FinishCm
        return (StartX * FinishY - FinishX * StartY) / 2.0
    return ArcArea(Value)


def ArcArea(Value: ArcSpan) -> float:
    CenterX, CenterY = Value.CenterCm
    Radius = Value.RadiusCm
    First = Value.StartAngle
    Second = First + Value.SweepAngle
    return (
        Radius * Radius * Value.SweepAngle
        + CenterX * Radius * (SineOf(Second) - SineOf(First))
        - CenterY * Radius * (Cosine(Second) - Cosine(First))
    ) / 2.0


def LoopArea(LoopValue: KPlaneLoop) -> float:
    return sum(SpanArea(Value) for Value in LoopValue)


def WindNumber(Polygon: list[tuple[float, float]], Point: tuple[float, float]) -> int:
    Winding = 0
    PointX, PointY = Point
    for Index, (StartX, StartY) in enumerate(Polygon):
        FinishX, FinishY = Polygon[(Index + 1) % len(Polygon)]
        Cross = (FinishX - StartX) * (PointY - StartY) - (PointX - StartX) * (
            FinishY - StartY
        )
        if StartY <= PointY < FinishY and Cross > 0:
            Winding += 1
        elif FinishY <= PointY < StartY and Cross < 0:
            Winding -= 1
    return Winding


def IsInRegion(Loops: tuple[KPlaneLoop, ...], Point: tuple[float, float]) -> bool:
    return sum(WindNumber(LoopPolygon(LoopValue), Point) for LoopValue in Loops) > 0


def IsLoopClosed(LoopValue: KPlaneLoop) -> bool:
    return all(
        abs(
            SpanFinish(Value)[0] - SpanStart(LoopValue[(Index + 1) % len(LoopValue)])[0]
        )
        < 1e-7
        and abs(
            SpanFinish(Value)[1] - SpanStart(LoopValue[(Index + 1) % len(LoopValue)])[1]
        )
        < 1e-7
        for Index, Value in enumerate(LoopValue)
    )
