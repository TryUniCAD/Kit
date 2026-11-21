from typing import cast as CastValue

from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingModelRef import DrawingModelRef
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet
from interchange.document.Models.Drawing.ValidText import HasDrawingText, HasUniqueIds
from interchange.document.Validation.CheckDrawSheet import (
    CheckDrawSheet,
    HasValidNotes,
    HasValidViews,
)
from interchange.document.Validation.CheckDrawView import CheckDrawView


# drawing graph integrity must hold before consumers traverse active sheets or links
def CheckDrawing(DrawingValue: object) -> tuple[str, ...]:
    if not isinstance(DrawingValue, DrawingData):
        return ("document drawing must be DrawingData",)
    if not HasDrawRecords(DrawingValue.Sheets, DrawingSheet) or not DrawingValue.Sheets:
        return ("drawing requires a tuple of sheets",)
    if not HasDrawRecords(DrawingValue.ModelRefs, DrawingModelRef):
        return ("drawing requires a tuple of model references",)
    Errors = list(CheckDrawLinks(DrawingValue))
    for SheetValue in DrawingValue.Sheets:
        Errors.extend(CheckDrawSheet(SheetValue))
        if HasValidViews(SheetValue.Views):
            for ViewValue in SheetValue.Views:
                Errors.extend(CheckDrawView(ViewValue))
    return tuple(Errors)


# malformed nested wire values need validation before they become graph nodes
def HasDrawRecords(Values: object, RecordType: type[object]) -> bool:
    return isinstance(Values, tuple) and all(
        isinstance(Value, RecordType) for Value in CastValue(tuple[object, ...], Values)
    )


# sheet and viewport identifiers are document wide so links remain unambiguous
def CheckDrawLinks(DrawingValue: DrawingData) -> tuple[str, ...]:
    Errors: list[str] = []
    SheetIds = tuple(SheetValue.EntityId for SheetValue in DrawingValue.Sheets)
    ModelIds = tuple(LinkValue.EntityId for LinkValue in DrawingValue.ModelRefs)
    Views = tuple(
        ViewValue
        for SheetValue in DrawingValue.Sheets
        if HasValidViews(SheetValue.Views)
        for ViewValue in SheetValue.Views
    )
    ViewIds = tuple(ViewValue.EntityId for ViewValue in Views)
    NoteIds = tuple(
        NoteValue.EntityId
        for SheetValue in DrawingValue.Sheets
        if SheetValue.Notes is not None and HasValidNotes(SheetValue.Notes)
        for NoteValue in SheetValue.Notes
    )
    if not HasUniqueIds((*SheetIds, *ModelIds, *ViewIds, *NoteIds)):
        Errors.append(
            "drawing sheet, view, model and note ids must be nonempty and unique"
            if NoteIds
            else "drawing sheet, view and model ids must be nonempty and unique"
        )
    if DrawingValue.ActiveSheetId not in SheetIds:
        Errors.append("drawing active sheet id must reference a sheet")
    if any(ViewValue.ModelRefId not in ModelIds for ViewValue in Views):
        Errors.append("drawing view references an unknown model id")
    if any(
        not HasDrawingText(LinkValue.SourcePath)
        or not HasDrawingText(LinkValue.SourceFormatId)
        for LinkValue in DrawingValue.ModelRefs
    ):
        Errors.append("drawing model reference requires path and source format")
    return tuple(Errors)
