from __future__ import annotations

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
from convert.adapters.solidworks.drawing.Drawing import ReadDrawing
from convert.adapters.solidworks.drawing.Models import DrawingData, DrawingView
from convert.adapters.solidworks.drawing.Positions import (
    KMaxCoordinate,
    KMaxScale,
    KMinScale,
    KOutlineOffset,
)

# the sheet outline keeps this fixed padding around the projected view
KOutlinePadding = 0.004318
from convert.adapters.solidworks.drawing.WriterBindings import BindViews, ViewIndex
from convert.adapters.solidworks.drawing.WriterRecords import (
    DefinitionView,
    DefinitionViews,
    DisplayView,
    DisplayViews,
    PositionIndex,
)


# the source position is the only stable key when a view has been renamed
def MatchRecordMut(SourceView: DrawingView, Index: PositionIndex) -> int:
    if SourceView.PositionX is None or SourceView.PositionY is None:
        raise SldprtFormatError("source view is missing placement data")
    try:
        CreationIndex = ViewIndex(SourceView.Name) - 1
    except SldprtFormatError:
        CreationIndex = -1
    return Index.Take(SourceView.PositionX, SourceView.PositionY, CreationIndex)


# supplied outline bounds must reach the output instead of the source outline
def OutlineValues(
    ViewValue: DrawingView, DisplayRecord: DisplayView, Ratio: float
) -> tuple[float, float, float, float]:
    if (
        ViewValue.OutlineMinX is not None
        and ViewValue.OutlineMinY is not None
        and ViewValue.OutlineMaxX is not None
        and ViewValue.OutlineMaxY is not None
    ):
        return (
            ViewValue.OutlineMinX,
            ViewValue.OutlineMinY,
            ViewValue.OutlineMaxX,
            ViewValue.OutlineMaxY,
        )
    PositionX = ViewValue.PositionX
    PositionY = ViewValue.PositionY
    if PositionX is None or PositionY is None:
        raise SldprtFormatError("drawing view is missing placement data")
    LowerX, LowerY, UpperX, UpperY = DisplayRecord.Outline
    return (
        PositionX
        + (LowerX - DisplayRecord.PositionX + KOutlinePadding) * Ratio
        - KOutlinePadding,
        PositionY
        + (LowerY - DisplayRecord.PositionY + KOutlinePadding) * Ratio
        - KOutlinePadding,
        PositionX
        + (UpperX - DisplayRecord.PositionX - KOutlinePadding) * Ratio
        + KOutlinePadding,
        PositionY
        + (UpperY - DisplayRecord.PositionY - KOutlinePadding) * Ratio
        + KOutlinePadding,
    )


# one view rewrite keeps the definition and display records in step
def RewriteViewMut(
    ViewValue: DrawingView,
    DefinitionRecord: DefinitionView,
    DisplayRecord: DisplayView,
    NewDefinition: bytearray,
    NewDisplay: bytearray,
) -> None:
    PositionX = ViewValue.PositionX
    PositionY = ViewValue.PositionY
    ViewScale = ViewValue.ViewScale
    if PositionX is None or PositionY is None or ViewScale is None:
        raise SldprtFormatError("drawing view is missing placement data")
    if not (
        MathValue.isfinite(PositionX)
        and MathValue.isfinite(PositionY)
        and abs(PositionX) < KMaxCoordinate
        and abs(PositionY) < KMaxCoordinate
        and KMinScale <= ViewScale < KMaxScale
    ):
        raise SldprtFormatError("drawing view placement is invalid")
    Ratio = ViewScale / DisplayRecord.Scale
    OutlineOffset = DisplayRecord.Primary + KOutlineOffset
    Struct.pack_into(
        "<dddd",
        NewDisplay,
        OutlineOffset,
        *OutlineValues(ViewValue, DisplayRecord, Ratio),
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
    SourceData = ReadDrawing(Source, IncludePositions=True)
    SourceViews = tuple(
        ViewValue for SheetValue in SourceData.Sheets for ViewValue in SheetValue.Views
    )
    DisplayRecords = DisplayViews(Display)
    DefinitionRecords = DefinitionViews(Definition, DisplayRecords)
    if len(DefinitionRecords) != len(SourceViews) or len(DisplayRecords) != len(
        SourceViews
    ):
        raise SldprtFormatError("drawing view records do not match the view count")
    NewDefinition = bytearray(Definition)
    NewDisplay = bytearray(Display)
    DefinitionIndex = PositionIndex(DefinitionRecords)
    DisplayIndex = PositionIndex(DisplayRecords)
    for SourceView, DataView in BindViews(SourceData, DataValue):
        DefinitionSlot = MatchRecordMut(SourceView, DefinitionIndex)
        DisplaySlot = MatchRecordMut(SourceView, DisplayIndex)
        RewriteViewMut(
            DataView,
            DefinitionRecords[DefinitionSlot],
            DisplayRecords[DisplaySlot],
            NewDefinition,
            NewDisplay,
        )
    Streams[KDefinitionStream] = bytes(NewDefinition)
    Streams[KDisplayStream] = bytes(NewDisplay)
    return BuildSldprt(Streams, Template=Source)
