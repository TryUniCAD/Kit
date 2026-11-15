from __future__ import annotations

from dataclasses import dataclass
import math as MathValue
import re as RegexLib
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
from convert.adapters.solidworks.drawing.Positions import (
    KMaxCoordinate,
    KMaxScale,
    KMinScale,
    KOutlineOffset,
    KRecordOffset,
)

# the record width bounds the scan so the last record is not skipped
KViewRecordLength = 40

# the suffix is needed because keyword order does not follow creation order
KViewIndex = RegexLib.compile(r"(\d+)$")


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


# noise rejection needs every field checked before a record is kept
def DefinitionViews(DataValue: bytes) -> tuple[DefinitionView, ...]:
    Result: list[DefinitionView] = []
    for Offset in range(0, len(DataValue) - KViewRecordLength + 1):
        XValue, YValue = Struct.unpack_from("<dd", DataValue, Offset)
        if not (
            MathValue.isfinite(XValue)
            and MathValue.isfinite(YValue)
            and 0.0 < XValue < KMaxCoordinate
            and 0.0 < YValue < KMaxCoordinate
        ):
            continue
        ZValue = Struct.unpack_from("<d", DataValue, Offset + 16)[0]
        ScaleValue = Struct.unpack_from("<d", DataValue, Offset + 24)[0]
        MarkerValue = Struct.unpack_from("<d", DataValue, Offset + 32)[0]
        if ZValue != 0.0 or not (KMinScale <= ScaleValue < KMaxScale):
            continue
        if MarkerValue != 1.0:
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
            and 0.0 < XValue < KMaxCoordinate
            and 0.0 < YValue < KMaxCoordinate
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
        Result.append(DisplayView(Offset, TwinOffset, XValue, YValue, TwinScale))
        Consumed.add(TwinOffset)
    return tuple(Result)


# the creation index binds records because keyword order is not creation order
def ViewIndex(ViewName: str) -> int:
    Match = KViewIndex.search(ViewName)
    if Match is None:
        raise SldprtFormatError("drawing view name has no creation index")
    return int(Match.group(1))


# one view rewrite keeps the definition and display records in step
def RewriteView(
    ViewValue: object,
    DefinitionRecord: DefinitionView,
    DisplayRecord: DisplayView,
    NewDefinition: bytearray,
    NewDisplay: bytearray,
) -> None:
    PositionX = getattr(ViewValue, "PositionX")
    PositionY = getattr(ViewValue, "PositionY")
    ViewScale = getattr(ViewValue, "ViewScale")
    if PositionX is None or PositionY is None or ViewScale is None:
        raise SldprtFormatError("drawing view is missing placement data")
    if not (
        MathValue.isfinite(PositionX)
        and MathValue.isfinite(PositionY)
        and 0.0 < PositionX < KMaxCoordinate
        and 0.0 < PositionY < KMaxCoordinate
        and KMinScale <= ViewScale < KMaxScale
    ):
        raise SldprtFormatError("drawing view placement is invalid")
    DeltaX = PositionX - DisplayRecord.PositionX
    DeltaY = PositionY - DisplayRecord.PositionY
    OutlineOffset = DisplayRecord.Primary + KOutlineOffset
    LowerX, LowerY, UpperX, UpperY = Struct.unpack_from(
        "<dddd", NewDisplay, OutlineOffset
    )
    Struct.pack_into(
        "<dddd",
        NewDisplay,
        OutlineOffset,
        LowerX + DeltaX,
        LowerY + DeltaY,
        UpperX + DeltaX,
        UpperY + DeltaY,
    )
    Struct.pack_into(
        "<dd", NewDefinition, DefinitionRecord.Offset, PositionX, PositionY
    )
    Struct.pack_into("<d", NewDefinition, DefinitionRecord.Offset + 24, ViewScale)
    Struct.pack_into("<dd", NewDisplay, DisplayRecord.Primary, PositionX, PositionY)
    Struct.pack_into("<dd", NewDisplay, DisplayRecord.Twin, PositionX, PositionY)
    Struct.pack_into("<d", NewDisplay, DisplayRecord.Twin + 24, ViewScale)


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
    Ordered = sorted(Views, key=lambda ViewValue: ViewIndex(ViewValue.Name))
    NewDefinition = bytearray(Definition)
    NewDisplay = bytearray(Display)
    for ViewValue, DefinitionRecord, DisplayRecord in zip(
        Ordered, DefinitionRecords, DisplayRecords, strict=True
    ):
        RewriteView(
            ViewValue, DefinitionRecord, DisplayRecord, NewDefinition, NewDisplay
        )
    Streams[KDefinitionStream] = bytes(NewDefinition)
    Streams[KDisplayStream] = bytes(NewDisplay)
    return BuildSldprt(Streams, Template=Source)
