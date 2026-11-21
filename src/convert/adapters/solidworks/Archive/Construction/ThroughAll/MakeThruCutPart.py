from convert.adapters.solidworks.Archive.Construction.Circles.MakeCircleFeat import (
    MakeCircleFeat,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThruCutMut import (
    MakeThruCutMut,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughPartSpec import (
    ThroughPartSpec,
)


# a through cut must use its real support and free circle after the actual stock boss has consumed its identities
def MakeThruCutPart(
    SystemValue: PartSystem,
    SettingsValue: PartBuildInput,
    InputValue: ThroughPartSpec,
    Allocator: PersistentIds,
) -> CutGraph:
    AxisValue = InputValue.StockValue.AxisValue
    ProfileValue = MakeCircleFeat(
        InputValue.SketchName,
        SystemValue.RootValue,
        SystemValue.SystemValues.PlaneValues[AxisValue],
        AxisValue,
        InputValue.CircleValue,
        SettingsValue.TargetValue,
        Allocator,
    )
    return MakeThruCutMut(
        InputValue.FeatureName,
        SystemValue.RootValue,
        ProfileValue,
        InputValue.EndValue,
        SettingsValue.TargetValue,
        Allocator,
    )
