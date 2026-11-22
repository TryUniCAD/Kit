from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.MakeEllipSketch import (
    MakeEllipSketch,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Profile.BeginProfileMut import (
    BeginProfileMut,
)
from convert.adapters.solidworks.Archive.Construction.Profile.MakeProfileData import (
    MakeProfileData,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)


# the ellipse sketch must retain the same actual part support and frame as the other profile families
def MakeEllipProf(
    PartValue: PartSystem,
    PlanValue: EllipsePlan,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> ProfileGraph:
    ProfileValue, Reference, FrameValue = BeginProfileMut(
        PlanValue.SketchName,
        PartValue.RootValue,
        PartValue.SystemValues.PlaneValues[PlanValue.AxisValue],
        PlanValue.AxisValue,
        TargetValue,
        Allocator,
    )
    SketchValue = MakeEllipSketch(ProfileValue, PlanValue)
    ProfileValue.FieldsValue.update(
        MakeProfileData(SketchValue.SketchValue, Reference, FrameValue)
    )
    return ProfileGraph(ProfileValue, SketchValue, Reference, FrameValue)
