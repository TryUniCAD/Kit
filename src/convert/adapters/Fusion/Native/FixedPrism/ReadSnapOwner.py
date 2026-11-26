from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import TextValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# the history and snapshot serializers must each bind back to their own design collection
def ReadSnapOwner(
    Graph: NativeGraph, Context: ExtrudeContext, PartName: str
) -> NativeNode:
    Bodies = ResolveField(Graph, Context.Component, "rBodies", "Bodies")
    CacheBodies = ResolveField(Graph, Context.Component, "rCacheBodies", "Bodies")
    History = ResolveField(Graph, Bodies, "rBRepSerializer", "BRepHistorySerializer")
    Cache = ResolveField(Graph, CacheBodies, "rBRepSerializer", "BRepSerializer")
    if (
        Bodies == CacheBodies
        or ResolveField(Graph, History, "rBodies", "Bodies") != Bodies
        or ResolveField(Graph, Cache, "rBodies", "Bodies") != CacheBodies
    ):
        raise ValueError("Native fixed snapshot serializer ownership is not reciprocal")
    if PartName != "Breps.BlobParts/" + TextValue(Cache.Fields["partName"]):
        raise ValueError("Native fixed snapshot is not the selected serializer part")
    return Cache
