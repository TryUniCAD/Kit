from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimMap import ReadRimMap
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    RequireFields,
    ResolveField,
)
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# healthy parameter flags differ from feature flags so dynamic checks must retain the actual owner role
def CheckRimDynamic(Graph: NativeGraph, Owner: NativeNode, Nodes: NativeNode) -> None:
    RequireFields(
        Owner,
        {
            "isActive": True,
            "isEdited": False,
            "isEliminated": False,
            "rGroupRepresentative": None,
        },
    )
    if Graph.Resolve(Owner.Fields["rParent"]) != Nodes:
        raise ValueError("Native rim dynamic node belongs to another collection")
    Dynamic = ResolveField(Graph, Owner, "rDynamicUpdateData", "DynamicUpdateData")
    if Graph.Resolve(Dynamic.Fields["rOwnerNode"]) != Owner:
        raise ValueError("Native rim dynamic update owner is not reciprocal")
    Healthy = Owner.ClassName not in ("DcDoubleParameter", "DcComponent")
    RequireFields(
        Dynamic,
        {"isBodyOK": Healthy, "isPredecessorOK": Healthy, "xRefPredecessorsHash": 0},
    )
    EmptyFields(Dynamic, ("bodies",))
    if IntegerValue(Dynamic.Fields["timeStamp"]) < 0:
        raise ValueError("Native rim dynamic timestamp is invalid")
    for Reference, Stamp in ReadRimMap(Dynamic.Fields["predecessors"]).items():
        Predecessor = Graph.Resolve(Reference)
        Update = ResolveField(
            Graph, Predecessor, "rDynamicUpdateData", "DynamicUpdateData"
        )
        if IntegerValue(Stamp) != IntegerValue(Update.Fields["timeStamp"]):
            raise ValueError("Native rim predecessor timestamp is stale")
    if not Healthy:
        EmptyFields(Dynamic, ("predecessors",))
    if "status" in Owner.Fields:
        Status = ResolveField(Graph, Owner, "status", "DcStatus")
        RequireFields(Status, {"statusType": 0})
        EmptyFields(Status, ("statusCodes",))
