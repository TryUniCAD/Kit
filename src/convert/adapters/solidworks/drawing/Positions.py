from __future__ import annotations

from dataclasses import dataclass
import math as MathValue
import struct as Struct

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.drawing.Models import ViewBounds
from interchange import Vector3

# repeated position records are separated by this native display list stride
KRecordOffset = 384

# displayed coordinates stay far below this guard against arbitrary binary noise
KMaxCoordinate = 1000000.0

# the outline quadruple starts this many bytes after the paired centre record
KOutlineOffset = 37

# the model bounds block starts this many bytes after the paired centre record
KBoundsOffset = 135


# one recovered placement keeps the centre and sheet bounds together
@dataclass(frozen=True, slots=True)
class ViewPlacement:
    CenterX: float
    CenterY: float
    LowerX: float
    LowerY: float
    UpperX: float
    UpperY: float
    Bounds: ViewBounds


# view centres are recovered as paired display list records and deduplicated by pair
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


def PlacementAt(
    DataValue: bytes,
    Offset: int,
    Center: tuple[float, float],
    Outline: tuple[float, float, float, float],
) -> ViewPlacement:
    LowerX, LowerY, UpperX, UpperY = Outline
    return ViewPlacement(
        Center[0],
        Center[1],
        LowerX,
        LowerY,
        UpperX,
        UpperY,
        BoundsAt(DataValue, Offset),
    )


def Positions(DataValue: bytes) -> tuple[ViewPlacement, ...]:
    Candidates: dict[int, tuple[float, float]] = {}
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
        if ZValue != 0.0 or WValue not in (1.0, 2.0):
            continue
        Candidates[Offset] = (XValue, YValue)
    Points: list[ViewPlacement] = []
    Consumed: set[int] = set()
    for Offset in sorted(Candidates):
        if Offset in Consumed:
            continue
        Paired = Offset + KRecordOffset
        if Candidates.get(Paired) != Candidates[Offset]:
            continue
        OutlineOffset = Offset + KOutlineOffset
        if OutlineOffset + 32 > len(DataValue):
            raise SldprtFormatError("drawing view outline is truncated")
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
            raise SldprtFormatError("drawing view outline is invalid")
        Points.append(PlacementAt(DataValue, Offset, Candidates[Offset], Outline))
        Consumed.add(Paired)
    return tuple(Points)
