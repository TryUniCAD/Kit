from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimVertex import (
    CheckRimVertex,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe


# complete recipe agreement prevents matching numeric radii from hiding another selected topology
def CheckRimRecipe(Graph: NativeGraph, Context: RimContext) -> None:
    Value = Context.Recipe
    if (
        Value.Version != 3
        or Value.LwdTags
        or len(Value.Tags) != 3
        or any(len(TagGroups) != 1 for TagGroups in Value.Tags)
        or not isinstance(Value.Payload, EdgeRecipe)
    ):
        raise ValueError("Native rim requires one complete three group edge recipe")
    Payload = Value.Payload
    if (
        Payload.PrimaryTagIndex != 0
        or Payload.LwdTagIndex != -1
        or Payload.ReferenceFaceIndex != -1
        or tuple(FaceValue.PrimaryTagIndex for FaceValue in Payload.AdjacentFaces)
        != (1, 2)
        or any(FaceValue.LwdTagIndex != -1 for FaceValue in Payload.AdjacentFaces)
    ):
        raise ValueError("Native rim edge recipe adjacency is not qualified")
    CheckRimVertex(Payload)
    if (
        any(
            TagValue.SecondaryId != 0
            or TagValue.ApproachId != 0
            or len(TagValue.OperationIds) != 1
            for TagGroups in Value.Tags
            for TagValue in TagGroups
        )
        or len(
            {
                TagValue.OperationIds
                for TagGroups in Value.Tags
                for TagValue in TagGroups
            }
        )
        != 1
    ):
        raise ValueError("Native rim recipe tags have inconsistent operation owners")
    Progenitor = Graph.OneClass("BrepProgenitor")
    RequireFields(Progenitor, {"rParent": None})
    Recipe = ResolveField(Graph, Context.SelectedRef, "rRecipe", "ASMRecipe")
    Duplicate = ResolveField(Graph, Progenitor, "m_brepRecipe", "ASMRecipe")
    if Duplicate.Fields["m_Recipe"] != Recipe.Fields["m_Recipe"]:
        raise ValueError("Native rim selected recipe differs from its progenitor")
    SameNodes((Recipe, Duplicate), Graph.ByClass("ASMRecipe"))
