from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField


# each timeline pair resolves its own sketch and extent while sharing the actual design body
def MakeCutContext(
    Graph: NativeGraph,
    SketchFeature: NativeNode,
    Extrude: NativeNode,
    DcBody: NativeNode,
) -> ExtrudeContext:
    Component = Graph.OneClass("FusionComponent")
    Sketch = ResolveField(Graph, SketchFeature, "rSketch", "MSketch")
    return ExtrudeContext(
        Component,
        ResolveField(Graph, Component, "rDesignFragment", "DcDesignFragment"),
        SketchFeature,
        Sketch,
        ResolveField(Graph, Sketch, "UCS", "CoordinateSystem"),
        Extrude,
        ResolveField(Graph, Extrude, "rAlongDistance", "DcDoubleParameter"),
        ResolveField(Graph, Extrude, "rTaperAngle", "DcDoubleParameter"),
        ResolveField(Graph, DcBody, "rBody", "Body"),
        DcBody,
    )
