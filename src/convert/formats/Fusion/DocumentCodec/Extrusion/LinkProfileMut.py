from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Extrusion.RecipeValues import (
    CircleLoop,
    CurveRecipe,
)


def LinkProfileMut(Author: AuthorState) -> None:
    Reference = Author.Reference
    Author.Change(
        "profile_model",
        dataRefs=[Reference("profile_region")],
        trackingType=65,
        rParentFeature=Reference("dc_extrude"),
    )
    ScopeValue = [
        Author.MakeGroup(
            "PassiveScopeValue",
            dict(
                assetId=Author.AssetId,
                scopeEntityIdentifier=str(Author.Roles["circle_sketch"]),
                scopeIdType=1,
                segmentId=Author.Policy.DesignSegmentId,
            ),
        )
    ]
    Author.Change(
        "profile_region",
        rRecipe=Reference("region_recipe"),
        rScope=ScopeValue,
        trackingType=65,
        rParentFeature=Reference("dc_extrude"),
    )
    TagId = Author.Policy.FirstSketchTag + 2
    RecipeData = [
        Author.MakeGroup(
            "SkRegionRecipeDataValue",
            dict(faceRecipe=[CircleLoop(TagId)], originalFaceRecipes=[]),
        )
    ]
    Author.Change(
        "region_recipe",
        rSketchRegionRef=Reference("profile_region"),
        skRegionRecipe=[RecipeData],
    )
    Author.Change("curve_progenitor", rRecipe=Reference("curve_recipe"))
    Author.Change("curve_recipe", profileEdgeTagData=CurveRecipe(TagId, True))
