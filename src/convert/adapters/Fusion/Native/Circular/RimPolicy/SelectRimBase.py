from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Graph.OrderedFeatures import OrderedFeatures


# a third history operation must have complete ordered ownership before its body can be projected
def SelectRimBase(Graph: NativeGraph) -> tuple[ExtrudeContext, NativeNode]:
    Component = Graph.OneClass("FusionComponent")
    Fragment, Features = OrderedFeatures(Graph, Component)
    if tuple(Value.ClassName for Value in Features) != (
        "DcSketch",
        "DcExtrudeFeature",
        "DcFilletEdgeFeature",
    ):
        raise ValueError("Native rim fillet requires sketch extrusion and fillet order")
    SameNodes(
        Features,
        tuple(
            Value
            for Value in Graph.Nodes.values()
            if Value.SegmentId == 0 and Graph.HasBase(Value, "DcFeature")
        ),
    )
    SketchFeature, Extrude, Feature = Features
    Sketch = ResolveField(Graph, SketchFeature, "rSketch", "MSketch")
    Bodies = LinkedNodes(Graph, Extrude, "dcBodies")
    if len(Bodies) != 1 or Bodies[0].ClassName != "DcBody":
        raise ValueError("Native rim extrusion requires one owned body")
    return (
        ExtrudeContext(
            Component,
            Fragment,
            SketchFeature,
            Sketch,
            ResolveField(Graph, Sketch, "UCS", "CoordinateSystem"),
            Extrude,
            ResolveField(Graph, Extrude, "rAlongDistance", "DcDoubleParameter"),
            ResolveField(Graph, Extrude, "rTaperAngle", "DcDoubleParameter"),
            ResolveField(Graph, Bodies[0], "rBody", "Body"),
            Bodies[0],
        ),
        Feature,
    )
