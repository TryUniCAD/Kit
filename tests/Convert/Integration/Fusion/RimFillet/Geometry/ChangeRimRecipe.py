from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimContext import (
    ReadRimContext,
)
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.Formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField


# coherent duplicate recipe edits must still refuse when the full groups select the wrong physical topology
def ChangeRimRecipe(Model: DocumentModel, CaseName: str) -> DocumentModel:
    Graph = BuildGraph(Model)
    Context = ReadRimContext(Graph)
    Snapshot = Model.Snapshots[0].Snapshot
    assert isinstance(Snapshot, SnapshotModel)
    for NodeValue in Graph.ByClass("ASMRecipe"):
        Optional = NodeValue.Fields["m_Recipe"]
        if (
            not isinstance(Optional, OptionalValue)
            or not isinstance(Optional.Value, RecipeValue)
            or not isinstance(Optional.Value.Payload, EdgeRecipe)
        ):
            continue
        Recipe = Optional.Value
        Payload = Recipe.Payload
        assert isinstance(Payload, EdgeRecipe)
        Index = (
            Payload.PrimaryTagIndex
            if CaseName == "selected_lower"
            else Payload.AdjacentFaces[1].PrimaryTagIndex
        )
        Group = Recipe.Tags[Index][0]
        Alternate = (
            Snapshot.TagSet.BottomEdge
            if CaseName == "selected_lower"
            else Snapshot.TagSet.BottomFace
        )
        Groups = list(Recipe.Tags)
        Groups[Index] = (
            ReplaceData(
                Group,
                PrimaryId=tuple(Alternate.PrimaryId.encode("ascii")),
                OperationIds=Alternate.OperationIds,
            ),
        )
        Model = ChangeField(
            Model,
            NodeValue.ObjectId,
            "m_Recipe",
            ReplaceData(Optional, Value=ReplaceData(Recipe, Tags=tuple(Groups))),
        )
    assert Context.Recipe != ReadRimContext(BuildGraph(Model)).Recipe
    return Model
