from __future__ import annotations

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.drawing.Models import DrawingData, DrawingView


# the sheet is needed because two sheets can repeat a view name
def ViewKey(SheetName: str, ViewName: str) -> tuple[str, str]:
    return (SheetName.casefold(), ViewName.casefold())


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
    if len(UnmatchedData) != len(UnmatchedSource):
        raise SldprtFormatError("drawing view names do not match the source")
    if len(UnmatchedData) > 1:
        raise SldprtFormatError("drawing renames more than one view")
    for (SheetName, DataView), (SourceSheet, SourceView) in zip(
        UnmatchedData, UnmatchedSource, strict=True
    ):
        if SheetName.casefold() != SourceSheet.casefold():
            raise SldprtFormatError("drawing renamed view changed its sheet")
        Matched[ViewKey(SourceSheet, SourceView.Name)] = DataView
    return tuple(
        (ViewValue, Matched[ViewKey(SheetName, ViewValue.Name)])
        for SheetName, ViewValue in SourceViews
    )
