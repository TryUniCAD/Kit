from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    RequireFields,
    ResolveField,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# model slots must follow actual feature ownership rather than one saved parameter allocation order
def CheckFixBind(
    Graph: NativeGraph,
    Binding: NativeNode,
    Owner: NativeNode,
    Table: NativeNode,
    DcNodes: NativeNode,
    IsTaper: bool,
) -> NativeNode:
    Param = ResolveField(Graph, Binding, "parameter", "Parameter")
    Update = ResolveField(Graph, Binding, "rDynamicUpdateData", "DynamicUpdateData")
    RequireFields(
        Binding,
        {
            "rrOwnerFeature": LocalRef(Owner.ObjectId),
            "rParentFeature": LocalRef(Owner.ObjectId),
            "rParent": LocalRef(DcNodes.ObjectId),
            "isActive": True,
            "isEdited": False,
            "isEliminated": False,
            "rGroupRepresentative": None,
        },
    )
    RequireFields(
        Param,
        {
            "rParent": LocalRef(Table.ObjectId),
            "dcParameter": LocalRef(Binding.ObjectId),
            "unit": "deg" if IsTaper else "mm",
            "isUserDefined": False,
            "isDriven": False,
            "group": None,
            "rClientObject": None,
        },
    )
    RequireFields(
        Update,
        {
            "rOwnerNode": LocalRef(Binding.ObjectId),
            "isBodyOK": False,
            "isPredecessorOK": False,
            "xRefPredecessorsHash": 0,
        },
    )
    EmptyFields(Update, ("bodies", "predecessors"))
    Amount = NumberValue(Param.Fields["value"])
    if Amount != NumberValue(Binding.Fields["value"]) or (
        Amount != 0 if IsTaper else Amount <= 0
    ):
        raise ValueError("Native fixed rectangle driver values or zero taper disagree")
    return Param
