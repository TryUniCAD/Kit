from typing import cast as CastValue

from interchange.document.Models.Drawing.DrawingNote import DrawingNote
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet
from interchange.document.Models.Drawing.DrawingView import DrawingView
from interchange.document.Models.Drawing.ValidMeasure import (
    IsFiniteMeasure,
    IsValidRatio,
)
from interchange.document.Models.Drawing.ValidText import HasDrawingText
from interchange.geometry.Models.VectorSpace import SpaceVector


# a drawing must have bounded paper and a typed view list for consumer access
def CheckDrawSheet(SheetValue: DrawingSheet) -> tuple[str, ...]:
    Errors: list[str] = []
    if not HasDrawingText(SheetValue.EntityName):
        Errors.append("drawing sheet requires a name")
    if not all(
        IsFiniteMeasure(Value) and Value > 0
        for Value in (SheetValue.SheetWidth, SheetValue.SheetHeight)
    ):
        Errors.append("drawing sheet requires positive width and height")
    if not IsValidRatio(SheetValue.ScaleRatio):
        Errors.append("drawing sheet requires a positive scale ratio")
    if not HasValidViews(SheetValue.Views):
        Errors.append("drawing sheet requires a tuple of drawing views")
    if SheetValue.Notes is not None:
        if not HasValidNotes(SheetValue.Notes):
            Errors.append("drawing sheet requires typed plain notes")
        else:
            for NoteValue in SheetValue.Notes:
                Position = CastValue(object, NoteValue.PositionValue)
                if not HasDrawingText(NoteValue.TextValue):
                    Errors.append("drawing note requires nonempty text")
                if not isinstance(Position, SpaceVector) or not all(
                    IsFiniteMeasure(Component)
                    for Component in (Position.XCoord, Position.YCoord, Position.ZCoord)
                ):
                    Errors.append("drawing note requires a finite position")
    return tuple(Errors)


# graph validation must check record types before traversing view properties
def HasValidViews(Values: object) -> bool:
    return isinstance(Values, tuple) and all(
        isinstance(Value, DrawingView)
        for Value in CastValue(tuple[object, ...], Values)
    )


# malformed wire note records must be refused before accessing their positions
def HasValidNotes(Values: object) -> bool:
    return isinstance(Values, tuple) and all(
        isinstance(Value, DrawingNote)
        for Value in CastValue(tuple[object, ...], Values)
    )
