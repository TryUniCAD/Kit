from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.FaceRecipe import FaceRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.UvOrderEntry import UvOrderEntry


@MakeDataClass(frozen=True, slots=True)
class VertexRecipe:
    PrimaryTagIndex: int
    AdjacentFaces: tuple[FaceRecipe, ...]
    AdjacentEdges: tuple[EdgeRecipe, ...]
    UvOrders: tuple[UvOrderEntry, ...]
