from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from typing import TYPE_CHECKING

from convert.formats.Fusion.EntityCodec.Recipes.Model.FaceRecipe import FaceRecipe

if TYPE_CHECKING:
    from convert.formats.Fusion.EntityCodec.Recipes.Model.VertexRecipe import (
        VertexRecipe,
    )


@MakeDataClass(frozen=True, slots=True)
class EdgeRecipe:
    PrimaryTagIndex: int
    LwdTagIndex: int
    AdjacentFaces: tuple[FaceRecipe, ...]
    AdjacentVertices: tuple[VertexRecipe, ...]
    ReferenceFaceIndex: int
