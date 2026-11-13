from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot

KOrderSlack = 1e-10
KOrderDegree = 3


def SpreadKnots(Values: tuple[float, ...], Counts: tuple[int, ...]) -> list[float]:
    Spread = [Values[0]]
    for KnotValue, Count in zip(Values, Counts):
        Spread.extend([KnotValue] * Count)
    Spread.append(Values[-1])
    return Spread


def DeriveLevel(
    Knots: list[float], Poles: list[list[float]], Level: int
) -> list[list[float]]:
    Scale = KOrderDegree - Level + 1
    Derived: list[list[float]] = []
    for Index in range(len(Poles) - 1):
        Width = Knots[Index + KOrderDegree + 1] - Knots[Index + Level]
        Derived.append(
            [
                Scale * (After - Before) / Width if Width > 0.0 else 0.0
                for Before, After in zip(Poles[Index], Poles[Index + 1])
            ]
        )
    return Derived


def SpanValue(
    Knots: list[float],
    Poles: list[list[float]],
    Level: int,
    SpanIndex: int,
    Param: float,
) -> list[float]:
    Degree = KOrderDegree - Level
    Shifted = Knots[Level : len(Knots) - Level]
    Local = SpanIndex - Level
    Points = [list(Poles[Local - Degree + Offset]) for Offset in range(Degree + 1)]
    for Round in range(1, Degree + 1):
        for Offset in range(Degree, Round - 1, -1):
            Start = Shifted[Local - Degree + Offset]
            Width = Shifted[Local + 1 + Offset - Round] - Start
            Alpha = (Param - Start) / Width
            Points[Offset] = [
                (1.0 - Alpha) * Before + Alpha * After
                for Before, After in zip(Points[Offset - 1], Points[Offset])
            ]
    return Points[Degree]


def KnotOrders(
    Knots: list[float], Poles: tuple[tuple[float, ...], ...]
) -> dict[float, int]:
    Levels = [[list(PoleValue) for PoleValue in Poles]]
    for Level in (1, 2, 3):
        Levels.append(DeriveLevel(Knots, Levels[-1], Level))
    Orders: dict[float, int] = {}
    Inner = Knots[KOrderDegree + 1 : len(Knots) - KOrderDegree - 1]
    for KnotValue in sorted(set(Inner)):
        LeftSpan = max(Index for Index, Value in enumerate(Knots) if Value < KnotValue)
        RightSpan = (
            min(Index for Index, Value in enumerate(Knots) if Value > KnotValue) - 1
        )
        for Level in (1, 2, 3):
            Before = SpanValue(Knots, Levels[Level], Level, LeftSpan, KnotValue)
            After = SpanValue(Knots, Levels[Level], Level, RightSpan, KnotValue)
            if (
                max(
                    abs(BeforeValue - AfterValue)
                    for BeforeValue, AfterValue in zip(Before, After)
                )
                > KOrderSlack
            ):
                Orders[KnotValue] = Level
                break
    return Orders


def SplitOrders(
    Merged: dict[float, int],
) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
    return (
        tuple(sorted(Value for Value, Level in Merged.items() if Level == 1)),
        tuple(sorted(Value for Value, Level in Merged.items() if Level == 2)),
        tuple(sorted(Value for Value, Level in Merged.items() if Level == 3)),
    )


def CurveOrders(
    Curve: BsCurve,
) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
    if Curve.Degree != KOrderDegree or Curve.Rational:
        raise ValueError("Fusion jump orders need nonrational cubic curves")
    Knots = SpreadKnots(Curve.Knots, Curve.Multiplicity)
    return SplitOrders(KnotOrders(Knots, Curve.Poles))


def MergeOrders(
    Knots: tuple[SplineKnot, ...], Lines: list[tuple[KJournalVector, ...]]
) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
    Spread = SpreadKnots(
        tuple(KnotValue.Value for KnotValue in Knots),
        tuple(KnotValue.Count for KnotValue in Knots),
    )
    Merged: dict[float, int] = {}
    for LineValue in Lines:
        for KnotValue, Level in KnotOrders(Spread, LineValue).items():
            Merged[KnotValue] = min(Level, Merged.get(KnotValue, Level))
    return SplitOrders(Merged)


def SurfaceOrders(Surface: NubsSurface) -> tuple[tuple[float, ...], ...]:
    if (Surface.DegreeU, Surface.DegreeV) != (KOrderDegree, KOrderDegree):
        raise ValueError("Fusion jump orders need bicubic surfaces")
    Width = sum(KnotValue.Count for KnotValue in Surface.KnotsU) - 2
    Height = len(Surface.Points) // Width
    Points = Surface.Points
    if Width * Height != len(Points):
        raise ValueError("Fusion jump orders found a ragged pole grid")
    RowLines = [Points[Index * Width : (Index + 1) * Width] for Index in range(Height)]
    Columns = [Points[Index::Width] for Index in range(Width)]
    return (
        *MergeOrders(Surface.KnotsU, RowLines),
        *MergeOrders(Surface.KnotsV, Columns),
    )
