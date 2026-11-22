from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import (
    AnchorPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)


# both origin box paths derive the same rectangle presentation from authored lengths
def BoxAnchorInput(PlanValue: BlindPlan, TopAttached: bool) -> AnchorPartInput:
    Margin = min(PlanValue.WidthValue, PlanValue.HeightValue) / 4
    WidthText = (PlanValue.WidthValue / 2, Margin if TopAttached else -Margin)
    HeightText = (
        (-Margin, -PlanValue.HeightValue / 2)
        if TopAttached
        else (PlanValue.WidthValue + Margin, PlanValue.HeightValue / 2)
    )
    return AnchorPartInput(
        "corner", RectDimInput(WidthText, HeightText, False, 1, False), TopAttached
    )
