from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNodes, LinkedNodes
from convert.adapters.Fusion.Native.Rectangle.ReadRectangle import ReadRectangle
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion


# independently decoded profiles must together account for every native point and line
def ReadCutShapes(
    Graph: NativeGraph, Contexts: tuple[ExtrudeContext, ExtrudeContext], AssetId: str
) -> tuple[RectGeometry, RectGeometry]:
    Shapes = tuple(ReadRectangle(Graph, Context, Scoped=True) for Context in Contexts)
    Children = tuple(
        Value
        for Context in Contexts
        for Value in LinkedNodes(Graph, Context.Sketch, "children")
    )
    SameNodes(
        tuple(Value for Value in Children if Value.ClassName == "Point3D"),
        Graph.ByClass("Point3D"),
    )
    SameNodes(
        tuple(Value for Shape in Shapes for Value in Shape.LineNodes),
        Graph.ByClass("Line3D"),
    )
    for Context, Shape in zip(Contexts, Shapes, strict=True):
        CheckRegion(Graph, Context, Shape.LineNodes, AssetId, Scoped=True)
    return Shapes[0], Shapes[1]
