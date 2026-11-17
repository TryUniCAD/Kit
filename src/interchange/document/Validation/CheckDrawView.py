from interchange.assembly.TransformMatrix import TransformMatrix
from interchange.document.Models.Drawing.DrawingView import DrawingView
from interchange.document.Models.Drawing.ValidMeasure import (
    IsFiniteMeasure,
    IsValidRatio,
)
from interchange.document.Models.Drawing.ValidOutline import IsValidOutline
from interchange.document.Models.Drawing.ValidText import HasDrawingText
from interchange.geometry.Models.VectorPlane import PlaneVector


# invalid view geometry must fail at the portable document boundary
def CheckDrawView(ViewValue: DrawingView) -> tuple[str, ...]:
    Errors: list[str] = []
    if not (
        HasDrawingText(ViewValue.EntityName)
        and HasDrawingText(ViewValue.ConfigurationName)
    ):
        Errors.append("drawing view requires name and model configuration")
    Orientation: object = ViewValue.OrientationName
    if Orientation is not None and not HasDrawingText(Orientation):
        Errors.append("drawing view orientation name must be nonempty text")
    Position = CastValue(object, ViewValue.PositionValue)
    if not isinstance(Position, PlaneVector) or not (
        IsFiniteMeasure(Position.x) and IsFiniteMeasure(Position.y)
    ):
        Errors.append("drawing view requires a finite sheet position")
    if ViewValue.ScaleRatio is not None and not IsValidRatio(ViewValue.ScaleRatio):
        Errors.append("drawing view requires a positive scale ratio")
    Transform = CastValue(object, ViewValue.ModelToSheet)
    if Transform is not None and (
        not isinstance(Transform, TransformMatrix) or not Transform.IsFinite()
    ):
        Errors.append("drawing view requires a finite model to sheet transform")
    Outline: object = ViewValue.OutlineValues
    if Outline is not None and not IsValidOutline(Outline):
        Errors.append("drawing view requires an ordered finite outline")
    return tuple(Errors)


from typing import cast as CastValue
