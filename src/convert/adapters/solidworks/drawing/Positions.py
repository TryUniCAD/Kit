from __future__ import annotations

from dataclasses import dataclass
import math as MathValue
import struct as Struct

from convert.adapters.solidworks.container.Container import SldprtFormatError

# repeated position records are separated by this native display list stride
KRecordOffset = 384

# displayed coordinates stay far below this guard against arbitrary binary noise
KMaxCoordinate = 1000000.0

# the outline quadruple starts this many bytes after the paired centre record
KOutlineOffset = 37


# one recovered placement keeps the centre and sheet bounds together
@dataclass(frozen=True, slots=True)
class ViewPlacement:
    CenterX: float
    CenterY: float
    LowerX: float
    LowerY: float
    UpperX: float
    UpperY: float


# view centres are recovered as paired display list records and deduplicated by pair
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
        LowerX, LowerY, UpperX, UpperY = Struct.unpack_from(
            "<dddd", DataValue, OutlineOffset
        )
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
        Points.append(
            ViewPlacement(
                Candidates[Offset][0],
                Candidates[Offset][1],
                LowerX,
                LowerY,
                UpperX,
                UpperY,
            )
        )
        Consumed.add(Paired)
    return tuple(Points)
