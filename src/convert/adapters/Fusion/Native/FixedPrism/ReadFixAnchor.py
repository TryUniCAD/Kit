from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import PointCoords
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# fixed native corner custody keeps the actual anchor distinct from the sketch origin
def ReadFixAnchor(
    Graph: NativeGraph, Lines: tuple[NativeNode, ...]
) -> tuple[NativeNode, NativeNode]:
    Points = Graph.ByClass("Point3D")
    Origins = tuple(Point for Point in Points if Point.Fields["isOrigin"] is True)
    Starts = tuple(
        ResolveField(Graph, LineNode, "rStartPoint", "Point3D") for LineNode in Lines
    )
    Anchors = tuple(Point for Point in Starts if Point.Fields["isFixed"] is True)
    if len(Origins) != 1 or len(Anchors) != 1 or Origins[0] in Starts:
        raise ValueError(
            "Native fixed rectangle requires two distinct fixed point identities"
        )
    Anchor, Origin = Anchors[0], Origins[0]
    SameNodes(Points, (*Starts, Origin))
    RequireFields(Origin, {"isFixed": True})
    RequireFields(Anchor, {"isOrigin": False})
    if any(
        PointCoords(Point.Fields["point"]) != (0.0, 0.0, 0.0)
        for Point in (Anchor, Origin)
    ):
        raise ValueError("Native fixed rectangle is not anchored at the sketch origin")
    return Anchor, Origin
