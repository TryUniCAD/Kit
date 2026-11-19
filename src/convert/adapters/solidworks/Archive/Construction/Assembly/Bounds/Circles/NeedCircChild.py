from convert.adapters.solidworks.Archive.Construction.Assembly.CheckAsmChild import (
    CheckAsmChild,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.Circles.CheckCircEnd import (
    CheckCircEnd,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.Circles.CheckCircGeom import (
    CheckCircGeom,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.Circles.CheckCircRef import (
    CheckCircRef,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)


# circle target admission retains the actual complete generated child and closes alternate features and unsupported end profiles
def NeedCircChild(ChildValue: PartCandidate) -> CirclePlan:
    if type(ChildValue) is not PartCandidate:
        raise TypeError("circle bounds require the actual generated part candidate")
    CheckAsmChild(ChildValue)
    PlanValue = ChildValue.PlanValue
    if type(PlanValue) is not CirclePlan or ChildValue.CutValue is not None:
        raise ValueError("circle bounds require one ordinary uncut circle boss")
    EndValue = PlanValue.EndValue
    if (
        (PlanValue.AxisValue, PlanValue.PlaneName) != ("z", "Front Plane")
        or EndValue.ModeValue != "blind"
        or EndValue.IsReversed
        or EndValue.SecondDepth is not None
    ):
        raise ValueError("circle bounds require the qualified forward Front blind end")
    Expected = (
        *ChildValue.SystemValue.FeatureValues,
        ChildValue.ProfileValue.ProfileValue,
        ChildValue.BossValue.FeatureValue,
    )
    Actual = ChildValue.ResolvedValue.RootsValue
    if len(Actual) != len(Expected) or any(
        LeftValue is not RightValue
        for LeftValue, RightValue in zip(Actual, Expected, strict=True)
    ):
        raise ValueError("circle bounds require the actual complete ordered history")
    CheckCircRef(ChildValue)
    CheckCircGeom(ChildValue.ProfileValue, PlanValue.CircleValue)
    CheckCircEnd(ChildValue, PlanValue)
    return PlanValue
