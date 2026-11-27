from convert.adapters.Fusion.Native.Circular.RimFillet.ReadRimRecipe import (
    ReadRimRecipe,
)
from convert.adapters.Fusion.Native.Circular.RimFillet.FindRimOwner import FindRimOwner
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe


# every source recipe group must witness the selected top rim and its actual adjacent faces and seam vertex
def CheckRimRecipe(
    State: GeometryState,
    Context: RimContext,
    Faces: dict[str, int],
    Edges: dict[str, int],
) -> None:
    Recipe = Context.Recipe
    Payload = Recipe.Payload
    if not isinstance(Payload, EdgeRecipe):
        raise ValueError("Native rim requires a complete source edge recipe")
    Owner = FindRimOwner(
        State, ReadRimRecipe(Recipe, Payload.PrimaryTagIndex), EdgeNode
    )
    Adjacent = tuple(
        FindRimOwner(State, ReadRimRecipe(Recipe, FaceValue.PrimaryTagIndex), FaceNode)
        for FaceValue in Payload.AdjacentFaces
    )
    if (
        Owner != Edges["top"]
        or len(Adjacent) != 2
        or set(Adjacent) != {Faces["side"], Faces["top"]}
        or len(Payload.AdjacentVertices) != 1
    ):
        raise ValueError("Native rim recipe selects another physical edge or face")
    Vertex = Payload.AdjacentVertices[0]
    VertexFaces = tuple(
        FindRimOwner(State, ReadRimRecipe(Recipe, FaceValue.PrimaryTagIndex), FaceNode)
        for FaceValue in Vertex.AdjacentFaces
    )
    if (
        Vertex.PrimaryTagIndex != -1
        or len(VertexFaces) != 2
        or set(VertexFaces) != set(Adjacent)
        or len(Vertex.AdjacentEdges) != 1
    ):
        raise ValueError("Native rim vertex recipe has another face intersection")
    LinkedEdge = Vertex.AdjacentEdges[0]
    if (
        FindRimOwner(State, ReadRimRecipe(Recipe, LinkedEdge.PrimaryTagIndex), EdgeNode)
        != Owner
        or LinkedEdge.AdjacentFaces
        or LinkedEdge.AdjacentVertices
    ):
        raise ValueError("Native rim vertex recipe has another circular seam")
    Indices = {
        Payload.PrimaryTagIndex,
        LinkedEdge.PrimaryTagIndex,
        *(FaceValue.PrimaryTagIndex for FaceValue in Payload.AdjacentFaces),
        *(FaceValue.PrimaryTagIndex for FaceValue in Vertex.AdjacentFaces),
    }
    if Indices != set(range(len(Recipe.Tags))):
        raise ValueError("Native rim recipe contains unaccounted feature groups")
