from convert.adapters.Fusion.Native.Cuts.MakeCutContext import MakeCutContext
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.OrderedFeatures import OrderedFeatures
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNodes, LinkedNodes


# a bounded modifying history must contain exactly two real sketch and extrusion pairs
def SelectCutPair(Graph: NativeGraph) -> tuple[ExtrudeContext, ExtrudeContext]:
    _, Features = OrderedFeatures(Graph, Graph.OneClass("FusionComponent"))
    if tuple(Value.ClassName for Value in Features) != (
        "DcSketch",
        "DcExtrudeFeature",
        "DcSketch",
        "DcExtrudeFeature",
    ):
        raise ValueError(
            "Native cut projection requires two sketch and extrusion pairs"
        )
    SameNodes(
        Features,
        tuple(
            Value
            for Value in Graph.Nodes.values()
            if Value.SegmentId == 0 and Graph.HasBase(Value, "DcFeature")
        ),
    )
    Bodies = LinkedNodes(Graph, Features[1], "dcBodies")
    if len(Bodies) != 1 or Bodies[0].ClassName != "DcBody":
        raise ValueError("Native cut stock has no unique created body")
    return MakeCutContext(Graph, Features[0], Features[1], Bodies[0]), MakeCutContext(
        Graph, Features[2], Features[3], Bodies[0]
    )
