from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math as MathValue
import struct as Struct
from typing import Protocol

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.drawing.Positions import (
    KMaxCoordinate,
    KMaxScale,
    KMinScale,
    KOutlineOffset,
    KRecordOffset,
)

# the record width bounds the scan so the last record is not skipped
KViewRecordLength = 40


# callers need the offset and values together to rewrite in place
@dataclass(frozen=True, slots=True)
class DefinitionView:
    Offset: int
    PositionX: float
    PositionY: float
    Scale: float


# callers need both offsets because the twin carries the scale
@dataclass(frozen=True, slots=True)
class DisplayView:
    Primary: int
    Twin: int
    PositionX: float
    PositionY: float
    Scale: float
    Outline: tuple[float, float, float, float]


# both record kinds share the position fields the matcher needs
class PlacedRecord(Protocol):
    @property
    def PositionX(self) -> float: ...

    @property
    def PositionY(self) -> float: ...


# the index keeps coincident records in creation order and lookup constant
class PositionIndex:
    def __init__(self, Records: Sequence[PlacedRecord]) -> None:
        super().__init__()
        self.Buckets: dict[tuple[float, float], list[tuple[float, float, int]]] = {}
        for Index, Record in enumerate(Records):
            self.Buckets.setdefault((Record.PositionX, Record.PositionY), []).append(
                (Record.PositionX, Record.PositionY, Index)
            )

    def Candidates(
        self, XValue: float, YValue: float
    ) -> list[tuple[float, float, int]]:
        return list(self.Buckets.get((XValue, YValue), ()))

    def Contains(self, XValue: float, YValue: float) -> bool:
        return (XValue, YValue) in self.Buckets

    def Take(self, XValue: float, YValue: float, Preferred: int) -> int:
        Candidates = self.Candidates(XValue, YValue)
        if not Candidates:
            raise SldprtFormatError("source view has no matching record")
        Selected = next(
            (ItemValue for ItemValue in Candidates if ItemValue[2] == Preferred),
            Candidates[0],
        )
        self.Buckets[(XValue, YValue)].remove(Selected)
        return Selected[2]


# a definition record is kept only when a display record shares its position
def DefinitionViews(
    DataValue: bytes, DisplayRecords: Sequence[PlacedRecord]
) -> tuple[DefinitionView, ...]:
    Index = PositionIndex(DisplayRecords)
    Result: list[DefinitionView] = []
    for Offset in range(0, len(DataValue) - KViewRecordLength + 1):
        XValue, YValue = Struct.unpack_from("<dd", DataValue, Offset)
        if not (
            MathValue.isfinite(XValue)
            and MathValue.isfinite(YValue)
            and abs(XValue) < KMaxCoordinate
            and abs(YValue) < KMaxCoordinate
        ):
            continue
        ZValue = Struct.unpack_from("<d", DataValue, Offset + 16)[0]
        ScaleValue = Struct.unpack_from("<d", DataValue, Offset + 24)[0]
        MarkerValue = Struct.unpack_from("<d", DataValue, Offset + 32)[0]
        if ZValue != 0.0 or not (KMinScale <= ScaleValue < KMaxScale):
            continue
        if MarkerValue != 1.0:
            continue
        if not Index.Contains(XValue, YValue):
            continue
        Result.append(DefinitionView(Offset, XValue, YValue, ScaleValue))
    return tuple(Result)


# the twin is needed because the primary only carries the marker
def DisplayViews(DataValue: bytes) -> tuple[DisplayView, ...]:
    Result: list[DisplayView] = []
    Consumed: set[int] = set()
    for Offset in range(0, len(DataValue) - 32):
        if Offset in Consumed:
            continue
        XValue, YValue = Struct.unpack_from("<dd", DataValue, Offset)
        if not (
            MathValue.isfinite(XValue)
            and MathValue.isfinite(YValue)
            and abs(XValue) < KMaxCoordinate
            and abs(YValue) < KMaxCoordinate
        ):
            continue
        ZValue = Struct.unpack_from("<d", DataValue, Offset + 16)[0]
        MarkerValue = Struct.unpack_from("<d", DataValue, Offset + 24)[0]
        if ZValue != 0.0 or MarkerValue != 1.0:
            continue
        TwinOffset = Offset + KRecordOffset
        if TwinOffset + 32 > len(DataValue):
            continue
        TwinX, TwinY = Struct.unpack_from("<dd", DataValue, TwinOffset)
        TwinZ = Struct.unpack_from("<d", DataValue, TwinOffset + 16)[0]
        TwinScale = Struct.unpack_from("<d", DataValue, TwinOffset + 24)[0]
        if not (
            MathValue.isclose(TwinX, XValue, rel_tol=0.0, abs_tol=1e-09)
            and MathValue.isclose(TwinY, YValue, rel_tol=0.0, abs_tol=1e-09)
        ):
            continue
        if TwinZ != 0.0 or not (KMinScale <= TwinScale < KMaxScale):
            continue
        OutlineOffset = Offset + KOutlineOffset
        if OutlineOffset + 32 > len(DataValue):
            continue
        Outline = Struct.unpack_from("<dddd", DataValue, OutlineOffset)
        Result.append(
            DisplayView(Offset, TwinOffset, XValue, YValue, TwinScale, Outline)
        )
        Consumed.add(TwinOffset)
    return tuple(Result)
