from collections.abc import Mapping
from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Core.Preparation.Readback.ExactMm import ExactMm
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import SketchEntity
from interchange.geometry.Models.VectorPlane import PlaneVector


# each endpoint must come from the public line and its actual typed native point index
def ReadColdEdge(
    Entity: SketchEntity,
    Points: tuple[Mapping[str, object], ...],
    *,
    IsScaled: bool = False,
) -> SketchEntity:
    PairValue = Entity.attributes.get("native_point_indices")
    Geometry = Entity.geometry
    if type(Geometry) is not LineGeometry or type(PairValue) is not tuple:
        raise ValueError("SOLIDWORKS cold line has no typed point pair")
    Indices = CastValue(tuple[object, ...], PairValue)
    if len(Indices) != 2:
        raise ValueError("SOLIDWORKS cold line has no typed point pair")
    StartIndex, EndIndex = Indices
    if (
        type(StartIndex) is not int
        or type(EndIndex) is not int
        or not 0 <= StartIndex < len(Points)
        or not 0 <= EndIndex < len(Points)
    ):
        raise ValueError("SOLIDWORKS cold line points are outside the typed sketch")
    StartValue, Finish = Points[StartIndex], Points[EndIndex]
    return ReplaceValue(
        Entity,
        geometry=LineGeometry(
            PlaneVector(
                ExactMm(StartValue.get("x"), Geometry.start.x, IsScaled=IsScaled),
                ExactMm(StartValue.get("y"), Geometry.start.y, IsScaled=IsScaled),
            ),
            PlaneVector(
                ExactMm(Finish.get("x"), Geometry.end.x, IsScaled=IsScaled),
                ExactMm(Finish.get("y"), Geometry.end.y, IsScaled=IsScaled),
            ),
        ),
        attributes=FreezeMapping(),
        provenance=None,
    )
