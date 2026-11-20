from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# the creation-order record links each component to its saved timeline in execution order
def OrderedFeatures(
    Graph: NativeGraph, Component: NativeNode
) -> tuple[NativeNode, tuple[NativeNode, ...]]:
    Fragment = ResolveField(Graph, Component, "rDesignFragment", "DcDesignFragment")
    Order = ResolveField(
        Graph, Fragment, "rCreationOrderFeatures", "DcCreationOrderFeatures"
    )
    Features = LinkedNodes(Graph, Order, "representationFeatures")
    if len({Feature.Identity for Feature in Features}) != len(Features):
        raise ValueError("Native Fusion creation order repeats a feature")
    return Fragment, Features
