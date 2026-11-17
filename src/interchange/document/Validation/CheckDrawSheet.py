from typing import cast as CastValue

from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet
from interchange.document.Models.Drawing.DrawingView import DrawingView
from interchange.document.Models.Drawing.ValidMeasure import (
    IsFiniteMeasure,
    IsValidRatio,
)
from interchange.document.Models.Drawing.ValidText import HasDrawingText


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
    return tuple(Errors)


# graph validation must check record types before traversing view properties
def HasValidViews(Values: object) -> bool:
    return isinstance(Values, tuple) and all(
        isinstance(Value, DrawingView)
        for Value in CastValue(tuple[object, ...], Values)
    )
