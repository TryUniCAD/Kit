from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.ConvertGrid import (
    ConvertGrid,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.CheckFolds import (
    CheckFolds,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.GridBody import GridBody
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageBody import CageBody
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ReadShapes import (
    ReadShapes,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilKey import (
    StencilKey,
)
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface


def ConvertForm(Surface: TsplineSurface) -> FormBody:
    CheckSurface(Surface)
    if StencilKey(Surface) in ReadShapes():
        return CageBody(Surface)
    BodyValue = GridBody(ConvertGrid(Surface))
    CheckFolds(BodyValue)
    return BodyValue
