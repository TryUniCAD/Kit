from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.MakeBox import (
    MakeBox,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.Circles.NeedCircChild import (
    NeedCircChild,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)


# an ordinary front cylinder supplies analytic child local extrema and the same independently serialized native point pair sphere
def MakeCircleBox(ChildValue: PartCandidate) -> dict[str, float]:
    PlanValue = NeedCircChild(ChildValue)
    CenterX, CenterY = PlanValue.CircleValue.CenterValue
    RadiusValue = PlanValue.CircleValue.RadiusValue
    Minimum = (CenterX - RadiusValue, CenterY - RadiusValue, 0.0)
    Maximum = (CenterX + RadiusValue, CenterY + RadiusValue, PlanValue.DepthValue)
    return MakeBox(Minimum, Maximum)
