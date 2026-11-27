from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    RequireFields,
    ResolveField,
    SameNumbers,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# reciprocal parameter owners prevent equal numeric values from disguising a different driving feature
def CheckRimBinding(
    Graph: NativeGraph,
    Binding: NativeNode,
    Owner: NativeNode,
    Table: NativeNode,
    Nodes: NativeNode,
    RoleName: str,
    UnitName: str,
) -> NativeNode:
    RequireFields(
        Binding,
        {
            "isActive": True,
            "isEdited": False,
            "isEliminated": False,
            "rGroupRepresentative": None,
        },
    )
    if (
        Graph.Resolve(Binding.Fields["rrOwnerFeature"]) != Owner
        or Graph.Resolve(Binding.Fields["rParentFeature"]) != Owner
        or Graph.Resolve(Binding.Fields["rParent"]) != Nodes
    ):
        raise ValueError("Native rim parameter binding has inconsistent owners")
    Parameter = ResolveField(Graph, Binding, "parameter", "Parameter")
    if (
        Graph.Resolve(Parameter.Fields["dcParameter"]) != Binding
        or Graph.Resolve(Parameter.Fields["rParent"]) != Table
    ):
        raise ValueError("Native rim parameter binding is not reciprocal")
    RequireFields(
        Parameter,
        {
            "name": RoleName,
            "unit": UnitName,
            "isUserDefined": False,
            "isDirty": False,
            "isDriven": False,
            "isOrphan": False,
            "isExternal": False,
            "expressionType": 0,
            "booleanValue": False,
            "textValue": "",
            "rClientObject": None,
            "group": None,
        },
    )
    SameNumbers(
        (NumberValue(Parameter.Fields["value"]),),
        (NumberValue(Binding.Fields["value"]),),
    )
    return Parameter
