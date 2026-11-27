from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue


# source recipes retain complete group ownership instead of comparing only their primary text
def ReadRimRecipe(Recipe: RecipeValue, Index: int) -> FeatureTag:
    if not 0 <= Index < len(Recipe.Tags) or len(Recipe.Tags[Index]) != 1:
        raise ValueError("Native rim recipe has an ambiguous feature group")
    Group = Recipe.Tags[Index][0]
    return FeatureTag(
        "".join(chr(Value) for Value in Group.PrimaryId),
        Group.OperationIds,
        Group.SecondaryId,
        Group.ApproachId,
    )
