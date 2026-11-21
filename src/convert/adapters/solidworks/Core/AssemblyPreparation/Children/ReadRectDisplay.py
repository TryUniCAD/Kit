from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)


# source free annotation placement must follow the actual rectangle bounds rather than any saved display cache
def ReadRectDisplay(PlanValue: BlindPlan, RecipeValue: PartBuildInput) -> RectDimInput:
    LeftValue, BottomValue = PlanValue.VerticesValue[0]
    RightValue, TopValue = PlanValue.VerticesValue[2]
    return RectDimInput(
        ((LeftValue + RightValue) / 2, BottomValue - 0.25 * (TopValue - BottomValue)),
        (RightValue + 0.25 * (RightValue - LeftValue), (BottomValue + TopValue) / 2),
        RecipeValue.DesignIntent,
        RecipeValue.SelectedLeader,
        False,
    )
