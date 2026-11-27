from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimRecipe import (
    CheckRimRecipe,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion


# profile and edge references require disjoint complete ownership before scoped validation is permitted
def CheckRimSelect(Graph: NativeGraph, Context: RimContext, AssetId: str) -> None:
    Extrusion = Context.Extrusion
    Selected = ResolveField(Graph, Context.EdgeData, "connectedEdgeRef", "ModelDataRef")
    if LinkedNodes(Graph, Context.Feature, "targetDataRefs") != (
        Selected,
    ) or LinkedNodes(Graph, Context.SelectedRef, "refBodies") != (Extrusion.DcBody,):
        raise ValueError("Native rim selection references a different target or body")
    SameNodes(
        LinkedNodes(Graph, Context.Feature, "childNodes"),
        (Selected, Context.SelectedRef, Context.Radius, Context.Weight),
    )
    Nodes = ResolveField(Graph, Extrusion.Fragment, "rNodes", "DcNodes")
    for Value in (Selected, Context.SelectedRef):
        RequireFields(
            Value,
            {
                "trackingType": 8,
                "updateFlag": 0,
                "xRefAssetHash": 0,
                "isActive": True,
                "isEdited": False,
                "isEliminated": False,
                "rGroupRepresentative": None,
            },
        )
        if (
            Graph.Resolve(Value.Fields["rParentFeature"]) != Context.Feature
            or Graph.Resolve(Value.Fields["rParent"]) != Nodes
            or NumberValue(Value.Fields["computeTime"]) < 0
        ):
            raise ValueError("Native rim selected reference has inconsistent ownership")
    RequireFields(Selected, {"rOwnerOccurrence": None, "rTargetOccurrence": None})
    EmptyFields(Selected, ("refBodies",))
    RequireFields(
        Context.SelectedRef,
        {"bAlwaysRecompute": False, "bDirReversedAgainstRefEntity": False},
    )
    Profiles = LinkedNodes(Graph, Extrusion.Extrude, "profileDataRefs")
    SameNodes((*Profiles, Selected), Graph.ByClass("ModelDataRef"))
    CheckRegion(
        Graph,
        Extrusion,
        (ReadCircle(Graph, Extrusion).CurveNode,),
        AssetId,
        Scoped=True,
    )
    CheckRimRecipe(Graph, Context)
