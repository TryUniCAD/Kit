from __future__ import annotations

from dataclasses import dataclass
import math as MathValue
import struct as Struct

from convert.adapters.solidworks.container.Container import (
    BuildSldprt,
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.container.Format import (
    DEFINITION_STREAM as KDefinitionStream,
    DISPLAY_LISTS_STREAM as KDisplayStream,
)
from convert.adapters.solidworks.drawing.Models import DrawingData
from convert.adapters.solidworks.drawing.Positions import KRecordOffset

# a view record holds the position a zero z the scale and a unit marker
KViewRecordLength = 40

# a plausible view position stays below this guard against binary noise
KMaxPosition = 1000.0

# a plausible view scale stays inside this range against binary noise
KMinScale = 0.01

# a plausible view scale stays inside this range against binary noise
KMaxScale = 1000.0


# one definition view record keeps its offset and recovered values together
@dataclass(frozen=True, slots=True)
class DefinitionView:
    Offset: int
    PositionX: float
    PositionY: float
    Scale: float


# one display list record keeps the primary and twin offsets together
@dataclass(frozen=True, slots=True)
class DisplayView:
    Primary: int
    Twin: int
    PositionX: float
    PositionY: float
    Scale: float


# definition view records are found by their position zero scale and unit marker
def DefinitionViews(DataValue: bytes) -> tuple[DefinitionView, ...]:
    Result: list[DefinitionView] = []
    for Offset in range(0, len(DataValue) - KViewRecordLength + 1):
        XValue, YValue = Struct.unpack_from("<dd", DataValue, Offset)
        if not (
            MathValue.isfinite(XValue)
            and MathValue.isfinite(YValue)
            and 0.0 < XValue < KMaxPosition
            and 0.0 < YValue < KMaxPosition
        ):
            continue
        ZValue = Struct.unpack_from("<d", DataValue, Offset + 16)[0]
        ScaleValue = Struct.unpack_from("<d", DataValue, Offset + 24)[0]
        MarkerValue = Struct.unpack_from("<d", DataValue, Offset + 32)[0]
        if ZValue != 0.0 or not (KMinScale <= ScaleValue <= KMaxScale):
            continue
        if MarkerValue != 1.0:
            continue
        Result.append(DefinitionView(Offset, XValue, YValue, ScaleValue))
    return tuple(Result)


# display list records are found by their paired centre and twin scale
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
            and 0.0 < XValue < KMaxPosition
            and 0.0 < YValue < KMaxPosition
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
        if TwinZ != 0.0 or not (KMinScale <= TwinScale <= KMaxScale):
            continue
        Result.append(DisplayView(Offset, TwinOffset, XValue, YValue, TwinScale))
        Consumed.add(TwinOffset)
    return tuple(Result)


# the writer rewrites only the recovered position and scale records
def WriteDrawing(Source: bytes, DataValue: DrawingData) -> bytes:
    Archive = SldprtArchive.from_bytes(Source, "drawing")
    Streams = dict(Archive.streams)
    Definition = Streams.get(KDefinitionStream)
    Display = Streams.get(KDisplayStream)
    if Definition is None:
        raise SldprtFormatError(f"drawing is missing {KDefinitionStream}")
    if Display is None:
        raise SldprtFormatError(f"drawing is missing {KDisplayStream}")
    Views = tuple(
        ViewValue for SheetValue in DataValue.Sheets for ViewValue in SheetValue.Views
    )
    DefinitionRecords = DefinitionViews(Definition)
    DisplayRecords = DisplayViews(Display)
    if len(DefinitionRecords) != len(Views) or len(DisplayRecords) != len(Views):
        raise SldprtFormatError("drawing view records do not match the view count")
    NewDefinition = bytearray(Definition)
    NewDisplay = bytearray(Display)
    for ViewValue, DefinitionRecord, DisplayRecord in zip(
        Views, DefinitionRecords, DisplayRecords, strict=True
    ):
        if (
            ViewValue.PositionX is None
            or ViewValue.PositionY is None
            or ViewValue.ViewScale is None
        ):
            raise SldprtFormatError("drawing view is missing placement data")
        if not (
            MathValue.isfinite(ViewValue.PositionX)
            and MathValue.isfinite(ViewValue.PositionY)
            and KMinScale <= ViewValue.ViewScale <= KMaxScale
        ):
            raise SldprtFormatError("drawing view placement is invalid")
        Struct.pack_into(
            "<dd",
            NewDefinition,
            DefinitionRecord.Offset,
            ViewValue.PositionX,
            ViewValue.PositionY,
        )
        Struct.pack_into(
            "<d", NewDefinition, DefinitionRecord.Offset + 24, ViewValue.ViewScale
        )
        Struct.pack_into(
            "<dd",
            NewDisplay,
            DisplayRecord.Primary,
            ViewValue.PositionX,
            ViewValue.PositionY,
        )
        Struct.pack_into(
            "<dd",
            NewDisplay,
            DisplayRecord.Twin,
            ViewValue.PositionX,
            ViewValue.PositionY,
        )
        Struct.pack_into("<d", NewDisplay, DisplayRecord.Twin + 24, ViewValue.ViewScale)
    Streams[KDefinitionStream] = bytes(NewDefinition)
    Streams[KDisplayStream] = bytes(NewDisplay)
    return BuildSldprt(Streams, Template=Source)
