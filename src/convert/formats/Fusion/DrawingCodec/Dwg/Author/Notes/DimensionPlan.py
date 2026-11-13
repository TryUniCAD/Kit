from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DimensionDraft import (
    DimensionDraft,
)

KPointPair = tuple[float, float]
KArrowSize = 3.5
KExtOffset = 2.1
KExtExtend = 2.1
KTextGap = 1.4
KTextHeight = 3.5
KExtentRatio = 1.0211459754433834
KDigitRatio = 0.7346521146004013
KMarkRatio = 0.3673260573002006
KDecimals = 2


@MakeDataClass(frozen=True, slots=True)
class DimensionPlan:
    FirstPoint: KPointPair
    SecondPoint: KPointPair
    LinePoint: KPointPair
    TextPoint: KPointPair
    TextValue: str
    TextWidth: float
    Measurement: float
    LinearFactor: float
    Lines: tuple[tuple[KPointPair, KPointPair], ...]
    Arrows: tuple[tuple[KPointPair, KPointPair, KPointPair], ...]


def MeasureText(Measurement: float) -> str:
    TextValue = f"{Measurement:.{KDecimals}f}".rstrip("0").rstrip(".")
    return "0" if TextValue in ("", "-0") else TextValue


def TextWidth(TextValue: str) -> float:
    Widths = (KDigitRatio if Glyph.isdigit() else KMarkRatio for Glyph in TextValue)
    return sum(Widths) * KTextHeight


def ArrowAt(
    ApexAcross: float, Toward: float, LineY: float
) -> tuple[KPointPair, KPointPair, KPointPair]:
    BaseX = ApexAcross + Toward * KArrowSize
    Halved = KArrowSize / 6
    return ((BaseX, LineY + Halved), (BaseX, LineY - Halved), (ApexAcross, LineY))


def ExtensionLine(Point: KPointPair, LineY: float) -> tuple[KPointPair, KPointPair]:
    Signum = 1.0 if LineY > Point[1] else -1.0
    return (
        (Point[0], Point[1] + Signum * KExtOffset),
        (Point[0], LineY + Signum * KExtExtend),
    )


def PlanDimension(Draft: DimensionDraft) -> DimensionPlan:
    First, Second, LineY = Draft.FirstPoint, Draft.SecondPoint, Draft.LineHeight
    if Draft.ViewScale <= 0 or abs(First[0] - Second[0]) <= 2 * KArrowSize:
        raise ValueError("Authored DWG dimension is too short or has no view scale")
    if abs(LineY - First[1]) <= KExtOffset or abs(LineY - Second[1]) <= KExtOffset:
        raise ValueError("Authored DWG dimension line overlaps its points")
    Toward = -1.0 if First[0] > Second[0] else 1.0
    Measurement = abs(First[0] - Second[0]) / Draft.ViewScale
    TextValue = MeasureText(Measurement)
    Middle = (First[0] + Second[0]) / 2
    TextY = LineY + KTextGap + KTextHeight * KExtentRatio / 2
    return DimensionPlan(
        First,
        Second,
        (Second[0], LineY),
        (Middle, TextY),
        TextValue,
        TextWidth(TextValue),
        Measurement,
        -1 / Draft.ViewScale,
        (
            ExtensionLine(First, LineY),
            ExtensionLine(Second, LineY),
            (
                (First[0] + Toward * KArrowSize, LineY),
                (Second[0] - Toward * KArrowSize, LineY),
            ),
        ),
        (ArrowAt(First[0], Toward, LineY), ArrowAt(Second[0], -Toward, LineY)),
    )
