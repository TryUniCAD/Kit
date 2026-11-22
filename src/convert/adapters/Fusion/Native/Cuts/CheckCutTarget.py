from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    SameNodes,
    ResolveField,
    RequireFields,
    EmptyFields,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import MappingItems, SeriesItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.Formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeTag import RecipeTag
from convert.Formats.Fusion.EntityCodec.Recipes.Model.BodyRecipe import BodyRecipe


# the modifying operand must identify the created body through both its entity link and native recipe
def CheckCutTarget(
    Graph: NativeGraph,
    Contexts: tuple[ExtrudeContext, ExtrudeContext],
    Operations: dict[int, tuple[int, ...]],
) -> FeatureTag:
    Stock, ToolCut = Contexts
    Targets = LinkedNodes(Graph, ToolCut.Extrude, "targetDataRefs")
    if len(Targets) != 1 or Targets[0].ClassName != "ModelDataRef":
        raise ValueError("Native cut requires one explicit target reference")
    Operand = Graph.OneClass("DRBody")
    SameNodes((Operand,), LinkedNodes(Graph, Targets[0], "dataRefs"))
    SameNodes((Stock.DcBody,), LinkedNodes(Graph, Operand, "refBodies"))
    RequireFields(Operand, {"trackingType": 8, "updateFlag": 0, "xRefAssetHash": 0})
    if (
        Graph.Resolve(Operand.Fields["rParentFeature"]) != ToolCut.Extrude
        or Graph.Resolve(Targets[0].Fields["rParentFeature"]) != ToolCut.Extrude
    ):
        raise ValueError("Native cut target belongs to another feature")
    Recipe = ResolveField(Graph, Operand, "rRecipe", "ASMRecipe")
    SameNodes((Recipe,), Graph.ByClass("ASMRecipe"))
    Saved = Recipe.Fields["m_Recipe"]
    if not isinstance(Saved, OptionalValue) or not isinstance(Saved.Value, RecipeValue):
        raise ValueError("Native cut body recipe is absent")
    Table = ResolveField(Graph, Stock.Extrude, "rProgenitorTable", "ProgenitorTable")
    BodyPairs = tuple(
        Entry
        for Entry in SeriesItems(Table.Fields["ProgenitorTagVec"])
        if isinstance(Entry, ValuePair)
        and Graph.Resolve(Entry.First).ClassName == "BodyProgenitor"
    )
    if len(BodyPairs) != 1:
        raise ValueError("Native cut stock has no unique body progenitor")
    RequireFields(
        Graph.Resolve(BodyPairs[0].First), {"bodyUuid": Stock.DcBody.Fields["bodyUuid"]}
    )
    Allocated = Operations[Stock.Extrude.ObjectId]
    if not Allocated or Saved.Value != RecipeValue(
        3,
        (
            (
                RecipeTag(
                    tuple(ord(Character) for Character in str(Allocated[0])),
                    IntegerValue(BodyPairs[0].Second),
                    (),
                    0,
                ),
            ),
        ),
        (),
        BodyRecipe(0, -1),
    ):
        raise ValueError("Native cut recipe does not identify the stock body operation")
    Pairs = MappingItems(Operand.Fields["operIdTypeMap"])
    if (
        len(Pairs) != 1
        or IntegerValue(Pairs[0].First) != Allocated[0]
        or IntegerValue(Pairs[0].Second) != 33
    ):
        raise ValueError("Native cut target operation type is inconsistent")
    EmptyFields(Operand, ("caches",))
    EmptyFields(ToolCut.Extrude, ("dcBodies",))
    return FeatureTag(str(Allocated[0]), (), IntegerValue(BodyPairs[0].Second), 0)
