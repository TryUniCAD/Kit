from __future__ import annotations

from collections.abc import Sequence
import math as MathValue
import struct as Struct
from typing import Protocol

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
from convert.adapters.solidworks.drawing.WriterRecords import (
    DefinitionView,
    DefinitionViews,
    DisplayView,
    DisplayViews,
)


# both record kinds share the position fields the matcher needs
class PositionedRecord(Protocol):
    @property
    def PositionX(self) -> float: ...

    @property
    def PositionY(self) -> float: ...


# the source position is the only stable key when a view has been renamed
def MatchRecordMut(
    SourceView: DrawingView,
    Records: Sequence[PositionedRecord],
    UsedIndices: set[int],
) -> int:
    if SourceView.PositionX is None or SourceView.PositionY is None:
        raise SldprtFormatError("source view is missing placement data")
    for Index, Record in enumerate(Records):
        if Index in UsedIndices:
            continue
        if MathValue.isclose(
            Record.PositionX, SourceView.PositionX, rel_tol=0.0, abs_tol=1e-09
        ) and MathValue.isclose(
            Record.PositionY, SourceView.PositionY, rel_tol=0.0, abs_tol=1e-09
        ):
            UsedIndices.add(Index)
            return Index
    raise SldprtFormatError("source view has no matching record")


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
    SourceData = ReadDrawing(Source, IncludePositions=True)
    SourceViews = tuple(
        ViewValue for SheetValue in SourceData.Sheets for ViewValue in SheetValue.Views
    )
    DataViews = tuple(
        ViewValue for SheetValue in DataValue.Sheets for ViewValue in SheetValue.Views
    )
    if len(SourceViews) != len(DataViews):
        raise SldprtFormatError("drawing view count does not match the source")
    DefinitionRecords = DefinitionViews(Definition)
    DisplayRecords = DisplayViews(Display)
    if len(DefinitionRecords) != len(DataViews) or len(DisplayRecords) != len(
        DataViews
    ):
        raise SldprtFormatError("drawing view records do not match the view count")
    NewDefinition = bytearray(Definition)
    NewDisplay = bytearray(Display)
    UsedDefinition: set[int] = set()
    UsedDisplay: set[int] = set()
    for SourceView, DataView in zip(SourceViews, DataViews, strict=True):
        DefinitionIndex = MatchRecordMut(SourceView, DefinitionRecords, UsedDefinition)
        DisplayIndex = MatchRecordMut(SourceView, DisplayRecords, UsedDisplay)
        RewriteViewMut(
            DataView,
            DefinitionRecords[DefinitionIndex],
            DisplayRecords[DisplayIndex],
            NewDefinition,
            NewDisplay,
        )
    Streams[KDefinitionStream] = bytes(NewDefinition)
    Streams[KDisplayStream] = bytes(NewDisplay)
    return BuildSldprt(Streams, Template=Source)
