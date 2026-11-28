from convert.adapters.solidworks.Archive.Construction.Circles.CircleGraph import (
    CircleGraph,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipseGraph import (
    EllipseGraph,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)


# rectangle dimension helpers must reject another profile family before using its concrete line and point owners
def RequirePolygon(Value: PolygonGraph | CircleGraph | EllipseGraph) -> PolygonGraph:
    if type(Value) is not PolygonGraph:
        raise ValueError("rectangle dimensions require their actual polygon graph")
    return Value
