from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    RequireFields,
    ResolveField,
    SameNumbers,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# invalid binding input must fail here so public document claims remain grounded in native records
def CheckBinding(
    Graph: NativeGraph, Binding: NativeNode, Context: ExtrudeContext
) -> NativeNode:
    RequireFields(Binding, {"isActive": True, "isEdited": False, "isEliminated": False})
    if (
        Graph.Resolve(Binding.Fields["rrOwnerFeature"]) != Context.Extrude
        or Graph.Resolve(Binding.Fields["rParentFeature"]) != Context.Extrude
    ):
        raise ValueError("Native extrusion parameter owner is inconsistent")
    Parameter = ResolveField(Graph, Binding, "parameter", "Parameter")
    if Graph.Resolve(Parameter.Fields["dcParameter"]) != Binding:
        raise ValueError("Native parameter binding is not reciprocal")
    SameNumbers(
        (NumberValue(Parameter.Fields["value"]),),
        (NumberValue(Binding.Fields["value"]),),
    )
    return Parameter
