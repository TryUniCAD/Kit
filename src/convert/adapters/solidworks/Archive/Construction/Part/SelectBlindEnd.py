from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import (
    BlindEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.PartPlan import (
    KPartPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.PocketPlan import (
    PocketPlan,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughPartSpec import (
    ThroughPartSpec,
)


# the shared blind composer chooses the exact active end law and keeps the through stock bound to its own plan
def SelectBlindEnd(
    PlanValue: KPartPlan,
    PocketValue: PocketPlan | None,
    ThroughValue: ThroughPartSpec | None,
) -> BlindEndInput | BossEndInput:
    if ThroughValue is not None:
        if PocketValue is not None or ThroughValue.StockValue is not PlanValue:
            raise ValueError(
                "through all composition requires its actual sole stock plan"
            )
        return BossEndInput(PlanValue.DepthValue, False, 19000, "mid_plane")
    if isinstance(PlanValue, CirclePlan):
        return PlanValue.EndValue
    if isinstance(PlanValue, BlindPlan) and PlanValue.Reversed:
        return BossEndInput(
            PlanValue.DepthValue, True, 19000, "blind", DepthName=PlanValue.DepthName
        )
    return BlindEndInput(PlanValue.DepthValue, False, 19000, PlanValue.DepthName)
