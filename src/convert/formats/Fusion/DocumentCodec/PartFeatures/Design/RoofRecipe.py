from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.SelectRecipe import (
    PickFace,
    PickVertex,
    RecipeTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.BoundFaceRecipe import (
    BoundFaceRecipe,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue


def RoofPlans(Solid: PrismSolid) -> list[tuple[tuple[FaceLabel, ...], ...]]:
    if len(Solid.Slabs) != 1 or len(Solid.Slabs[0].Loops) != 1:
        raise ValueError("Fusion part roof selection requires a single-profile prism")
    LoopValue = Solid.Slabs[0].Loops[0]
    RoofValue = Solid.Slabs[0].RoofLabel
    Order = (LoopValue[-1], *LoopValue[:-1])
    First = (Order[-1].Label, Order[0].Label, RoofValue)
    Opening = First
    Plans: list[tuple[tuple[FaceLabel, ...], ...]] = []
    for Index, Value in enumerate(Order):
        Closing = (
            First
            if Index + 1 == len(Order)
            else (Order[Index + 1].Label, RoofValue, Value.Label)
        )
        Plans.append(((Value.Label, RoofValue), Opening, Closing))
        Opening = Closing
    return Plans


def RoofRecipe(Solid: PrismSolid) -> RecipeValue:
    Plans = RoofPlans(Solid)
    Labels: list[FaceLabel] = [Solid.Slabs[0].RoofLabel]
    for PlanValue in Plans:
        Labels.extend(
            Label for Group in PlanValue for Label in Group if Label not in Labels
        )
    Place = {Label: Index for Index, Label in enumerate(Labels)}
    Edges = tuple(
        EdgeRecipe(
            -1,
            -1,
            tuple(PickFace(Place[Label]) for Label in Faces),
            (
                PickVertex(tuple(Place[Label] for Label in Opening)),
                PickVertex(tuple(Place[Label] for Label in Closing)),
            ),
            -1,
        )
        for Faces, Opening, Closing in Plans
    )
    return RecipeValue(3, RecipeTags(Labels), (), BoundFaceRecipe(0, -1, Edges))
