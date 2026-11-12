from typing import TypeAlias

from convert.formats.Fusion.EntityCodec.Recipes.Model.BaseRecipe import BaseRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.BodyRecipe import BodyRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.BoundFaceRecipe import (
    BoundFaceRecipe,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.FaceRecipe import FaceRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.VertexRecipe import VertexRecipe

KRecipePayload: TypeAlias = (
    BaseRecipe | BodyRecipe | FaceRecipe | BoundFaceRecipe | EdgeRecipe | VertexRecipe
)
