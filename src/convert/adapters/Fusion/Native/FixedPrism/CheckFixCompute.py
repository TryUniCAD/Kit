from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Rectangle.CheckRectDeps import CheckRectDeps


# the two independent sketch drivers may exchange compute positions without changing their dependency edges
def CheckFixCompute(
    Graph: NativeGraph, Context: ExtrudeContext, Bindings: tuple[NativeNode, ...]
) -> None:
    Compute = ResolveField(
        Graph, Context.Fragment, "rComputeManager", "DcComputeManager"
    )
    Order = tuple(
        NodeValue
        for NodeValue in LinkedNodes(Graph, Compute, "sortedNodesAll")
        if NodeValue in Bindings
    )
    SameNodes(Order, Bindings)
    StyleOwners = Graph.ByClass("VMBrepRef")
    if len(StyleOwners) > 1:
        raise ValueError("Native fixed rectangle supports one saved face appearance")
    CheckRectDeps(Graph, Context, Order, next(iter(StyleOwners), None))
