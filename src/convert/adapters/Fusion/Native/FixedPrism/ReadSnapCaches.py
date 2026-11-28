from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# the two snapshot caches must belong to the selected tool and profile in this component
def ReadSnapCaches(
    Graph: NativeGraph, Context: ExtrudeContext, AssetId: str
) -> tuple[NativeNode, NativeNode]:
    ToolNode = ResolveField(
        Graph, Context.Extrude, "rExtrudeToolBody", "DcExtrudeToolBody"
    )
    Region = Graph.OneClass("SketchRegionRef", Context.Sketch.SegmentId)
    Tools = LinkedNodes(Graph, ToolNode, "toolbodyCaches")
    Regions = tuple(
        CacheNode
        for CacheNode in LinkedNodes(Graph, Region, "caches")
        if CacheNode.ClassName == "ETCachedTopology"
    )
    if len(Tools) != 1 or len(Regions) != 1 or Tools[0].ClassName != "ETCachedTopology":
        raise ValueError("Native fixed snapshot requires one tool and one region cache")
    SameNodes(
        (*Tools, *Regions), Graph.ByClass("ETCachedTopology", Context.Sketch.SegmentId)
    )
    Scope = {
        "assetId": AssetId,
        "scopeEntityIdentifier": Context.Component.Fields["persistentId"],
        "scopeIdType": 2,
        "segmentId": Context.Component.SegmentId,
    }
    for CacheNode in (*Tools, *Regions):
        if (
            ObjectFields(CacheNode.Fields["scope"]) != Scope
            or CacheNode.Fields["progenitor"] is not None
        ):
            raise ValueError(
                "Native fixed snapshot cache scope disagrees with its component"
            )
    return Tools[0], Regions[0]
