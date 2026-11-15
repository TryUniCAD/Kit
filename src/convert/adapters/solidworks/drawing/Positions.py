from __future__ import annotations

from dataclasses import dataclass
import math as MathValue
import struct as Struct

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.drawing.Models import ViewBounds
from interchange import Vector3

# the twin record is found by this stride so the scale can be read
KRecordOffset = 384

# binary noise rarely lands below this guard so it is rejected
KMaxCoordinate = 1000000.0

# an implausible scale must be rejected before it distorts sheet edges
KMaxScale = 1000.0

# a near zero scale must be rejected before it collapses sheet edges
KMinScale = 0.01

# the outline offset is needed because the outline is not length prefixed
KOutlineOffset = 37

# the bounds offset is needed because the bounds block is not length prefixed
KBoundsOffset = 135


# callers need the centre scale and bounds together to project edges
@dataclass(frozen=True, slots=True)
class ViewPlacement:
    CenterX: float
    CenterY: float
    LowerX: float
    LowerY: float
    UpperX: float
    UpperY: float
    Scale: float
    Bounds: ViewBounds


# a missing or invalid bounds block must fail closed rather than guess
def BoundsAt(DataValue: bytes, Offset: int) -> ViewBounds:
    BoundsOffset = Offset + KBoundsOffset
    if BoundsOffset + 72 > len(DataValue):
        raise SldprtFormatError("drawing model bounds are truncated")
    Values = Struct.unpack_from("<9d", DataValue, BoundsOffset)
    if not all((MathValue.isfinite(ItemValue) for ItemValue in Values)):
        raise SldprtFormatError("drawing model bounds are invalid")
    CenterX, CenterY, CenterZ, PeakX, PeakY, PeakZ, FloorX, FloorY, FloorZ = Values
    if (
        FloorX > CenterX
        or CenterX > PeakX
        or FloorY > CenterY
        or CenterY > PeakY
        or FloorZ > CenterZ
        or CenterZ > PeakZ
    ):
        raise SldprtFormatError("drawing model bounds are invalid")
    return ViewBounds(
        Vector3(CenterX, CenterY, CenterZ),
        Vector3(FloorX, FloorY, FloorZ),
        Vector3(PeakX, PeakY, PeakZ),
    )


# one value keeps the placement fields from drifting apart
def PlacementAt(
    DataValue: bytes,
    Offset: int,
    Center: tuple[float, float],
    Outline: tuple[float, float, float, float],
    Scale: float,
) -> ViewPlacement:
    LowerX, LowerY, UpperX, UpperY = Outline
    return ViewPlacement(
        Center[0],
        Center[1],
        LowerX,
        LowerY,
        UpperX,
        UpperY,
        Scale,
        BoundsAt(DataValue, Offset),
    )


# noise rejection needs every field checked before a record is kept
def Candidates(DataValue: bytes) -> dict[int, tuple[float, float, float]]:
    Result: dict[int, tuple[float, float, float]] = {}
    for Offset in range(0, len(DataValue) - 32):
        XValue, YValue = Struct.unpack_from("<dd", DataValue, Offset)
        ZValue = Struct.unpack_from("<d", DataValue, Offset + 16)[0]
        WValue = Struct.unpack_from("<d", DataValue, Offset + 24)[0]
        if not (
            MathValue.isfinite(XValue)
            and MathValue.isfinite(YValue)
            and abs(XValue) < KMaxCoordinate
            and abs(YValue) < KMaxCoordinate
        ):
            continue
        if ZValue != 0.0 or not (KMinScale <= WValue < KMaxScale):
            continue
        Result[Offset] = (XValue, YValue, WValue)
    return Result


# the twin centre is compared with tolerance because the doubles differ
def IsSameCentre(
    FirstValue: tuple[float, float, float],
    SecondValue: tuple[float, float, float],
) -> bool:
    return MathValue.isclose(
        FirstValue[0], SecondValue[0], rel_tol=0.0, abs_tol=1e-09
    ) and MathValue.isclose(FirstValue[1], SecondValue[1], rel_tol=0.0, abs_tol=1e-09)


# the twin is needed because the primary only carries the marker
def Positions(DataValue: bytes) -> tuple[ViewPlacement, ...]:
    Records = Candidates(DataValue)
    Points: list[ViewPlacement] = []
    Consumed: set[int] = set()
    for Offset in sorted(Records):
        if Offset in Consumed:
            continue
        Paired = Offset + KRecordOffset
        TwinValue = Records.get(Paired)
        if TwinValue is None or not IsSameCentre(TwinValue, Records[Offset]):
            continue
        if Records[Offset][2] != 1.0:
            continue
        OutlineOffset = Offset + KOutlineOffset
        if OutlineOffset + 32 > len(DataValue):
            continue
        Outline = Struct.unpack_from("<dddd", DataValue, OutlineOffset)
        LowerX, LowerY, UpperX, UpperY = Outline
        if (
            not (
                MathValue.isfinite(LowerX)
                and MathValue.isfinite(LowerY)
                and MathValue.isfinite(UpperX)
                and MathValue.isfinite(UpperY)
            )
            or LowerX >= UpperX
            or LowerY >= UpperY
        ):
            continue
        try:
            Placement = PlacementAt(
                DataValue,
                Offset,
                (Records[Offset][0], Records[Offset][1]),
                Outline,
                TwinValue[2],
            )
        except SldprtFormatError:
            continue
        Points.append(Placement)
        Consumed.add(Paired)
    return tuple(Points)
