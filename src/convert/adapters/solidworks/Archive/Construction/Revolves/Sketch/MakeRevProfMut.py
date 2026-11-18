from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Profile.MakeProfileMut import (
    MakeProfileMut,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Sketch.AddRevAxisMut import (
    AddRevAxisMut,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Sketch.AddRevRulesMut import (
    AddRevRulesMut,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonInput import (
    PolygonInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the fresh revolve profile must share the actual registered front plane model and allocator with its downstream boss
def MakeRevProfMut(
    SystemValue: PartSystem,
    InputValue: PartBuildInput,
    PlanValue: RevolvePlan,
    Allocator: PersistentIds,
) -> tuple[ProfileGraph, ArchiveNode]:
    ProfileValue = MakeProfileMut(
        PlanValue.SketchName,
        SystemValue.RootValue,
        SystemValue.SystemValues.PlaneValues["z"],
        "z",
        PolygonInput(PlanValue.VerticesValue, 19000),
        InputValue.TargetValue,
        Allocator,
    )
    ProfileValue, AxisValue = AddRevAxisMut(ProfileValue, PlanValue)
    AddRevRulesMut(ProfileValue, PlanValue, Allocator)
    return ProfileValue, AxisValue
