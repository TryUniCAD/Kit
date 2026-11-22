from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Scene.MakeSweepScene import (
    MakeSweepScene,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.AttachMembers import (
    AttachMembers,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)


# the ordered ordinary sweep tree includes the actual annotation cabinet ahead of the surface folder
def BindSwSceneMut(
    SystemValue: PartSystem, InputValue: PartBuildInput, Allocator: PersistentIds
) -> PartSystem:
    _ = AttachMembers(
        SystemValue,
        MakeSweepScene(InputValue.OutputValue.SavedAt),
        InputValue.TargetValue,
        Allocator,
    )
    CabinetValue = SystemValue.SystemValues.CabinetValue
    SurfaceValue = SystemValue.SystemValues.FolderValues["moSurfaceBodyFolder_c"]
    RootValues = tuple(
        NodeValue
        for NodeValue in SystemValue.FeatureValues
        if NodeValue is not CabinetValue
    )
    if len(RootValues) + 1 != len(SystemValue.FeatureValues):
        raise ValueError("sweep requires its actual unique annotation cabinet")
    IndexValue = RootValues.index(SurfaceValue)
    return ReplaceValue(
        SystemValue,
        FeatureValues=(
            *RootValues[:IndexValue],
            CabinetValue,
            *RootValues[IndexValue:],
        ),
    )
