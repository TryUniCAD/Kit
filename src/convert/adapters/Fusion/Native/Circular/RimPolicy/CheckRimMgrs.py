from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimDeps import CheckRimDeps
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimDynamic import (
    CheckRimDynamic,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimIds import CheckRimIds
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph


# complete manager ownership prevents orphan source nodes from disappearing behind a valid final body
def CheckRimMgrs(Graph: NativeGraph, Context: RimContext) -> None:
    Fragment = Context.Extrusion.Fragment
    Nodes = ResolveField(Graph, Fragment, "rNodes", "DcNodes")
    Children = LinkedNodes(Graph, Nodes, "children")
    for FieldName, ClassName in (
        ("rComputeManager", "DcComputeManager"),
        ("rDependencyManager", "DcDependencyManager"),
        ("rAssociationManager", "DcAssociationManager"),
        ("rFeatureIdManager", "DcFeatureIdManager"),
    ):
        Manager = ResolveField(Graph, Fragment, FieldName, ClassName)
        if Graph.Resolve(Manager.Fields["rOwnerFragment"]) != Fragment:
            raise ValueError("Native rim manager belongs to another fragment")
    Compute = Graph.OneClass("DcComputeManager")
    RequireFields(Compute, {"sortIsCurrent": True})
    SortedNodes = LinkedNodes(Graph, Compute, "sortedNodesAll")
    SameNodes(SortedNodes, Children)
    if len({Value.Identity for Value in SortedNodes}) != len(Children):
        raise ValueError("Native rim compute collection repeats source nodes")
    CheckRimDeps(Graph, Context)
    EmptyFields(
        Graph.OneClass("DcAssociationManager"),
        ("associationHolderMap", "featureAssociationMap"),
    )
    CheckRimIds(Graph, Context)
    Updates = tuple(
        ResolveField(Graph, Value, "rDynamicUpdateData", "DynamicUpdateData")
        for Value in Children
    )
    SameNodes(Updates, Graph.ByClass("DynamicUpdateData"))
    if len({Value.Identity for Value in Updates}) != len(Updates):
        raise ValueError("Native rim source nodes share dynamic update data")
    for Value in Children:
        CheckRimDynamic(Graph, Value, Nodes)
    SameNodes(
        tuple(
            ResolveField(Graph, Value, "status", "DcStatus")
            for Value in Children
            if "status" in Value.Fields
        ),
        Graph.ByClass("DcStatus"),
    )
    if IntegerValue(Context.Extrusion.Extrude.Fields["endModelHS"]) != IntegerValue(
        Context.Feature.Fields["startModelHS"]
    ) or IntegerValue(Context.Feature.Fields["endModelHS"]) <= IntegerValue(
        Context.Feature.Fields["startModelHS"]
    ):
        raise ValueError("Native rim history does not continue its extrusion")
