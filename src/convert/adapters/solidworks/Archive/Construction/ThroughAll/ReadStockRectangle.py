from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadRectSketch import (
    ReadRectSketch,
)
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import Sketch


# each rectangle relation must point to its actual line before the constructor allocates its canonical ordered contour
def ReadStockRect(
    SketchValue: Sketch, UnitScale: float
) -> tuple[tuple[float, float], ...]:
    Vertices = ReadRectSketch(ReplaceValue(SketchValue, constraints=()), UnitScale)
    Expected: dict[str, str] = {}
    for Entity in SketchValue.entities:
        Geometry = Entity.geometry
        if type(Geometry) is not LineGeometry:
            raise ValueError("through-all stock requires actual rectangle lines")
        if Geometry.start.x == Geometry.end.x:
            Expected[Entity.id] = "vertical"
        elif Geometry.start.y == Geometry.end.y:
            Expected[Entity.id] = "horizontal"
        else:
            raise ValueError("through-all stock edges must follow the sketch axes")
    Actual: dict[str, str] = {}
    for Relation in SketchValue.constraints:
        if (
            len(Relation.references) != 1
            or Relation.references[0].point
            or Relation.parameter_id is not None
            or not Relation.driving
            or Relation.suppressed
            or Relation.provenance is not None
            or Relation.attributes
        ):
            raise ValueError("through-all stock requires unary driving axis relations")
        OwnerId = Relation.references[0].entity_id
        if OwnerId in Actual:
            raise ValueError("through-all stock has a duplicate line relation")
        Actual[OwnerId] = Relation.kind
    if Actual != Expected:
        raise ValueError("through-all stock axis relations must match its four lines")
    LeftBound, Right = sorted({Point[0] for Point in Vertices})
    Bottom, TopBound = sorted({Point[1] for Point in Vertices})
    return (
        (LeftBound, Bottom),
        (Right, Bottom),
        (Right, TopBound),
        (LeftBound, TopBound),
    )
