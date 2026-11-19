from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.ReadPointPair import (
    ReadPointPair,
)


# the signed origin profile measures its negative v edge from the anchor and keeps both physical lengths positive
def ReadRectEdges(
    GeometryValue: PolygonGraph, NegativeV: bool
) -> tuple[tuple[int, int, float], tuple[int, int, float]]:
    Positions = tuple(
        ReadPointPair(PointValue) for PointValue in GeometryValue.PointValues
    )
    if len(Positions) != 4:
        raise ValueError("rectangle drivers require four actual contour points")
    StartU, StartV = Positions[0]
    EndU, EndV = Positions[2]
    LengthU = EndU - StartU
    LengthV = StartV - EndV if NegativeV else EndV - StartV
    if (
        Positions[1] != (EndU, StartV)
        or Positions[3] != (StartU, EndV)
        or not IsFinite(LengthU)
        or not IsFinite(LengthV)
        or min(LengthU, LengthV) <= 1e-8
    ):
        raise ValueError("rectangle drivers require the ordered local axis edges")
    if NegativeV:
        return (0, 1, LengthU), (0, 3, LengthV)
    return (0, 1, LengthU), (1, 2, LengthV)
