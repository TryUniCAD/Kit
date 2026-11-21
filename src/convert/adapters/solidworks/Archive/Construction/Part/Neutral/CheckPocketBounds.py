from convert.adapters.solidworks.Archive.Construction.Part.Neutral.PocketPlan import (
    PocketPlan,
)


# the blind pocket must leave positive radial and end wall thickness in the single boss
def CheckPocketFit(PlanValue: PocketPlan) -> None:
    XValues, YValues = zip(*PlanValue.BossValue.VerticesValue, strict=True)
    CenterX, CenterY = PlanValue.CircleValue.CenterValue
    ClearanceValue = min(
        CenterX - min(XValues),
        max(XValues) - CenterX,
        CenterY - min(YValues),
        max(YValues) - CenterY,
    )
    if (
        PlanValue.CircleValue.RadiusValue >= ClearanceValue
        or PlanValue.EndValue.DepthValue >= PlanValue.BossValue.DepthValue
    ):
        raise ValueError("ordinary blind pocket must lie inside the actual boss")
