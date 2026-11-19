from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.MakeBox import (
    MakeBox,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.Circles.MakeCircleBox import (
    MakeCircleBox,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)


# admitted child bounds retain exact line loop behavior and separately verify the ordinary front circle owners
def MakeChildBox(ChildValue: PartCandidate) -> dict[str, float]:
    PlanValue = ChildValue.PlanValue
    if type(PlanValue) is CirclePlan:
        return MakeCircleBox(ChildValue)
    if type(PlanValue) is not BlindPlan:
        raise ValueError("assembly constituent bounds require an admitted line loop")
    VerticesValue = PlanValue.VerticesValue
    Minimum = (
        min(PointValue[0] for PointValue in VerticesValue),
        min(PointValue[1] for PointValue in VerticesValue),
        0.0,
    )
    Maximum = (
        max(PointValue[0] for PointValue in VerticesValue),
        max(PointValue[1] for PointValue in VerticesValue),
        PlanValue.DepthValue,
    )
    return MakeBox(Minimum, Maximum)
