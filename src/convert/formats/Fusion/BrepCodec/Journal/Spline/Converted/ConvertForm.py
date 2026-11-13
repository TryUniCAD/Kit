from dataclasses import replace as ReplaceValue

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


def UnitSpans(Surface: TsplineSurface) -> TsplineSurface:
    Edges = tuple(
        ReplaceValue(EdgeValue, KnotInterval=1.0)
        for EdgeValue in Surface.Topology.Edges
    )
    return ReplaceValue(Surface, Topology=ReplaceValue(Surface.Topology, Edges=Edges))


def ConvertForm(Surface: TsplineSurface) -> FormBody:
    CheckSurface(Surface)
    if StencilKey(Surface) in ReadShapes():
        return CageBody(Surface)
    if StencilKey(UnitSpans(Surface)) in ReadShapes():
        raise ValueError("Fusion Form stencil conversion needs unit knot intervals")
    BodyValue = GridBody(ConvertGrid(Surface))
    CheckFolds(BodyValue)
    return BodyValue
