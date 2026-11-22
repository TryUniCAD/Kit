from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircGeom import (
    ReadCircGeom,
)
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.Models.Sketch import Sketch


# the ordinary circle emitter already represents its coincident auxiliary centre point
def ReadStockCircle(SketchValue: Sketch) -> CircleInput:
    Circles = tuple(
        Value for Value in SketchValue.entities if Value.kind == GeometryKind.KCircle
    )
    if SketchValue.constraints or SketchValue.parameter_ids or len(Circles) != 1:
        raise ValueError("the through cut requires its sole free circular profile")
    Circle = Circles[0]
    Geometry = Circle.geometry
    Points = tuple(Value for Value in SketchValue.entities if Value is not Circle)
    if (
        type(Geometry) is not CircleGeometry
        or len(Points) > 1
        or any(
            Value.kind != GeometryKind.KPoint
            or type(Value.geometry) is not PointGeometry
            or Value.geometry.point != Geometry.center
            or Value.construction
            or Value.fixed
            or Value.provenance is not None
            or Value.attributes
            for Value in Points
        )
    ):
        raise ValueError("the through cut has an unsupported circle or centre owner")
    return ReadCircGeom(ReplaceValue(SketchValue, entities=(Circle,)), 0.001)
