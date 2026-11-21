from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.PartPlan import (
    KPartPlan,
)


# scoped visual construction uses the demonstrated forward dimensioned rectangle geometry
def CheckRectVisual(PlanValue: KPartPlan) -> None:
    if (
        type(PlanValue) is not BlindPlan
        or PlanValue.AxisValue != "z"
        or PlanValue.Reversed
        or PlanValue.DepthValue <= 0
        or len(PlanValue.VerticesValue) != 4
    ):
        raise ValueError(
            "planar visual construction requires a forward rectangular blind child"
        )
    First, Second, Third, Fourth = PlanValue.VerticesValue
    if (
        Second != (Third[0], First[1])
        or Fourth != (First[0], Third[1])
        or First[0] >= Third[0]
        or First[1] >= Third[1]
    ):
        raise ValueError(
            "planar visual construction requires ordered rectangular child vertices"
        )
