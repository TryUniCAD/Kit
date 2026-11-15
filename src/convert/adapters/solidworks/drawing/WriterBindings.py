from __future__ import annotations

import re as RegexLib

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.drawing.Models import DrawingData, DrawingView


def ViewKey(SheetName: str, ViewName: str) -> tuple[str, str]:
    return (SheetName.casefold(), ViewName.casefold())


# the creation index is needed because coincident views share one position
KViewIndex = RegexLib.compile(r"(\d+)$")


# the creation index is needed because coincident views share one position
def ViewIndex(ViewName: str) -> int:
    Match = KViewIndex.search(ViewName)
    if Match is None:
        raise SldprtFormatError("drawing view name has no creation index")
    return int(Match.group(1))


# the sheet and view names are the stable key so a reordered value still binds
def BindViews(
    SourceData: DrawingData, DataValue: DrawingData
) -> tuple[tuple[DrawingView, DrawingView], ...]:
    SourceViews = tuple(
        (SheetValue.Name, ViewValue)
        for SheetValue in SourceData.Sheets
        for ViewValue in SheetValue.Views
    )
    DataViews = tuple(
        (SheetValue.Name, ViewValue)
        for SheetValue in DataValue.Sheets
        for ViewValue in SheetValue.Views
    )
    if len(SourceViews) != len(DataViews):
        raise SldprtFormatError("drawing view count does not match the source")
    SourceByKey = {
        ViewKey(SheetName, ViewValue.Name): ViewValue
        for SheetName, ViewValue in SourceViews
    }
    if len(SourceByKey) != len(SourceViews):
        raise SldprtFormatError("drawing source repeats a sheet and view name")
    Matched: dict[tuple[str, str], DrawingView] = {}
    UnmatchedData: list[tuple[str, DrawingView]] = []
    for SheetName, DataView in DataViews:
        ViewKeyValue = ViewKey(SheetName, DataView.Name)
        if ViewKeyValue in SourceByKey and ViewKeyValue not in Matched:
            Matched[ViewKeyValue] = DataView
        else:
            UnmatchedData.append((SheetName, DataView))
    UnmatchedSource = [
        (SheetName, ViewValue)
        for SheetName, ViewValue in SourceViews
        if ViewKey(SheetName, ViewValue.Name) not in Matched
    ]
    if UnmatchedData or UnmatchedSource:
        raise SldprtFormatError("drawing view names do not match the source")
    return tuple(
        (ViewValue, Matched[ViewKey(SheetName, ViewValue.Name)])
        for SheetName, ViewValue in SourceViews
    )
