from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
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


# plain and dimensioned rectangles must retain identical native profile construction and actual system plane ownership before their distinct relations are added
def MakePartProfMut(
    SystemValue: PartSystem,
    InputValue: PartBuildInput,
    PlanValue: BlindPlan,
    Allocator: PersistentIds,
) -> ProfileGraph:
    return MakeProfileMut(
        PlanValue.SketchName,
        SystemValue.RootValue,
        SystemValue.SystemValues.PlaneValues[PlanValue.AxisValue],
        PlanValue.AxisValue,
        PolygonInput(PlanValue.VerticesValue, 19000),
        InputValue.TargetValue,
        Allocator,
    )
