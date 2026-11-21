from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
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
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Sketch.MakeThinRingMut import (
    MakeThinRingMut,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the thin sketch uses the same principal support owner as the actual selected axis
def MakeThinProfMut(
    SystemValue: PartSystem,
    InputValue: PartBuildInput,
    PlanValue: RevolvePlan,
    Allocator: PersistentIds,
) -> tuple[ProfileGraph, ArchiveNode]:
    ProfileValue, Reference, FrameValue = BeginProfileMut(
        PlanValue.SketchName,
        SystemValue.RootValue,
        SystemValue.SystemValues.PlaneValues[PlanValue.AxisValue],
        PlanValue.AxisValue,
        InputValue.TargetValue,
        Allocator,
    )
    ShapeValue = MakeThinRingMut(ProfileValue, PlanValue)
    ProfileValue.FieldsValue.update(
        MakeProfileData(ShapeValue.SketchValue, Reference, FrameValue)
    )
    return (
        ProfileGraph(ProfileValue, ShapeValue, Reference, FrameValue),
        ShapeValue.LineValues[-1],
    )
