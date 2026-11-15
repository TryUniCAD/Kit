from __future__ import annotations

from dataclasses import replace as ReplaceData

from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.container.Format import (
    ASSEMBLY_SUFFIX as KAsmSuffix,
    DISPLAY_LISTS_STREAM as KDisplayStream,
    PART_SUFFIX as KPartSuffix,
)
from convert.adapters.solidworks.drawing.Models import DrawingSheet, DrawingView
from convert.adapters.solidworks.drawing.Positions import Positions, ViewPlacement


# the vendor view list binds recovered centres to sheets without relying on xml order
def ViewOrder(TextData: str) -> tuple[tuple[str, str], ...]:
    Tokens = TextData.split("@")
    Result: list[tuple[str, str]] = []
    for Index, Token in enumerate(Tokens):
        if not Token.casefold().endswith((KPartSuffix, KAsmSuffix)):
            continue
        if Index + 2 >= len(Tokens):
            raise SldprtFormatError("drawing view list is truncated")
        SheetName, ViewName = Tokens[Index + 2], Tokens[Index + 1]
        if not SheetName or not ViewName:
            raise SldprtFormatError("drawing view list has an empty name")
        Result.append((SheetName, ViewName))
    return tuple(Result)


# recovered centres are attached only when the metadata order matches every view
def AttachPositions(
    Sheets: tuple[DrawingSheet, ...],
    Order: tuple[tuple[str, str], ...],
    Points: tuple[ViewPlacement, ...],
) -> tuple[DrawingSheet, ...]:
    if not Order or len(Order) != len(Points):
        raise SldprtFormatError("drawing view positions do not match the view list")
    Index: dict[tuple[str, str], int] = {}
    for PositionIndex, (SheetName, ViewName) in enumerate(Order):
        ViewKey = (SheetName.casefold(), ViewName.casefold())
        if ViewKey in Index:
            raise SldprtFormatError("drawing view list repeats a view")
        Index[ViewKey] = PositionIndex
    SeenKeys: set[tuple[str, str]] = set()
    NewSheets: list[DrawingSheet] = []
    for SheetValue in Sheets:
        NewViews: list[DrawingView] = []
        for ViewValue in SheetValue.Views:
            ViewKey = (SheetValue.Name.casefold(), ViewValue.Name.casefold())
            Position = Index.get(ViewKey)
            if Position is None:
                raise SldprtFormatError("drawing view is missing from the view list")
            Placement = Points[Position]
            NewViews.append(
                ReplaceData(
                    ViewValue,
                    PositionX=Placement.CenterX,
                    PositionY=Placement.CenterY,
                    OutlineMinX=Placement.LowerX,
                    OutlineMinY=Placement.LowerY,
                    OutlineMaxX=Placement.UpperX,
                    OutlineMaxY=Placement.UpperY,
                    ModelBounds=Placement.Bounds,
                )
            )
            SeenKeys.add(ViewKey)
        NewSheets.append(ReplaceData(SheetValue, Views=tuple(NewViews)))
    if SeenKeys != set(Index):
        raise SldprtFormatError("drawing view list names an unknown view")
    return tuple(NewSheets)


# position recovery needs both the display list and the vendor view list
def PositionSheets(
    Sheets: tuple[DrawingSheet, ...], TextData: str, Archive: SldprtArchive
) -> tuple[DrawingSheet, ...]:
    Display = Archive.get(KDisplayStream)
    if Display is None:
        raise SldprtFormatError(f"drawing is missing {KDisplayStream}")
    return AttachPositions(Sheets, ViewOrder(TextData), Positions(Display))
