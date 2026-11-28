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
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonInput import (
    PolygonInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeAxisOnlyMut import (
    MakeAxisOnlyMut,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)


# the stock profile binds the authored principal support and publishes only its actual four rectangle relations
def MakeThruProfile(
    SystemValue: PartSystem,
    SettingsValue: PartBuildInput,
    PlanValue: ThroughStock,
    Allocator: PersistentIds,
) -> ProfileGraph:
    ResultValue = MakeProfileMut(
        PlanValue.SketchName,
        SystemValue.RootValue,
        SystemValue.SystemValues.PlaneValues[PlanValue.AxisValue],
        PlanValue.AxisValue,
        PolygonInput(PlanValue.VerticesValue, 19000),
        SettingsValue.TargetValue,
        Allocator,
    )
    MakeAxisOnlyMut(ResultValue, Allocator)
    return ResultValue
