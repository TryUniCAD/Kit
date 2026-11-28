from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    LinkedNodes,
    RequireFields,
    ResolveField,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, TextValue
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.Formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the saved face operation must identify the modeled extrusion and live body and editable dependency owner
def CheckStyleOwner(
    Graph: NativeGraph, Context: ExtrudeContext, AssetId: str
) -> tuple[NativeNode, str, RecipeValue]:
    Owner = Graph.OneClass("VMBrepRef")
    Nodes = ResolveField(Graph, Context.Fragment, "rNodes", "DcNodes")
    Birth = IntegerValue(Context.Extrude.Fields["birthday"])
    RequireFields(
        Owner,
        {
            "rFeature": LocalRef(Context.Extrude.ObjectId),
            "rParent": LocalRef(Nodes.ObjectId),
            "rParentFeature": None,
            "rGroupRepresentative": None,
            "isActive": True,
            "isEdited": False,
            "isEliminated": False,
            "bAlwaysRecompute": False,
            "bDirReversedAgainstRefEntity": False,
            "birthday": Birth,
            "firstBirthday": Birth,
            "computeTime": 0.0,
            "trackingType": 16,
            "updateFlag": 0,
            "xRefAssetHash": 0,
        },
    )
    EmptyFields(Owner, ("caches",))
    Scope = ObjectFields(Owner.Fields["rScope"])
    if (
        LinkedNodes(Graph, Owner, "refBodies") != (Context.DcBody,)
        or LinkedNodes(Graph, Nodes, "children")[-1:] != (Owner,)
        or Scope["assetId"] != AssetId
        or Scope["scopeIdType"] != 2
        or Scope["scopeEntityIdentifier"] != Context.Component.Fields["persistentId"]
        or Scope["segmentId"] != Owner.SegmentId
    ):
        raise ValueError(
            "Native face appearance has an inconsistent body or component owner"
        )
    CheckStyleState(Graph, Context, Owner)
    RecipeNode = ResolveField(Graph, Owner, "rRecipe", "ASMRecipe")
    Recipe = RecipeNode.Fields["m_Recipe"]
    if (
        Graph.ByClass("ASMRecipe") != (RecipeNode,)
        or not isinstance(Recipe, OptionalValue)
        or not isinstance(Recipe.Value, RecipeValue)
    ):
        raise ValueError("Native face appearance requires one typed face recipe")
    return Owner, TextValue(Owner.Fields["visualMaterialTag"]), Recipe.Value


# the saved reciprocal update must use the actual extrusion timestamp and healthy status
def CheckStyleState(
    Graph: NativeGraph, Context: ExtrudeContext, Owner: NativeNode
) -> None:
    Status = ResolveField(Graph, Owner, "status", "DcStatus")
    RequireFields(Status, {"statusType": 0})
    EmptyFields(Status, ("statusCodes",))
    if any(
        NodeValue.SegmentId == Owner.SegmentId
        and NodeValue != Owner
        and NodeValue.Fields.get("status") == LocalRef(Status.ObjectId)
        for NodeValue in Graph.Nodes.values()
    ):
        raise ValueError("Native face appearance shares its compute status")
    Update = ResolveField(Graph, Owner, "rDynamicUpdateData", "DynamicUpdateData")
    SourceUpdate = ResolveField(
        Graph, Context.Extrude, "rDynamicUpdateData", "DynamicUpdateData"
    )
    RequireFields(
        Update,
        {
            "rOwnerNode": LocalRef(Owner.ObjectId),
            "isBodyOK": True,
            "isPredecessorOK": True,
            "xRefPredecessorsHash": 0,
            "predecessors": ValueMap(
                (
                    ValuePair(
                        LocalRef(Context.Extrude.ObjectId),
                        SourceUpdate.Fields["timeStamp"],
                    ),
                )
            ),
        },
    )
    EmptyFields(Update, ("bodies",))
